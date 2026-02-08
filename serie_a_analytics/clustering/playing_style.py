"""
Playing Style K-Means Clustering Module.

This module implements K-means clustering to identify playing styles
for Serie A 2015-2016 team+manager combinations based on 15 selected metrics.

Supports loading data from:
- Supabase (for Streamlit Cloud deployment)
- CSV files (for local development fallback)
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA

# Add parent path for config imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import DATA_SOURCE


class PlayingStyleClusterer:
    """
    K-means clustering for identifying playing styles.

    Uses 15 carefully selected metrics across 5 categories:
    - Possession: possession_percentage, progressive_passes, dribbles_total
    - Pressing: ppda, pressing_high, counterpressing
    - Transitions: counter_attacks, buildup_sequences, fast_attacks
    - Attacking: xg_total, crosses_total, touches_in_box
    - Defending: tackles, interceptions, aerial_duels_defensive
    """

    # Selected metrics for clustering
    SELECTED_METRICS = [
        # Possession
        'possession_percentage',
        'progressive_passes',
        'dribbles_total',
        # Pressing
        'ppda',
        'pressing_high',
        'counterpressing',
        # Transitions
        'counter_attacks',
        'buildup_sequences',
        'fast_attacks',
        # Attacking
        'xg_total',
        'crosses_total',
        'touches_in_box',
        # Defending
        'tackles',
        'interceptions',
        'aerial_duels_defensive',
    ]

    # Metric display names (Italian)
    METRIC_NAMES_IT = {
        'possession_percentage': 'Possesso palla',
        'progressive_passes': 'Passaggi progressivi',
        'dribbles_total': 'Dribbling',
        'ppda': 'Intensità pressing',
        'pressing_high': 'Pressing alto',
        'counterpressing': 'Contro-pressing',
        'counter_attacks': 'Contropiedi',
        'buildup_sequences': 'Costruzione dal basso',
        'fast_attacks': 'Attacchi rapidi',
        'xg_total': 'Expected Goals',
        'crosses_total': 'Cross',
        'touches_in_box': 'Tocchi in area',
        'tackles': 'Contrasti',
        'interceptions': 'Intercettazioni',
        'aerial_duels_defensive': 'Duelli aerei difensivi',
    }

    # Metric categories for grouping
    METRIC_CATEGORIES = {
        'Possesso': ['possession_percentage', 'progressive_passes', 'dribbles_total'],
        'Pressing': ['ppda', 'pressing_high', 'counterpressing'],
        'Transizioni': ['counter_attacks', 'buildup_sequences', 'fast_attacks'],
        'Attacco': ['xg_total', 'crosses_total', 'touches_in_box'],
        'Difesa': ['tackles', 'interceptions', 'aerial_duels_defensive'],
    }

    def __init__(
        self,
        team_metrics_df: pd.DataFrame,
        combinations_df: pd.DataFrame,
        min_matches: int = 5
    ):
        """
        Initialize the clusterer.

        Args:
            team_metrics_df: DataFrame with team metrics (long format)
            combinations_df: DataFrame with team+manager combinations
            min_matches: Minimum matches required for inclusion
        """
        self.team_metrics_df = team_metrics_df.copy()
        self.combinations_df = combinations_df.copy()
        self.min_matches = min_matches

        # State variables
        self.data_wide: Optional[pd.DataFrame] = None
        self.scaler: Optional[StandardScaler] = None
        self.X_scaled: Optional[np.ndarray] = None
        self.kmeans: Optional[KMeans] = None
        self.labels: Optional[np.ndarray] = None
        self.cluster_info: Optional[dict] = None
        self.pca: Optional[PCA] = None
        self.X_pca: Optional[np.ndarray] = None

    def prepare_data(self) -> pd.DataFrame:
        """
        Prepare data for clustering: filter and pivot to wide format.

        Uses data passed to constructor (from Supabase or CSV).
        No longer reads directly from CSV files.

        Returns:
            DataFrame in wide format (rows=team+manager, columns=metrics)
        """
        # Filter combinations by minimum matches
        valid_combos = self.combinations_df[
            self.combinations_df['matches_count'] >= self.min_matches
        ].copy()

        # Ensure manager_id exists in combinations
        if 'manager_id' not in valid_combos.columns:
            # Create manager_id from index if not present (legacy CSV format)
            valid_combos = valid_combos.reset_index(drop=True)
            valid_combos['manager_id'] = valid_combos.index + 1

        # Get valid (team_id, manager_id) pairs
        valid_pairs = set(
            zip(valid_combos['team_id'].astype(int), valid_combos['manager_id'].astype(int))
        )

        # Filter metrics to selected ones and valid pairs
        filtered_metrics = self.team_metrics_df[
            (self.team_metrics_df['metric_name'].isin(self.SELECTED_METRICS)) &
            (self.team_metrics_df.apply(
                lambda r: (int(r['team_id']), int(r['manager_id'])) in valid_pairs, axis=1
            ))
        ].copy()

        # Pivot to wide format
        self.data_wide = filtered_metrics.pivot_table(
            index=['team_id', 'manager_id'],
            columns='metric_name',
            values='metric_value_p90',
            aggfunc='first'
        ).reset_index()

        # Build name mapping from combinations DataFrame
        name_map = {}
        for _, row in valid_combos.iterrows():
            team_id = int(row['team_id'])
            manager_id = int(row['manager_id'])
            name_map[(team_id, manager_id)] = {
                'team_name': row.get('team_name', 'Unknown'),
                'manager_name': row.get('manager_name', 'Unknown'),
                'matches_count': row.get('matches_count', 0)
            }

        # Add team and manager names
        self.data_wide['team_name'] = self.data_wide.apply(
            lambda r: name_map.get((int(r['team_id']), int(r['manager_id'])), {}).get('team_name', 'Unknown'),
            axis=1
        )
        self.data_wide['manager_name'] = self.data_wide.apply(
            lambda r: name_map.get((int(r['team_id']), int(r['manager_id'])), {}).get('manager_name', 'Unknown'),
            axis=1
        )
        self.data_wide['matches_count'] = self.data_wide.apply(
            lambda r: name_map.get((int(r['team_id']), int(r['manager_id'])), {}).get('matches_count', 0),
            axis=1
        )

        # Handle missing values (fill with column mean)
        for metric in self.SELECTED_METRICS:
            if metric in self.data_wide.columns:
                self.data_wide[metric] = self.data_wide[metric].fillna(
                    self.data_wide[metric].mean()
                )

        return self.data_wide

    # Features to remove due to high correlation (r > 0.7)
    # Keep the more interpretable one in each pair:
    # - possession_percentage (0.92) vs progressive_passes -> keep possession_percentage
    # - counter_attacks (0.88) vs fast_attacks -> keep counter_attacks
    # - xg_total (0.80) vs touches_in_box -> keep xg_total
    # - tackles (0.72) vs interceptions -> keep tackles
    CORRELATED_TO_REMOVE = ['progressive_passes', 'fast_attacks', 'touches_in_box', 'interceptions']

    def normalize_features(self, remove_correlated: bool = True, use_pca: bool = False, pca_variance: float = 0.90) -> np.ndarray:
        """
        Normalize features using StandardScaler with optional correlation removal and PCA.

        Args:
            remove_correlated: If True, removes highly correlated features (r > 0.7)
            use_pca: If True, applies PCA after scaling
            pca_variance: Variance to retain if using PCA (default 90%)

        Note: ppda is inverted (1/ppda) because lower ppda = more pressing.

        Returns:
            Scaled (and optionally PCA-transformed) feature matrix
        """
        if self.data_wide is None:
            self.prepare_data()

        # Extract feature columns
        feature_cols = [m for m in self.SELECTED_METRICS if m in self.data_wide.columns]

        # Remove highly correlated features if requested
        if remove_correlated:
            feature_cols = [m for m in feature_cols if m not in self.CORRELATED_TO_REMOVE]
            print(f"Removed {len(self.CORRELATED_TO_REMOVE)} correlated features. Using {len(feature_cols)} features.")

        self.feature_cols_used = feature_cols
        X = self.data_wide[feature_cols].copy()

        # Invert ppda (lower = better pressing, so invert for clustering)
        if 'ppda' in X.columns:
            # Avoid division by zero
            X['ppda'] = 1.0 / X['ppda'].replace(0, 0.001)

        # Handle outliers: clip to 3 standard deviations
        for col in X.columns:
            mean = X[col].mean()
            std = X[col].std()
            X[col] = X[col].clip(mean - 3*std, mean + 3*std)

        # Normalize with StandardScaler
        self.scaler = StandardScaler()
        self.X_scaled = self.scaler.fit_transform(X)

        # Optional PCA transformation
        self.pca_used = use_pca
        self.X_before_pca = self.X_scaled.copy()  # Save for interpretation
        if use_pca:
            from sklearn.decomposition import PCA as PCATransform
            pca_transform = PCATransform(n_components=pca_variance, random_state=42)
            self.X_scaled = pca_transform.fit_transform(self.X_scaled)
            print(f"PCA: reduced to {pca_transform.n_components_} components ({pca_variance*100:.0f}% variance)")

        return self.X_scaled

    def find_optimal_k(self, k_range: tuple = (2, 8)) -> dict:
        """
        Find optimal number of clusters using elbow method and silhouette score.

        Args:
            k_range: Tuple of (min_k, max_k) to test

        Returns:
            Dictionary with inertia, silhouette scores, and suggested k
        """
        if self.X_scaled is None:
            self.normalize_features()

        results = {
            'k_values': [],
            'inertia': [],
            'silhouette': [],
            'suggested_k': None
        }

        for k in range(k_range[0], k_range[1] + 1):
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(self.X_scaled)

            results['k_values'].append(k)
            results['inertia'].append(kmeans.inertia_)

            # Silhouette score (only valid for k >= 2)
            if k >= 2:
                sil_score = silhouette_score(self.X_scaled, labels)
                results['silhouette'].append(sil_score)
            else:
                results['silhouette'].append(None)

        # Find best k based on silhouette score
        valid_silhouettes = [s for s in results['silhouette'] if s is not None]
        if valid_silhouettes:
            best_idx = np.argmax(valid_silhouettes)
            results['suggested_k'] = results['k_values'][best_idx]

        return results

    def fit_clustering(self, k: int) -> dict:
        """
        Fit K-means clustering with specified k.

        Args:
            k: Number of clusters

        Returns:
            Dictionary with labels, centroids, and silhouette score
        """
        if self.X_scaled is None:
            self.normalize_features()

        self.kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        self.labels = self.kmeans.fit_predict(self.X_scaled)

        # Calculate silhouette score
        sil_score = silhouette_score(self.X_scaled, self.labels)

        # Add labels to data
        self.data_wide['cluster_id'] = self.labels

        # Calculate PCA for visualization
        self.pca = PCA(n_components=2)
        self.X_pca = self.pca.fit_transform(self.X_scaled)
        self.data_wide['pca_1'] = self.X_pca[:, 0]
        self.data_wide['pca_2'] = self.X_pca[:, 1]

        return {
            'labels': self.labels,
            'centroids': self.kmeans.cluster_centers_,
            'silhouette_score': sil_score,
            'n_clusters': k
        }

    def interpret_clusters(self) -> dict:
        """
        Interpret clusters and assign descriptive names based on centroids.

        Returns:
            Dictionary with cluster information and names
        """
        if self.kmeans is None or self.labels is None:
            raise ValueError("Must fit clustering first with fit_clustering()")

        feature_cols = getattr(self, 'feature_cols_used', [m for m in self.SELECTED_METRICS if m in self.data_wide.columns])

        self.cluster_info = {}

        # If PCA was used, calculate cluster means from original scaled features
        # Otherwise use the k-means centroids directly
        if getattr(self, 'pca_used', False) and hasattr(self, 'X_before_pca'):
            # Calculate mean of original features for each cluster
            centroids = []
            for cluster_id in range(self.kmeans.n_clusters):
                mask = self.labels == cluster_id
                cluster_mean = self.X_before_pca[mask].mean(axis=0)
                centroids.append(cluster_mean)
            centroids = np.array(centroids)
        else:
            centroids = self.kmeans.cluster_centers_

        for cluster_id in range(len(centroids)):
            centroid = centroids[cluster_id]

            # Find teams in this cluster
            cluster_teams = self.data_wide[self.data_wide['cluster_id'] == cluster_id]
            team_list = [
                f"{row['team_name']} ({row['manager_name'].split()[-1]})"
                for _, row in cluster_teams.iterrows()
            ]

            # Analyze centroid to determine characteristics
            characteristics = []
            style_scores = {}

            # Check each characteristic based on centroid values
            # Values are standardized, so >0.5 = notably above average
            threshold = 0.5

            for i, metric in enumerate(feature_cols):
                val = centroid[i]
                style_scores[metric] = val

                if metric == 'possession_percentage' and val > threshold:
                    characteristics.append('Alto possesso')
                elif metric == 'possession_percentage' and val < -threshold:
                    characteristics.append('Basso possesso')

                elif metric == 'progressive_passes' and val > threshold:
                    characteristics.append('Gioco verticale')

                elif metric == 'ppda' and val > threshold:  # Inverted: high = intense pressing
                    characteristics.append('Pressing intenso')
                elif metric == 'ppda' and val < -threshold:
                    characteristics.append('Pressing basso')

                elif metric == 'pressing_high' and val > threshold:
                    characteristics.append('Pressing alto')

                elif metric == 'counterpressing' and val > threshold:
                    characteristics.append('Contro-pressing')

                elif metric == 'counter_attacks' and val > threshold:
                    characteristics.append('Contropiede')

                elif metric == 'buildup_sequences' and val > threshold:
                    characteristics.append('Costruzione elaborata')
                elif metric == 'buildup_sequences' and val < -threshold:
                    characteristics.append('Gioco diretto')

                elif metric == 'fast_attacks' and val > threshold:
                    characteristics.append('Attacco rapido')

                elif metric == 'crosses_total' and val > threshold:
                    characteristics.append('Gioco sulle fasce')

                elif metric == 'touches_in_box' and val > threshold:
                    characteristics.append('Penetrazione centrale')

                elif metric == 'tackles' and val > threshold:
                    characteristics.append('Difesa aggressiva')

                elif metric == 'aerial_duels_defensive' and val > threshold:
                    characteristics.append('Forza aerea')

            # Generate cluster name based on cluster_id
            name = self._generate_cluster_name(cluster_id, characteristics, style_scores)
            description = self._generate_cluster_description(characteristics)

            self.cluster_info[cluster_id] = {
                'name': name,
                'description': description,
                'teams': team_list,
                'n_teams': len(team_list),
                'characteristics': characteristics,
                'centroid_raw': dict(zip(feature_cols, centroid)),
                'style_scores': style_scores
            }

        # Add cluster names to data
        self.data_wide['cluster_name'] = self.data_wide['cluster_id'].map(
            lambda x: self.cluster_info[x]['name']
        )

        return self.cluster_info

    # Fixed cluster names mapping (k=4, random_state=42, use_pca=True)
    CLUSTER_NAMES = {
        0: "Possesso Dominante",
        1: "Pressing e Verticalità",
        2: "Blocco Basso e Ripartenza",
        3: "Ampiezza e Inserimenti",
    }

    def _generate_cluster_name(self, cluster_id: int, characteristics: list, scores: dict) -> str:
        """Get the fixed name for a cluster."""
        return self.CLUSTER_NAMES.get(cluster_id, f"Cluster {cluster_id}")

    def _generate_cluster_description(self, characteristics: list) -> str:
        """Generate a description for a cluster."""
        if not characteristics:
            return "Squadre con approccio tattico equilibrato senza caratteristiche predominanti."

        char_str = ", ".join(characteristics[:3])
        return f"Squadre caratterizzate da: {char_str}."

    def get_team_style(self, team_id: int, manager_id: int) -> Optional[dict]:
        """
        Get the playing style for a specific team+manager combination.

        Args:
            team_id: Team ID
            manager_id: Manager ID

        Returns:
            Dictionary with style information or None if not found
        """
        if self.data_wide is None or 'cluster_id' not in self.data_wide.columns:
            return None

        team_row = self.data_wide[
            (self.data_wide['team_id'] == team_id) &
            (self.data_wide['manager_id'] == manager_id)
        ]

        if len(team_row) == 0:
            return None

        row = team_row.iloc[0]
        cluster_id = row['cluster_id']

        if self.cluster_info is None:
            return {
                'cluster_id': cluster_id,
                'cluster_name': f"Cluster {cluster_id}",
                'team_name': row.get('team_name', 'Unknown'),
                'manager_name': row.get('manager_name', 'Unknown'),
            }

        info = self.cluster_info[cluster_id]
        return {
            'cluster_id': cluster_id,
            'cluster_name': info['name'],
            'description': info['description'],
            'characteristics': info['characteristics'],
            'team_name': row.get('team_name', 'Unknown'),
            'manager_name': row.get('manager_name', 'Unknown'),
            'pca_coords': (row.get('pca_1', 0), row.get('pca_2', 0))
        }

    def get_cluster_radar_data(self, cluster_id: int) -> dict:
        """
        Get radar chart data for a specific cluster.

        Args:
            cluster_id: Cluster ID

        Returns:
            Dictionary with metric names and normalized values
        """
        if self.cluster_info is None:
            return {}

        info = self.cluster_info.get(cluster_id, {})
        centroid = info.get('centroid_raw', {})

        # Normalize to 0-100 scale for radar chart
        radar_data = {}
        for metric, value in centroid.items():
            # Convert from standardized to 0-100 (assuming approx -3 to +3 range)
            normalized = (value + 3) / 6 * 100
            normalized = max(0, min(100, normalized))
            radar_data[self.METRIC_NAMES_IT.get(metric, metric)] = normalized

        return radar_data

    def get_all_teams_pca(self) -> pd.DataFrame:
        """
        Get PCA coordinates for all teams for scatter plot.

        Returns:
            DataFrame with team info and PCA coordinates
        """
        if self.data_wide is None or 'pca_1' not in self.data_wide.columns:
            return pd.DataFrame()

        return self.data_wide[[
            'team_id', 'manager_id', 'team_name', 'manager_name',
            'cluster_id', 'cluster_name', 'pca_1', 'pca_2', 'matches_count'
        ]].copy()

    def export_results(self, output_path: Optional[str] = None) -> str:
        """
        Export clustering results to CSV.

        Args:
            output_path: Path to save CSV (default: data/processed/playing_styles.csv)

        Returns:
            Path to saved file
        """
        if self.data_wide is None or 'cluster_id' not in self.data_wide.columns:
            raise ValueError("Must fit clustering first")

        if output_path is None:
            output_path = Path(__file__).resolve().parent.parent / "data" / "processed" / "playing_styles.csv"

        # Prepare export data
        export_df = self.data_wide[[
            'team_id', 'manager_id', 'team_name', 'manager_name',
            'matches_count', 'cluster_id', 'cluster_name', 'pca_1', 'pca_2'
        ]].copy()

        # Add silhouette score per team
        if self.X_scaled is not None and self.labels is not None:
            from sklearn.metrics import silhouette_samples
            sample_silhouettes = silhouette_samples(self.X_scaled, self.labels)
            export_df['silhouette_score'] = sample_silhouettes

        export_df.to_csv(output_path, index=False)
        return str(output_path)

    def run_full_pipeline(self, k: Optional[int] = None, default_k: int = 4,
                          remove_correlated: bool = False, use_pca: bool = False) -> dict:
        """
        Run the complete clustering pipeline.

        Args:
            k: Number of clusters (if None, uses default_k for better interpretability)
            default_k: Default number of clusters (4 provides good balance)
            remove_correlated: Remove highly correlated features (recommended)
            use_pca: Apply PCA transformation before clustering

        Returns:
            Dictionary with all results
        """
        # Step 1: Prepare data
        self.prepare_data()

        # Step 2: Normalize (with optional correlation removal and PCA)
        self.normalize_features(remove_correlated=remove_correlated, use_pca=use_pca)

        # Step 3: Use specified k or default (k=4 provides best interpretability)
        if k is None:
            k = default_k
            print(f"Using default k={k} for better style interpretability")

        # Step 4: Fit clustering
        fit_results = self.fit_clustering(k)
        print(f"Clustering completed with silhouette score: {fit_results['silhouette_score']:.3f}")

        # Step 5: Interpret clusters
        cluster_info = self.interpret_clusters()

        # Step 6: Export results
        output_path = self.export_results()
        print(f"Results exported to: {output_path}")

        return {
            'n_clusters': k,
            'silhouette_score': fit_results['silhouette_score'],
            'cluster_info': cluster_info,
            'output_path': output_path
        }


def _fetch_all_rows(client, table_name: str, select_columns: str = '*', page_size: int = 1000) -> list:
    """Fetch all rows from a Supabase table using pagination."""
    all_data = []
    offset = 0

    while True:
        response = client.table(table_name).select(select_columns).range(
            offset, offset + page_size - 1
        ).execute()

        if not response.data:
            break

        all_data.extend(response.data)

        if len(response.data) < page_size:
            break

        offset += page_size

    return all_data


def load_clusterer_from_supabase(min_matches: int = 5) -> PlayingStyleClusterer:
    """
    Load clusterer with data from Supabase.

    Args:
        min_matches: Minimum matches required

    Returns:
        Initialized PlayingStyleClusterer
    """
    from config.supabase_config import get_supabase_client

    client = get_supabase_client()

    # Load team_metrics
    metrics_data = _fetch_all_rows(client, 'team_metrics')
    team_metrics = pd.DataFrame(metrics_data)

    # Load team_manager_combinations with team/manager names
    combos_data = _fetch_all_rows(client, 'team_manager_combinations')
    combinations = pd.DataFrame(combos_data)

    # Load team names
    teams_data = _fetch_all_rows(client, 'teams', 'team_id, team_name')
    teams_df = pd.DataFrame(teams_data)

    # Load manager names
    managers_data = _fetch_all_rows(client, 'managers', 'manager_id, manager_name')
    managers_df = pd.DataFrame(managers_data)

    # Add team_name and manager_name to combinations
    if not combinations.empty and not teams_df.empty:
        combinations = combinations.merge(
            teams_df[['team_id', 'team_name']],
            on='team_id',
            how='left'
        )
    if not combinations.empty and not managers_df.empty:
        combinations = combinations.merge(
            managers_df[['manager_id', 'manager_name']],
            on='manager_id',
            how='left'
        )

    return PlayingStyleClusterer(
        team_metrics_df=team_metrics,
        combinations_df=combinations,
        min_matches=min_matches
    )


def load_clusterer_from_csv(min_matches: int = 5) -> PlayingStyleClusterer:
    """
    Load clusterer with data from CSV files (fallback for local development).

    Args:
        min_matches: Minimum matches required

    Returns:
        Initialized PlayingStyleClusterer
    """
    data_dir = Path(__file__).resolve().parent.parent / "data" / "processed"

    team_metrics = pd.read_csv(data_dir / "team_metrics.csv")
    combinations = pd.read_csv(data_dir / "team_manager_combinations.csv")

    # Add manager_id if not present (legacy CSV format)
    if 'manager_id' not in combinations.columns:
        combinations = combinations.reset_index(drop=True)
        combinations['manager_id'] = combinations.index + 1

    return PlayingStyleClusterer(
        team_metrics_df=team_metrics,
        combinations_df=combinations,
        min_matches=min_matches
    )


def load_clusterer_from_data(min_matches: int = 5) -> PlayingStyleClusterer:
    """
    Convenience function to load clusterer with data.

    Uses Supabase if DATA_SOURCE="supabase", otherwise falls back to CSV.

    Args:
        min_matches: Minimum matches required

    Returns:
        Initialized PlayingStyleClusterer
    """
    if DATA_SOURCE == "supabase":
        try:
            return load_clusterer_from_supabase(min_matches)
        except Exception as e:
            print(f"Warning: Failed to load from Supabase ({e}), falling back to CSV")
            return load_clusterer_from_csv(min_matches)
    else:
        return load_clusterer_from_csv(min_matches)


if __name__ == "__main__":
    # Quick test
    print("Loading data and running clustering pipeline...")
    clusterer = load_clusterer_from_data(min_matches=5)
    results = clusterer.run_full_pipeline()

    print("\n" + "="*50)
    print("CLUSTERING RESULTS")
    print("="*50)

    for cluster_id, info in results['cluster_info'].items():
        print(f"\n### {info['name']} ({info['n_teams']} squadre)")
        print(f"    {info['description']}")
        print(f"    Squadre: {', '.join(info['teams'][:5])}{'...' if len(info['teams']) > 5 else ''}")
