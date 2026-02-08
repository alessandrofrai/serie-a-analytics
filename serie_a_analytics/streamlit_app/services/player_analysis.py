"""
Serie A Analytics - Player Analysis Service

This module provides z-score based analysis of players by comparing them
to others in the same positional role across the championship.

Key Features:
- Position grouping (GK, CB, FB, DM, CM, AM, W, FW)
- Z-score calculation by role
- Strength/weakness identification
- Role-specific metric relevance

The z-score indicates how many standard deviations a player's metric
is from the mean of players in the same role:
- z > 1.5: Excellent (top ~7%)
- z > 1.0: Very Good (top ~16%)
- z > 0.5: Good (top ~31%)
- z < -0.5: Below Average
- z < -1.0: Weak (bottom ~16%)
- z < -1.5: Very Weak (bottom ~7%)
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class RoleGrouping(Enum):
    """Position role groupings for player comparison."""
    GK = "Goalkeeper"
    CB = "Center Back"
    FB = "Full Back"
    DM = "Defensive Midfielder"
    CM = "Central Midfielder"
    AM = "Attacking Midfielder"
    W = "Winger"
    FW = "Forward"


# Map StatsBomb positions to role groups
POSITION_TO_ROLE: Dict[str, RoleGrouping] = {
    # Goalkeeper
    "Goalkeeper": RoleGrouping.GK,

    # Center Backs
    "Center Back": RoleGrouping.CB,
    "Left Center Back": RoleGrouping.CB,
    "Right Center Back": RoleGrouping.CB,

    # Full Backs (including wing backs)
    "Left Back": RoleGrouping.FB,
    "Right Back": RoleGrouping.FB,
    "Left Wing Back": RoleGrouping.FB,
    "Right Wing Back": RoleGrouping.FB,

    # Defensive Midfielders
    "Center Defensive Midfield": RoleGrouping.DM,
    "Left Defensive Midfield": RoleGrouping.DM,
    "Right Defensive Midfield": RoleGrouping.DM,

    # Central Midfielders
    "Center Midfield": RoleGrouping.CM,
    "Left Center Midfield": RoleGrouping.CM,
    "Right Center Midfield": RoleGrouping.CM,

    # Attacking Midfielders (including wide midfielders)
    "Center Attacking Midfield": RoleGrouping.AM,
    "Left Attacking Midfield": RoleGrouping.AM,
    "Right Attacking Midfield": RoleGrouping.AM,
    "Left Midfield": RoleGrouping.AM,
    "Right Midfield": RoleGrouping.AM,

    # Wingers
    "Left Wing": RoleGrouping.W,
    "Right Wing": RoleGrouping.W,

    # Forwards
    "Center Forward": RoleGrouping.FW,
    "Left Center Forward": RoleGrouping.FW,
    "Right Center Forward": RoleGrouping.FW,
}

# Role groups for easy reference
ROLE_GROUPS = {
    RoleGrouping.GK: "Portiere",
    RoleGrouping.CB: "Difensore Centrale",
    RoleGrouping.FB: "Terzino",
    RoleGrouping.DM: "Mediano",
    RoleGrouping.CM: "Centrocampista",
    RoleGrouping.AM: "Trequartista",
    RoleGrouping.W: "Ala",
    RoleGrouping.FW: "Attaccante",
}

# Metrics relevant for each role (for meaningful z-score comparison)
# Only include metrics that make sense to compare for each role
ROLE_RELEVANT_METRICS: Dict[RoleGrouping, Dict[str, List[str]]] = {
    RoleGrouping.GK: {
        "strengths": [  # Higher is better
            "passes_total", "passes_short", "passes_long",
        ],
        "weaknesses": [  # Lower is better (or these are weaknesses when high)
            "passes_total", "passes_short", "passes_long",  # Low = bad distribution
        ],
    },
    RoleGrouping.CB: {
        "strengths": [
            "clearances", "blocks", "interceptions", "tackles",
            "aerial_duels_open_play", "aerial_duels_set_pieces",
            "passes_total", "passes_long", "progressive_passes",
        ],
        "weaknesses": [
            "clearances", "interceptions", "tackles",
            "aerial_duels_open_play", "passes_total",
        ],
    },
    RoleGrouping.FB: {
        "strengths": [
            "crosses_total", "progressive_passes", "progressive_carries",
            "dribbles_total", "key_passes", "tackles", "interceptions",
            "passes_total",
        ],
        "weaknesses": [
            "crosses_total", "progressive_passes", "tackles",
            "passes_total", "dribbles_total",
        ],
    },
    RoleGrouping.DM: {
        "strengths": [
            "tackles", "interceptions", "ball_recoveries",
            "passes_total", "passes_medium", "progressive_passes",
            "ground_duels_defensive",
        ],
        "weaknesses": [
            "tackles", "interceptions", "ball_recoveries",
            "passes_total", "progressive_passes",
        ],
    },
    RoleGrouping.CM: {
        "strengths": [
            "passes_total", "passes_medium", "progressive_passes",
            "progressive_carries", "key_passes", "through_balls",
            "xa_total", "tackles", "interceptions", "ball_recoveries",
        ],
        "weaknesses": [
            "passes_total", "progressive_passes", "key_passes",
            "xa_total", "ball_recoveries",
        ],
    },
    RoleGrouping.AM: {
        "strengths": [
            "key_passes", "through_balls", "xa_total",
            "dribbles_total", "progressive_carries",
            "shots_total", "shots_on_target", "xg_total",
            "goals_scored",
        ],
        "weaknesses": [
            "key_passes", "xa_total", "dribbles_total",
            "shots_total", "xg_total",
        ],
    },
    RoleGrouping.W: {
        "strengths": [
            "crosses_total", "dribbles_total", "progressive_carries",
            "key_passes", "shots_total", "xg_total", "goals_scored",
            "xa_total",
        ],
        "weaknesses": [
            "crosses_total", "dribbles_total", "key_passes",
            "shots_total", "xg_total",
        ],
    },
    RoleGrouping.FW: {
        "strengths": [
            "shots_total", "shots_on_target", "xg_total", "goals_scored",
            "big_chances", "goal_conversion_rate", "touches_in_box",
            "aerial_duels_open_play",
        ],
        "weaknesses": [
            "shots_total", "xg_total", "goals_scored",
            "big_chances", "touches_in_box",
        ],
    },
}

# Italian names for metrics (for display)
METRIC_NAMES_IT: Dict[str, str] = {
    # Attacking
    'shots_total': 'Tiri',
    'shots_on_target': 'Tiri in Porta',
    'xg_total': 'xG',
    'goals_scored': 'Gol',
    'goal_conversion_rate': 'Conversione Tiri',
    'big_chances': 'Grandi Occasioni',
    'touches_in_box': 'Tocchi in Area',

    # Defending
    'tackles': 'Contrasti',
    'interceptions': 'Intercetti',
    'clearances': 'Respinte',
    'blocks': 'Blocchi',
    'aerial_duels_open_play': 'Duelli Aerei',
    'aerial_duels_set_pieces': 'Duelli Aerei (Palle Inattive)',
    'ground_duels_defensive': 'Duelli a Terra (Dif.)',

    # Possession
    'passes_total': 'Passaggi',
    'passes_short': 'Passaggi Corti',
    'passes_medium': 'Passaggi Medi',
    'passes_long': 'Passaggi Lunghi',
    'progressive_passes': 'Passaggi Progressivi',
    'progressive_carries': 'Conduzioni Progressive',
    'crosses_total': 'Cross',
    'dribbles_total': 'Dribbling',
    'key_passes': 'Passaggi Chiave',
    'through_balls': 'Filtranti',
    'xa_total': 'xA',
    'ball_recoveries': 'Recuperi',
    'switches_of_play': 'Cambi Gioco',
}


@dataclass
class PlayerMetricZScore:
    """Z-score for a single metric."""
    metric_name: str
    metric_name_it: str
    player_value: float
    role_mean: float
    role_std: float
    z_score: float
    n_players_in_role: int


@dataclass
class PlayerStrengthWeakness:
    """Identified strength or weakness for a player."""
    metric_name: str
    metric_name_it: str
    z_score: float
    player_value: float
    role_mean: float
    interpretation: str  # "excellent", "very_good", "good", "below_average", "weak", "very_weak"


@dataclass
class PlayerAnalysisResult:
    """Complete analysis result for a player."""
    player_id: int
    player_name: str
    role: RoleGrouping
    role_name_it: str
    minutes_played: int
    strengths: List[PlayerStrengthWeakness]
    weaknesses: List[PlayerStrengthWeakness]
    all_z_scores: Dict[str, PlayerMetricZScore]


class PlayerAnalyzer:
    """
    Analyzes players by calculating z-scores compared to same-role players.

    This class computes z-scores for each player's metrics relative to all
    players in the same positional role across the championship. This allows
    meaningful comparison (e.g., comparing a striker's xG to other strikers,
    not to goalkeepers).
    """

    def __init__(
        self,
        player_metrics_df: pd.DataFrame,
        player_minutes_df: pd.DataFrame,
        min_minutes: int = 270  # Minimum 3 full games
    ):
        """
        Initialize the analyzer.

        Args:
            player_metrics_df: DataFrame with player metrics
            player_minutes_df: DataFrame with player positions and minutes
            min_minutes: Minimum minutes to include a player in analysis
        """
        self.player_metrics = player_metrics_df
        self.player_minutes = player_minutes_df
        self.min_minutes = min_minutes

        # Build player position map (most common position)
        self._player_positions = self._build_player_positions()

        # Pre-calculate role-based statistics
        self._role_stats = self._calculate_role_statistics()

    def _build_player_positions(self) -> Dict[int, Tuple[str, RoleGrouping]]:
        """
        Determine each player's primary position and role.

        Returns:
            Dict mapping player_id to (position_name, RoleGrouping)
        """
        positions = {}

        if self.player_minutes is None or len(self.player_minutes) == 0:
            return positions

        # Group by player and find most common position
        player_groups = self.player_minutes.groupby('player_id')

        for player_id, group in player_groups:
            # Skip unknown positions
            valid_positions = group[
                (group['position'] != 'Unknown') &
                (group['position'].notna())
            ]

            if len(valid_positions) == 0:
                continue

            # Weight by minutes played
            position_minutes = valid_positions.groupby('position')['minutes_played'].sum()
            if len(position_minutes) == 0:
                continue

            primary_position = position_minutes.idxmax()
            total_minutes = position_minutes.sum()

            if total_minutes < self.min_minutes:
                continue

            role = POSITION_TO_ROLE.get(primary_position)
            if role is None:
                continue

            positions[int(player_id)] = (primary_position, role)

        return positions

    def _calculate_role_statistics(self) -> Dict[RoleGrouping, Dict[str, Dict[str, float]]]:
        """
        Calculate mean and std for each metric by role.

        Returns:
            Dict mapping RoleGrouping to {metric_name: {mean, std, n}}
        """
        role_stats = {}

        # Get players with their roles
        players_by_role: Dict[RoleGrouping, List[int]] = {}
        for player_id, (_, role) in self._player_positions.items():
            if role not in players_by_role:
                players_by_role[role] = []
            players_by_role[role].append(player_id)

        # Calculate statistics for each role
        for role, player_ids in players_by_role.items():
            role_stats[role] = {}

            # Get metrics for these players
            role_metrics = self.player_metrics[
                self.player_metrics['player_id'].isin(player_ids)
            ]

            # Group by metric and calculate stats
            for metric_name in role_metrics['metric_name'].unique():
                metric_values = role_metrics[
                    role_metrics['metric_name'] == metric_name
                ]['metric_value_p90'].values

                if len(metric_values) < 3:  # Need at least 3 for meaningful comparison
                    continue

                role_stats[role][metric_name] = {
                    'mean': float(np.mean(metric_values)),
                    'std': float(np.std(metric_values)) if np.std(metric_values) > 0 else 0.001,
                    'n': len(metric_values)
                }

        return role_stats

    def get_player_role(self, player_id: int) -> Optional[Tuple[str, RoleGrouping]]:
        """Get player's position and role."""
        return self._player_positions.get(player_id)

    def calculate_player_z_scores(
        self,
        player_id: int,
        team_id: int,
        manager_id: int
    ) -> Optional[PlayerAnalysisResult]:
        """
        Calculate z-scores for a player compared to same-role players.

        Args:
            player_id: Player ID
            team_id: Team ID for filtering metrics
            manager_id: Manager ID for filtering metrics

        Returns:
            PlayerAnalysisResult or None if player not analyzable
        """
        # Get player's role
        position_info = self._player_positions.get(player_id)
        if position_info is None:
            return None

        position_name, role = position_info
        role_name_it = ROLE_GROUPS.get(role, position_name)

        # Get role statistics
        role_stats = self._role_stats.get(role)
        if role_stats is None or len(role_stats) == 0:
            return None

        # Get player's metrics for this team/manager
        player_metrics = self.player_metrics[
            (self.player_metrics['player_id'] == player_id) &
            (self.player_metrics['team_id'] == team_id) &
            (self.player_metrics['manager_id'] == manager_id)
        ]

        if len(player_metrics) == 0:
            return None

        # Get player name and minutes
        player_name = player_metrics.iloc[0]['player_name']
        total_minutes = int(player_metrics.iloc[0].get('total_minutes', 0))

        if total_minutes < self.min_minutes:
            return None

        # Calculate z-scores for each metric
        all_z_scores = {}
        for _, row in player_metrics.iterrows():
            metric_name = row['metric_name']
            player_value = row['metric_value_p90']

            if metric_name not in role_stats:
                continue

            stats = role_stats[metric_name]
            z = (player_value - stats['mean']) / stats['std']

            all_z_scores[metric_name] = PlayerMetricZScore(
                metric_name=metric_name,
                metric_name_it=METRIC_NAMES_IT.get(metric_name, metric_name),
                player_value=player_value,
                role_mean=stats['mean'],
                role_std=stats['std'],
                z_score=z,
                n_players_in_role=stats['n']
            )

        # Identify strengths and weaknesses using role-relevant metrics
        relevant_metrics = ROLE_RELEVANT_METRICS.get(role, {})
        strength_metrics = relevant_metrics.get('strengths', [])
        weakness_metrics = relevant_metrics.get('weaknesses', [])

        # Find top strengths (highest positive z-scores among relevant metrics)
        strengths = []
        for metric_name in strength_metrics:
            if metric_name in all_z_scores:
                zs = all_z_scores[metric_name]
                if zs.z_score > 0.5:  # At least above average
                    strengths.append(PlayerStrengthWeakness(
                        metric_name=metric_name,
                        metric_name_it=zs.metric_name_it,
                        z_score=zs.z_score,
                        player_value=zs.player_value,
                        role_mean=zs.role_mean,
                        interpretation=self._interpret_z_score(zs.z_score, is_strength=True)
                    ))

        # Sort by z-score and take top 3
        strengths.sort(key=lambda x: x.z_score, reverse=True)
        strengths = strengths[:3]

        # Find top weaknesses (lowest negative z-scores among relevant metrics)
        weaknesses = []
        for metric_name in weakness_metrics:
            if metric_name in all_z_scores:
                zs = all_z_scores[metric_name]
                if zs.z_score < -0.5:  # Below average
                    weaknesses.append(PlayerStrengthWeakness(
                        metric_name=metric_name,
                        metric_name_it=zs.metric_name_it,
                        z_score=zs.z_score,
                        player_value=zs.player_value,
                        role_mean=zs.role_mean,
                        interpretation=self._interpret_z_score(zs.z_score, is_strength=False)
                    ))

        # Sort by z-score (most negative first) and take top 3
        weaknesses.sort(key=lambda x: x.z_score)
        weaknesses = weaknesses[:3]

        return PlayerAnalysisResult(
            player_id=player_id,
            player_name=player_name,
            role=role,
            role_name_it=role_name_it,
            minutes_played=total_minutes,
            strengths=strengths,
            weaknesses=weaknesses,
            all_z_scores=all_z_scores
        )

    @staticmethod
    def _interpret_z_score(z: float, is_strength: bool) -> str:
        """Interpret z-score for display."""
        if is_strength:
            if z >= 2.0:
                return "exceptional"
            elif z >= 1.5:
                return "excellent"
            elif z >= 1.0:
                return "very_good"
            else:
                return "good"
        else:
            if z <= -2.0:
                return "critical"
            elif z <= -1.5:
                return "very_weak"
            elif z <= -1.0:
                return "weak"
            else:
                return "below_average"

    def analyze_team_players(
        self,
        team_id: int,
        manager_id: int,
        player_ids: List[int]
    ) -> Dict[int, PlayerAnalysisResult]:
        """
        Analyze multiple players for a team.

        Args:
            team_id: Team ID
            manager_id: Manager ID
            player_ids: List of player IDs to analyze

        Returns:
            Dict mapping player_id to PlayerAnalysisResult
        """
        results = {}
        for player_id in player_ids:
            analysis = self.calculate_player_z_scores(player_id, team_id, manager_id)
            if analysis is not None:
                results[player_id] = analysis
        return results
