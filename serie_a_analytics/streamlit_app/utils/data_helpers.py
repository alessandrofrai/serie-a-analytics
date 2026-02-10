"""
Data loading and helper functions for Serie A Analytics.

This module contains all data loading and helper functions that are shared
between the main app and dashboard pages. These functions do NOT contain
any Streamlit-specific code at the top level, so they can be safely imported.
"""

import os
import random
import re
import subprocess
import sys
import unicodedata
from typing import Dict, Optional

import pandas as pd
from pathlib import Path
import streamlit as st

# Add parent path for config imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import centralized configuration (supports both .env and st.secrets)
from config.settings import DATA_SOURCE

# Minimum matches required for a team+manager combination
MIN_MATCHES = 5

# Percentile thresholds
TOP_PERCENTILE = 0.25
BOTTOM_PERCENTILE = 0.25

# Position ID to position name mapping (StatsBomb)
POSITION_ID_MAP = {
    1: "Goalkeeper",
    2: "Right Back",
    3: "Right Center Back",
    4: "Center Back",
    5: "Left Center Back",
    6: "Left Back",
    7: "Right Wing Back",
    8: "Left Wing Back",
    9: "Right Defensive Midfield",
    10: "Center Defensive Midfield",
    11: "Left Defensive Midfield",
    12: "Right Midfield",
    13: "Right Center Midfield",
    14: "Center Midfield",
    15: "Left Center Midfield",
    16: "Left Midfield",
    17: "Right Wing",
    18: "Right Attacking Midfield",
    19: "Center Attacking Midfield",
    20: "Left Attacking Midfield",
    21: "Left Wing",
    22: "Right Center Forward",
    23: "Center Forward",
    24: "Left Center Forward",
    25: "Striker",
}


def get_data_dir():
    """Get the data directory path."""
    return Path(__file__).resolve().parent.parent.parent / "data" / "processed"


def _get_supabase_client():
    """Get Supabase client (lazy import to avoid circular imports)."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from config.supabase_config import get_supabase_client
    return get_supabase_client()


def _fetch_all_rows(client, table_name, select_columns='*', page_size=1000):
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


# Fun loading messages for the loading animation
LOADING_MESSAGES = [
    "🧹 ...Spolverando le linee del campo... 🧹",
    "✨ ...Lucidando i pali della porta... ✨",
    "🪢 ...Districando i nodi della rete... 🪢",
    "🪑 ...Annaffiando le panchine... 🪑",
    "🌱 ...Contando i fili d'erba uno per uno... 🌱",
    "🎈 ...Gonfiando i palloni a fiato... 🎈",
    "📐 ...Misurando il fuorigioco col metro da sarta... 📐",
    "🧤 ...Insaponando i guanti del portiere... 🧤",
    "🎺 ...Accordando la trombetta del tifoso... 🎺",
    "🪣 ...Svuotando le pozzanghere con un cucchiaino... 🪣",
    "🔧 ...Avvitando il dischetto del centrocampo... 🔧",
    "🪮 ...Pettinando l'erba del centrocampo... 🪮",
    "🧣 ...Mettendo la sciarpa ai pali della porta... 🧣",
    "🍼 ...Dando il biberon al pallone... 🍼",
    "🧴 ...Mettendo la crema solare alla traversa... 🧴",
    "🎀 ...Mettendo un fiocchetto alle bandierine del corner... 🎀",
    "☂️ ...Riparando il dischetto dalla pioggia... ☂️",
    "🛏️ ...Rifacendo il letto all'area di rigore... 🛏️",
    "🎁 ...Incartando il fischietto dell'arbitro... 🎁",
]


@st.cache_data(ttl=3600, show_spinner=False)
def _load_supabase_table(table_name: str, select_columns: str = '*'):
    """Load a single table from Supabase (cached separately)."""
    client = _get_supabase_client()
    data = _fetch_all_rows(client, table_name, select_columns)
    return pd.DataFrame(data)


def load_data_from_supabase():
    """Load data from Supabase database with fun loading messages."""

    # Check if this is a fresh load (not from cache)
    # We use a session state flag to track first load
    is_first_load = 'data_loaded' not in st.session_state

    try:
        if is_first_load:
            # Create a placeholder that will disappear after loading
            loading_placeholder = st.empty()

            # Shuffle messages for variety
            messages = random.sample(LOADING_MESSAGES, len(LOADING_MESSAGES))
            shown_messages = []

            def show_message():
                # Add new message to the list
                shown_messages.append(messages[len(shown_messages) % len(messages)])
                # Render ALL messages accumulated so far
                html_lines = "".join(
                    f"<div style='color:#6b7280;font-size:1.6rem;padding:0.4rem 0;'>"
                    f"{msg}</div>"
                    for msg in shown_messages
                )
                loading_placeholder.markdown(
                    f"<div style='text-align:center;padding:1.5rem;background:#f8fafc;border-radius:12px;'>"
                    f"{html_lines}</div>",
                    unsafe_allow_html=True
                )

            # Load each table with a fun message
            show_message()
            teams_df = _load_supabase_table('teams', 'team_id, team_name')

            show_message()
            managers_df = _load_supabase_table('managers', 'manager_id, manager_name, team_id, matches_count')

            show_message()
            combinations_df = _load_supabase_table('team_manager_combinations', 'team_id, manager_id, matches_count')

            show_message()
            team_metrics_df = _load_supabase_table('team_metrics')

            show_message()
            players_df = _load_supabase_table('players', 'player_id, player_name')

            show_message()
            player_metrics_df = _load_supabase_table('player_metrics')

            show_message()
            formations_df = _load_supabase_table('formations')

            show_message()
            try:
                performances_df = _load_supabase_table('match_performances')
            except Exception:
                performances_df = pd.DataFrame()

            # Clear ALL loading messages - they disappear completely!
            loading_placeholder.empty()

            st.session_state.data_loaded = True
        else:
            # Data already loaded before, just fetch from cache silently
            teams_df = _load_supabase_table('teams', 'team_id, team_name')
            managers_df = _load_supabase_table('managers', 'manager_id, manager_name, team_id, matches_count')
            combinations_df = _load_supabase_table('team_manager_combinations', 'team_id, manager_id, matches_count')
            team_metrics_df = _load_supabase_table('team_metrics')
            players_df = _load_supabase_table('players', 'player_id, player_name')
            player_metrics_df = _load_supabase_table('player_metrics')
            formations_df = _load_supabase_table('formations')
            try:
                performances_df = _load_supabase_table('match_performances')
            except Exception:
                performances_df = pd.DataFrame()

        # Add team_name to managers
        if not managers_df.empty and not teams_df.empty:
            managers_df = managers_df.merge(
                teams_df[['team_id', 'team_name']],
                on='team_id',
                how='left'
            )

        # Add team_name and manager_name to combinations
        if not combinations_df.empty:
            if not teams_df.empty:
                combinations_df = combinations_df.merge(
                    teams_df[['team_id', 'team_name']],
                    on='team_id',
                    how='left'
                )
            if not managers_df.empty:
                combinations_df = combinations_df.merge(
                    managers_df[['manager_id', 'manager_name']].drop_duplicates(),
                    on='manager_id',
                    how='left'
                )

        # Add player_name to player_metrics
        if not player_metrics_df.empty and not players_df.empty:
            player_metrics_df = player_metrics_df.merge(
                players_df[['player_id', 'player_name']],
                on='player_id',
                how='left'
            )

        # Load additional tables from Supabase
        player_minutes_df = _load_supabase_table('player_minutes')
        matches_df = _load_supabase_table('matches')

        # Build data dictionary
        data = {
            'teams': teams_df,
            'managers': managers_df,
            'combinations': combinations_df,
            'team_metrics': team_metrics_df,
            'player_metrics': player_metrics_df,
            'players': players_df,
            'formations': formations_df,
            'performances': performances_df,  # For scatterplot
            'player_minutes': player_minutes_df if len(player_minutes_df) > 0 else None,
            'matches': matches_df if len(matches_df) > 0 else None,
        }

        # Store original combinations for manager_id mapping
        original_combinations = data['combinations'].copy()

        # Filter combinations with less than MIN_MATCHES
        data['combinations'] = data['combinations'][
            data['combinations']['matches_count'] >= MIN_MATCHES
        ].reset_index(drop=True)

        # Create mapping from (team_id, manager_name) to manager_id
        data['manager_id_map'] = {}
        for _, row in original_combinations.iterrows():
            if row['matches_count'] >= MIN_MATCHES:
                data['manager_id_map'][(row['team_id'], row['manager_name'])] = row['manager_id']

        # Create set of valid (team_id, manager_id) pairs
        valid_pairs = set()
        for _, row in original_combinations.iterrows():
            if row['matches_count'] >= MIN_MATCHES:
                valid_pairs.add((row['team_id'], row['manager_id']))

        # Filter team_metrics to only include valid combinations
        if 'manager_id' in data['team_metrics'].columns:
            data['team_metrics'] = data['team_metrics'][
                data['team_metrics'].apply(
                    lambda r: (r['team_id'], r['manager_id']) in valid_pairs, axis=1
                )
            ].reset_index(drop=True)

        data['valid_pairs'] = valid_pairs
        data['total_valid_combinations'] = len(valid_pairs)

        # CSV fallback only for local development (DATA_SOURCE != "supabase")
        # On Streamlit Cloud, all data comes from Supabase
        if data['player_minutes'] is None:
            data_dir = get_data_dir()
            player_minutes_path = data_dir / 'player_minutes.csv'
            if player_minutes_path.exists():
                data['player_minutes'] = pd.read_csv(player_minutes_path)

        if data['matches'] is None:
            data_dir = get_data_dir()
            matches_path = data_dir.parent / 'raw' / 'matches' / 'all_matches.csv'
            if matches_path.exists():
                data['matches'] = pd.read_csv(matches_path)

        if data['performances'].empty:
            data_dir = get_data_dir()
            performances_path = data_dir / 'match_performance_scatterplot.csv'
            if performances_path.exists():
                data['performances'] = pd.read_csv(performances_path)

        return data

    except Exception as e:
        st.error(f"Error loading data from Supabase: {e}")
        return None


def load_data():
    """Load processed data from configured source (Supabase or CSV).

    Note: Caching is handled at the individual table level for Supabase,
    and at function level for CSV loading.
    """
    # Use Supabase if configured
    if DATA_SOURCE == "supabase":
        return load_data_from_supabase()

    # Fallback to CSV
    return load_data_from_csv()


@st.cache_data(show_spinner="Caricamento dati...")
def load_data_from_csv():
    """Load processed data from CSV files and filter by MIN_MATCHES."""
    data_dir = get_data_dir()

    if not data_dir.exists():
        return None

    try:
        data = {
            'teams': pd.read_csv(data_dir / 'teams.csv'),
            'managers': pd.read_csv(data_dir / 'managers.csv'),
            'combinations': pd.read_csv(data_dir / 'team_manager_combinations.csv'),
            'team_metrics': pd.read_csv(data_dir / 'team_metrics.csv'),
            'player_metrics': pd.read_csv(data_dir / 'player_metrics.csv'),
            'players': pd.read_csv(data_dir / 'players.csv'),
            'formations': pd.read_csv(data_dir / 'formations.csv'),
        }

        player_minutes_path = data_dir / 'player_minutes.csv'
        if player_minutes_path.exists():
            data['player_minutes'] = pd.read_csv(player_minutes_path)
        else:
            data['player_minutes'] = None

        # Load matches for manager filtering
        matches_path = data_dir.parent / 'raw' / 'matches' / 'all_matches.csv'
        if matches_path.exists():
            data['matches'] = pd.read_csv(matches_path)
        else:
            data['matches'] = None

        # Load performances for scatterplot
        performances_path = data_dir / 'match_performance_scatterplot.csv'
        if performances_path.exists():
            data['performances'] = pd.read_csv(performances_path)
        else:
            data['performances'] = pd.DataFrame()

        # Store original combinations for manager_id mapping
        original_combinations = data['combinations'].copy()
        original_combinations['original_idx'] = original_combinations.index

        # Filter combinations with less than MIN_MATCHES
        data['combinations'] = data['combinations'][
            data['combinations']['matches_count'] >= MIN_MATCHES
        ].reset_index(drop=True)

        # Create mapping from (team_id, manager_name) to manager_id
        data['manager_id_map'] = {}
        for idx, row in original_combinations.iterrows():
            if row['matches_count'] >= MIN_MATCHES:
                data['manager_id_map'][(row['team_id'], row['manager_name'])] = idx + 1

        # Create set of valid (team_id, manager_id) pairs
        valid_pairs = set()
        for idx, row in original_combinations.iterrows():
            if row['matches_count'] >= MIN_MATCHES:
                valid_pairs.add((row['team_id'], idx + 1))

        # Filter team_metrics to only include valid combinations
        if 'manager_id' in data['team_metrics'].columns:
            data['team_metrics'] = data['team_metrics'][
                data['team_metrics'].apply(
                    lambda r: (r['team_id'], r['manager_id']) in valid_pairs, axis=1
                )
            ].reset_index(drop=True)

        data['valid_pairs'] = valid_pairs
        data['total_valid_combinations'] = len(valid_pairs)

        return data
    except FileNotFoundError as e:
        return None


@st.cache_data(ttl=3600)
def load_match_xg_data():
    """Load match xG data from Supabase (with CSV fallback for local dev)."""
    # Try Supabase first
    if DATA_SOURCE == "supabase":
        try:
            client = _get_supabase_client()
            data = _fetch_all_rows(client, 'match_xg')
            if data:
                return pd.DataFrame(data)
        except Exception:
            pass  # Fall through to CSV fallback

    # CSV fallback for local development
    data_path = get_data_dir() / "match_xg_by_cluster.csv"
    if data_path.exists():
        return pd.read_csv(data_path)
    return None


@st.cache_data(ttl=3600)
def load_match_formations_data():
    """Load match formations data from Supabase (with CSV fallback for local dev)."""
    # Try Supabase first
    if DATA_SOURCE == "supabase":
        try:
            client = _get_supabase_client()
            data = _fetch_all_rows(client, 'match_formations')
            if data:
                return pd.DataFrame(data)
        except Exception:
            pass  # Fall through to CSV fallback

    # CSV fallback for local development
    data_path = get_data_dir() / "match_formations.csv"
    if data_path.exists():
        return pd.read_csv(data_path)
    return None


@st.cache_resource(show_spinner="Caricamento dati...")
def get_playing_style_clusterer():
    """Load and cache the playing style clusterer."""
    try:
        from clustering.playing_style import load_clusterer_from_data
        clusterer = load_clusterer_from_data(min_matches=MIN_MATCHES)
        clusterer.run_full_pipeline(k=4, use_pca=True)
        return clusterer
    except Exception as e:
        print(f"Error loading clusterer: {e}")
        return None


def get_team_playing_style(team_id: int, manager_id: int) -> dict:
    """Get the playing style for a team+manager combination."""
    clusterer = get_playing_style_clusterer()
    if clusterer is None:
        return None
    return clusterer.get_team_style(team_id, manager_id)


def get_xg_by_opponent_cluster(team_id: int, manager_name: str) -> dict:
    """
    Calculate average xG for/against by opponent cluster for a team+manager.
    """
    match_xg_df = load_match_xg_data()
    if match_xg_df is None:
        return {}

    team_matches = match_xg_df[
        (match_xg_df['team_id'] == team_id) &
        (match_xg_df['team_manager'] == manager_name) &
        (match_xg_df['opponent_cluster'] != 'Unknown')
    ].copy()

    if len(team_matches) == 0:
        return {}

    result = {}
    for cluster_name in team_matches['opponent_cluster'].unique():
        cluster_matches = team_matches[team_matches['opponent_cluster'] == cluster_name]
        n_matches = len(cluster_matches)
        xg_for_avg = cluster_matches['xg_for'].mean()
        xg_against_avg = cluster_matches['xg_against'].mean()

        result[cluster_name] = {
            'matches': n_matches,
            'xg_for_avg': round(xg_for_avg, 2),
            'xg_against_avg': round(xg_against_avg, 2),
            'xg_diff': round(xg_for_avg - xg_against_avg, 2),
        }

    return result


def get_formation_stats(team_id: int, manager_name: str) -> dict:
    """Get formation statistics and match history for a team+manager."""
    formations_df = load_match_formations_data()
    if formations_df is None:
        return {}

    team_formations = formations_df[
        (formations_df['team_id'] == team_id) &
        (formations_df['manager_name'] == manager_name)
    ].copy()

    if len(team_formations) == 0:
        return {}

    team_formations = team_formations.sort_values('match_week')
    formation_counts = team_formations['formation'].value_counts()
    total_matches = len(team_formations)

    formations_all = []
    for formation, count in formation_counts.items():
        pct = round(count / total_matches * 100)
        formations_all.append({
            'formation': formation,
            'count': count,
            'percentage': pct,
        })

    formations_list = formations_all[:3]

    timeline = []
    for _, row in team_formations.iterrows():
        timeline.append({
            'match_week': int(row['match_week']),
            'formation': row['formation'],
            'opponent': row.get('opponent_name', ''),
            'is_home': row.get('is_home', True),
        })

    return {
        'formations': formations_list,
        'formations_all': formations_all,
        'total_matches': total_matches,
        'timeline': timeline,
        'primary_formation': formations_list[0]['formation'] if formations_list else '4-3-3',
    }


def extract_surname(full_name: str) -> str:
    """Extract surname handling particles like De, Di, Van, Von, La, etc."""
    if not full_name or full_name == 'Unknown':
        return 'Unknown'

    particles = {'de', 'di', 'da', 'del', 'della', 'van', 'von', 'la', 'le', 'el', 'dos', 'das'}
    parts = full_name.split()

    if len(parts) == 1:
        return parts[0]

    if len(parts) >= 2:
        potential_particle = parts[-2].lower()
        if potential_particle in particles:
            return ' '.join(parts[-2:])

    return parts[-1]


def _normalize_manager_name(name: str) -> str:
    if not name or not isinstance(name, str):
        return ""
    name = unicodedata.normalize('NFKD', name)
    name = ''.join(c for c in name if not unicodedata.combining(c))
    name = name.replace('.', ' ')
    name = re.sub(r'\s+', ' ', name)
    return name.strip().lower()


def _split_manager_names(raw: str) -> set:
    if not raw or not isinstance(raw, str):
        return set()
    parts = re.split(r'[;,/]', raw)
    names = set()
    for part in parts:
        if not part:
            continue
        for sub in re.split(r'\s+&\s+|\s+and\s+', part, flags=re.IGNORECASE):
            sub = sub.strip()
            if not sub:
                continue
            norm = _normalize_manager_name(sub)
            if norm:
                names.add(norm)
    return names


def get_manager_match_ids(matches_df, team_id, manager_name, teams_df):
    """Get all match_ids where the specified manager was coaching the team."""
    if matches_df is None or manager_name is None:
        return set()

    team_name_map = _build_team_name_map(teams_df)
    if not team_name_map:
        return set()

    target_managers = _split_manager_names(manager_name)
    if not target_managers:
        return set()

    match_ids = set()

    for _, row in matches_df.iterrows():
        home_team = row.get('home_team', '')
        away_team = row.get('away_team', '')
        home_key = _normalize_team_name(home_team)
        away_key = _normalize_team_name(away_team)

        home_sb_id = team_name_map.get(home_key)
        away_sb_id = team_name_map.get(away_key)

        if home_sb_id == team_id:
            home_managers = row.get('home_managers', '')
            if pd.notna(home_managers):
                home_set = _split_manager_names(str(home_managers))
                if home_set & target_managers:
                    match_ids.add(row['match_id'])
                    continue
            if pd.notna(home_managers) and manager_name in str(home_managers):
                match_ids.add(row['match_id'])

        if away_sb_id == team_id:
            away_managers = row.get('away_managers', '')
            if pd.notna(away_managers):
                away_set = _split_manager_names(str(away_managers))
                if away_set & target_managers:
                    match_ids.add(row['match_id'])
                    continue
            if pd.notna(away_managers) and manager_name in str(away_managers):
                match_ids.add(row['match_id'])

    return match_ids


def get_top_11_players(players_df, player_minutes_df, team_id, manager_id, formation,
                       matches_df=None, teams_df=None, manager_name=None,
                       formation_coordinates=None, position_mapping=None):
    """Get the top 11 players by minutes played, mapped to formation slots."""
    from config import FORMATION_COORDINATES, POSITION_MAPPING

    if formation_coordinates is None:
        formation_coordinates = FORMATION_COORDINATES
    if position_mapping is None:
        position_mapping = POSITION_MAPPING

    formation_coords = formation_coordinates.get(formation, formation_coordinates.get("4-3-3"))
    if formation_coords is None:
        return {}, {}

    slot_positions = {slot: info['position'] for slot, info in formation_coords.items()}

    if player_minutes_df is not None and 'team_id' in player_minutes_df.columns:
        team_players = player_minutes_df[player_minutes_df['team_id'] == team_id].copy()

        if matches_df is not None and manager_name is not None and 'match_id' in team_players.columns:
            manager_matches = get_manager_match_ids(matches_df, team_id, manager_name, teams_df)
            if manager_matches:
                team_players = team_players[team_players['match_id'].isin(manager_matches)].copy()
    else:
        team_players = players_df[players_df['team_id'] == team_id].copy() if 'team_id' in players_df.columns else players_df.copy()

    if len(team_players) == 0:
        return {}, {}

    players_with_position = team_players[team_players['position'] != 'Unknown'].copy()

    if len(players_with_position) == 0:
        return {}, {}

    player_position_minutes = players_with_position.groupby(['player_id', 'player_name', 'position']).agg({
        'minutes_played': 'sum'
    }).reset_index()
    player_position_minutes = player_position_minutes.rename(columns={'minutes_played': 'minutes_in_position'})

    # Load SofaScore names mapping for better display names
    sofascore_map = get_sofascore_names_map()

    player_position_info = []
    for _, row in player_position_minutes.iterrows():
        player_id = row['player_id']
        statsbomb_name = row['player_name']
        position = row['position']
        minutes = row['minutes_in_position']

        # Use SofaScore name if available, otherwise StatsBomb name
        display_name = get_player_display_name(int(player_id), statsbomb_name, sofascore_map)
        surname = extract_surname(display_name)

        formation_positions = position_mapping.get(position, [])

        player_position_info.append({
            'player_id': player_id,
            'surname': surname,
            'position': position,
            'formation_positions': formation_positions,
            'minutes': minutes
        })

    player_position_info.sort(key=lambda x: x['minutes'], reverse=True)

    player_names = {}
    player_id_to_slot = {}
    assigned_players = set()

    for slot, slot_position in slot_positions.items():
        best_match = None
        best_minutes = -1
        for pp in player_position_info:
            if pp['player_id'] in assigned_players:
                continue
            if slot_position in pp['formation_positions']:
                if pp['minutes'] > best_minutes:
                    best_match = pp
                    best_minutes = pp['minutes']
        if best_match:
            player_names[slot] = best_match['surname']
            player_id_to_slot[best_match['player_id']] = slot
            assigned_players.add(best_match['player_id'])

    for slot in slot_positions.keys():
        if slot not in player_names:
            for pp in player_position_info:
                if pp['player_id'] not in assigned_players:
                    player_names[slot] = pp['surname']
                    player_id_to_slot[pp['player_id']] = slot
                    assigned_players.add(pp['player_id'])
                    break

    return player_names, player_id_to_slot


def get_all_available_players(player_minutes_df, team_id, matches_df=None, teams_df=None, manager_name=None):
    """Get all available players for a team+manager with their positions and total minutes.

    Returns list of dicts with player_id, player_name (SofaScore preferred), surname, position, total_minutes.
    """
    if player_minutes_df is None or 'team_id' not in player_minutes_df.columns:
        return []

    team_players = player_minutes_df[player_minutes_df['team_id'] == team_id].copy()

    if matches_df is not None and manager_name is not None and 'match_id' in team_players.columns:
        manager_matches = get_manager_match_ids(matches_df, team_id, manager_name, teams_df)
        if manager_matches:
            team_players = team_players[team_players['match_id'].isin(manager_matches)].copy()

    if len(team_players) == 0:
        return []

    players_with_position = team_players[team_players['position'] != 'Unknown'].copy()

    if len(players_with_position) == 0:
        return []

    player_agg = players_with_position.groupby(['player_id', 'player_name']).agg({
        'minutes_played': 'sum',
        'position': lambda x: x.mode().iloc[0] if len(x) > 0 else 'Unknown'
    }).reset_index()
    player_agg = player_agg.rename(columns={'minutes_played': 'total_minutes'})
    player_agg = player_agg.sort_values('total_minutes', ascending=False)

    # Load SofaScore names mapping for better display names
    sofascore_map = get_sofascore_names_map()

    result = []
    for _, row in player_agg.iterrows():
        player_id = row['player_id']
        statsbomb_name = row['player_name']

        # Use SofaScore name if available, otherwise StatsBomb name
        display_name = get_player_display_name(int(player_id), statsbomb_name, sofascore_map)
        surname = extract_surname(display_name)

        result.append({
            'player_id': player_id,
            'player_name': display_name,  # SofaScore name if available
            'surname': surname,
            'position': row['position'],
            'total_minutes': int(row['total_minutes'])
        })

    return result


def apply_player_overrides(player_names, player_id_to_slot, overrides, all_players):
    """Apply user overrides to player assignments."""
    if not overrides:
        return player_names, player_id_to_slot

    player_lookup = {p['player_id']: p for p in all_players}

    new_player_names = player_names.copy()
    new_player_id_to_slot = player_id_to_slot.copy()

    for slot, new_player_id in overrides.items():
        if new_player_id not in player_lookup:
            continue

        player_info = player_lookup[new_player_id]

        old_player_id = None
        for pid, s in list(new_player_id_to_slot.items()):
            if s == slot:
                old_player_id = pid
                break

        if old_player_id is not None:
            del new_player_id_to_slot[old_player_id]

        if new_player_id in new_player_id_to_slot:
            old_slot = new_player_id_to_slot[new_player_id]
            del new_player_names[old_slot]
            del new_player_id_to_slot[new_player_id]

        new_player_names[slot] = player_info['surname']
        new_player_id_to_slot[new_player_id] = slot

    return new_player_names, new_player_id_to_slot


def get_rank_class(rank, total):
    """Get CSS class based on rank."""
    if total == 0:
        return "rank-mid"
    pct = (total - rank + 1) / total
    if pct >= 0.7:
        return "rank-top"
    elif pct >= 0.4:
        return "rank-mid"
    else:
        return "rank-low"


def is_strength(rank, total):
    """Check if metric is a strength (top 25%)."""
    if total == 0:
        return False
    return rank <= int(total * TOP_PERCENTILE)


def is_average(rank, total):
    """Check if metric is average (25-75%)."""
    if total == 0:
        return False
    top_threshold = int(total * TOP_PERCENTILE)
    bottom_threshold = int(total * (1 - BOTTOM_PERCENTILE))
    return rank > top_threshold and rank <= bottom_threshold


def is_weakness(rank, total):
    """Check if metric is a weakness (bottom 25%)."""
    if total == 0:
        return False
    return rank > int(total * (1 - BOTTOM_PERCENTILE))


# ===========================================
# TEAM LOGO FUNCTIONS
# ===========================================

# Cache for team logo mapping (team_id -> sofascore_id)
_team_logo_mapping = None


@st.cache_data(ttl=3600, show_spinner="Caricamento dati...")
def get_team_logo_mapping():
    """
    Get mapping from StatsBomb team_id to SofaScore external_id.
    Returns a dict: {team_id: {'sofascore_id': str, 'logo_format': str}}
    """
    global _team_logo_mapping
    if _team_logo_mapping is not None:
        return _team_logo_mapping

    try:
        client = _get_supabase_client()
        response = client.table('team_external_ids').select(
            'team_id, external_id, logo_format'
        ).eq('provider', 'sofascore').execute()

        _team_logo_mapping = {}
        for row in response.data:
            _team_logo_mapping[row['team_id']] = {
                'sofascore_id': row['external_id'],
                'logo_format': row.get('logo_format', 'png')
            }
        return _team_logo_mapping
    except Exception:
        return {}


def get_team_logo_path(team_id: int) -> Path:
    """
    Get the local file path for a team's logo.

    Args:
        team_id: StatsBomb team ID

    Returns:
        Path to the logo file, or None if not found
    """
    mapping = get_team_logo_mapping()
    if team_id not in mapping:
        return None

    sofascore_id = mapping[team_id]['sofascore_id']
    logo_format = mapping[team_id].get('logo_format', 'png')

    # Try different formats in preferred locations (assets first for deploy)
    project_root = Path(__file__).resolve().parents[2]
    base_paths = [
        project_root / "streamlit_app" / "assets" / "logos" / "sofascore",
        get_data_dir().parent / 'raw' / 'sofascore' / 'team_images',
    ]

    for base_path in base_paths:
        for ext in [logo_format, 'png', 'webp', 'svg']:
            logo_path = base_path / f"{sofascore_id}.{ext}"
            if logo_path.exists():
                return logo_path

    return None


def get_team_logo_base64(team_id: int) -> str:
    """
    Get a team's logo as a base64-encoded data URL for use in HTML.

    Args:
        team_id: StatsBomb team ID

    Returns:
        Base64 data URL string, or None if not found
    """
    import base64

    logo_path = get_team_logo_path(team_id)
    if logo_path is None or not logo_path.exists():
        return None

    # Determine MIME type
    ext = logo_path.suffix.lower()
    mime_types = {
        '.png': 'image/png',
        '.webp': 'image/webp',
        '.svg': 'image/svg+xml',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
    }
    mime_type = mime_types.get(ext, 'image/png')

    # Read and encode
    with open(logo_path, 'rb') as f:
        data = f.read()

    b64 = base64.b64encode(data).decode('utf-8')
    return f"data:{mime_type};base64,{b64}"


def get_team_logo_html(team_id: int, size: int = 80, fallback: str = "⚽") -> str:
    """
    Get HTML img tag for a team's logo.

    Args:
        team_id: StatsBomb team ID
        size: Size in pixels (width and height)
        fallback: Fallback text/emoji if logo not found

    Returns:
        HTML string with img tag or fallback
    """
    logo_b64 = get_team_logo_base64(team_id)
    if logo_b64:
        return f'<img src="{logo_b64}" style="width: {size}px; height: {size}px; object-fit: contain;" alt="Team Logo">'
    return f'<span style="font-size: {size}px;">{fallback}</span>'


# ===========================================
# SOFASCORE PLAYER DATA (FACES + RATINGS)
# ===========================================

# Fallback StatsBomb team_id -> SofaScore team_id mapping (when Supabase is unavailable)
_SOFASCORE_TEAM_ID_FALLBACK = {
    228: 2686,   # Atalanta
    240: 2685,   # Bologna
    1683: 43685, # Carpi
    231: 2694,   # Chievo
    290: 2705,   # Empoli
    239: 2693,   # Fiorentina
    291: 2801,   # Frosinone
    233: 2713,   # Genoa
    226: 2701,   # Hellas Verona
    238: 2697,   # Inter
    224: 2687,   # Juventus
    236: 2699,   # Lazio
    243: 2692,   # Milan
    227: 2714,   # Napoli
    2256: 2715,  # Palermo
    229: 2702,   # Roma
    234: 2711,   # Sampdoria
    232: 2793,   # Sassuolo
    241: 2696,   # Torino
    230: 2695,   # Udinese
}

# Track attempted downloads to avoid repeated subprocess calls
_PLAYER_IMAGE_DOWNLOAD_ATTEMPTED = set()


def _get_player_images_dirs():
    """Return ordered list of directories to search for player images."""
    dirs = []
    env_dir = os.getenv("PLAYER_IMAGES_DIR", "").strip()
    if env_dir:
        dirs.append(Path(env_dir).expanduser())

    project_root = Path(__file__).resolve().parents[2]
    assets_dir = project_root / "streamlit_app" / "assets" / "player_images"
    dirs.append(assets_dir)

    raw_dir = get_data_dir().parent / 'raw' / 'sofascore' / 'player_images'
    dirs.append(raw_dir)

    # Remove duplicates while preserving order
    unique_dirs = []
    seen = set()
    for d in dirs:
        key = str(d.resolve())
        if key in seen:
            continue
        seen.add(key)
        unique_dirs.append(d)
    return unique_dirs


def get_sofascore_team_id(team_id: int) -> int:
    """Get SofaScore team ID for a StatsBomb team ID (Supabase mapping or fallback)."""
    mapping = get_team_logo_mapping()
    if mapping and team_id in mapping:
        try:
            return int(mapping[team_id]['sofascore_id'])
        except Exception:
            pass
    return _SOFASCORE_TEAM_ID_FALLBACK.get(team_id)


@st.cache_data(ttl=3600, show_spinner="Caricamento dati...")
def load_manual_player_mapping() -> pd.DataFrame:
    """Load manual mapping between SofaScore and StatsBomb player IDs."""
    data_dir = get_data_dir().parent
    mapping_path = data_dir / 'manual_player_mapping.csv'
    if not mapping_path.exists():
        return pd.DataFrame()
    return pd.read_csv(mapping_path)


@st.cache_data(ttl=3600, show_spinner="Caricamento dati...")
def get_sofascore_player_id_map() -> dict:
    """
    Return dict mapping StatsBomb player_id -> SofaScore player_id.

    Priority order:
    1. player_external_ids table from Supabase (generated by setup_player_mapping.py)
    2. manual_player_mapping.csv (manual overrides)
    3. Automatic name matching (fallback)
    """
    # 1. First try player_external_ids from Supabase (highest priority, most reliable)
    external_ids_df = load_player_external_ids()
    supabase_map = {}
    if not external_ids_df.empty:
        sofascore_df = external_ids_df[external_ids_df['provider'] == 'sofascore'].copy()
        if not sofascore_df.empty:
            for _, row in sofascore_df.iterrows():
                player_id = row.get('player_id')
                external_id = row.get('external_id')
                if player_id is not None and external_id is not None:
                    try:
                        supabase_map[int(player_id)] = int(external_id)
                    except (ValueError, TypeError):
                        continue

    # 2. Manual mapping from CSV (second priority, for overrides)
    manual_df = load_manual_player_mapping()
    manual_map = {}
    if manual_df is not None and not manual_df.empty:
        manual_df = manual_df.dropna(subset=['statsbomb_player_id', 'sofascore_player_id']).copy()
        try:
            manual_df['statsbomb_player_id'] = manual_df['statsbomb_player_id'].astype(int)
            manual_df['sofascore_player_id'] = manual_df['sofascore_player_id'].astype(int)
        except Exception:
            pass
        manual_map = dict(zip(manual_df['statsbomb_player_id'], manual_df['sofascore_player_id']))

    # Combine: Supabase first, then manual overrides
    combined_map = {**supabase_map, **manual_map}

    # If we have enough mappings, return early (skip expensive automatic matching)
    if len(combined_map) > 100:
        return combined_map

    # 3. Fallback: Load StatsBomb players for automatic matching
    players_df = None

    if DATA_SOURCE == "supabase":
        try:
            client = _get_supabase_client()
            players_data = _fetch_all_rows(client, 'players', 'player_id, player_name, team_id')
            if players_data:
                players_df = pd.DataFrame(players_data)
        except Exception:
            pass

    # CSV fallback for local development
    if players_df is None or players_df.empty:
        data_dir = get_data_dir()
        players_path = data_dir / 'players.csv'
        if players_path.exists():
            players_df = pd.read_csv(players_path)

    if players_df is None or players_df.empty:
        return combined_map

    players_df['name_norm'] = players_df['player_name'].apply(_normalize_player_name)
    players_df['surname_norm'] = players_df['player_name'].apply(_player_surname)

    # Load SofaScore players from ratings
    ratings_df = load_sofascore_player_ratings()
    if ratings_df is None or ratings_df.empty:
        return combined_map

    required_cols = {'player_id', 'team_id', 'player_name'}
    if not required_cols.issubset(set(ratings_df.columns)):
        return combined_map

    sofa_players = ratings_df[['player_id', 'team_id', 'player_name']].dropna().drop_duplicates()
    if sofa_players.empty:
        return manual_map

    inv_team_map = get_sofascore_to_statsbomb_team_id_map()
    sofa_players['sb_team_id'] = sofa_players['team_id'].map(inv_team_map)
    sofa_players = sofa_players.dropna(subset=['sb_team_id']).copy()

    sofa_players['sb_team_id'] = sofa_players['sb_team_id'].astype(int)
    sofa_players['name_norm'] = sofa_players['player_name'].apply(_normalize_player_name)
    sofa_players['surname_norm'] = sofa_players['player_name'].apply(_player_surname)

    # Build lookup tables
    from collections import defaultdict

    full_lookup = defaultdict(set)
    surname_lookup = defaultdict(set)

    for _, row in sofa_players.iterrows():
        key_full = (int(row['sb_team_id']), row['name_norm'])
        if row['name_norm']:
            full_lookup[key_full].add(int(row['player_id']))

        key_surname = (int(row['sb_team_id']), row['surname_norm'])
        if row['surname_norm']:
            surname_lookup[key_surname].add(int(row['player_id']))

    # Build final mapping (start with combined Supabase + manual mappings)
    mapping = dict(combined_map)

    for _, row in players_df.iterrows():
        sb_id = row.get('player_id')
        if pd.isna(sb_id):
            continue
        try:
            sb_id = int(sb_id)
        except Exception:
            continue
        if sb_id in mapping:
            continue

        team_id = row.get('team_id')
        if pd.isna(team_id):
            continue
        try:
            team_id = int(team_id)
        except Exception:
            continue

        name_norm = row.get('name_norm', '')
        surname_norm = row.get('surname_norm', '')

        # 1) Full name match (unique)
        if name_norm:
            ids = full_lookup.get((team_id, name_norm))
            if ids and len(ids) == 1:
                mapping[sb_id] = next(iter(ids))
                continue

        # 2) Surname match (unique) - fallback only if unique
        if surname_norm:
            ids = surname_lookup.get((team_id, surname_norm))
            if ids and len(ids) == 1:
                mapping[sb_id] = next(iter(ids))
                continue

    return mapping


@st.cache_data(ttl=3600, show_spinner="Caricamento dati...")
def get_sofascore_to_statsbomb_team_id_map() -> dict:
    """Return dict mapping SofaScore team_id -> StatsBomb team_id."""
    mapping = get_team_logo_mapping()
    if mapping:
        inv = {}
        for sb_id, row in mapping.items():
            try:
                inv[int(row['sofascore_id'])] = int(sb_id)
            except Exception:
                continue
        if inv:
            return inv
    return {v: k for k, v in _SOFASCORE_TEAM_ID_FALLBACK.items()}


@st.cache_data(ttl=3600, show_spinner="Caricamento dati...")
def load_sofascore_events() -> pd.DataFrame:
    """
    Load SofaScore events (matches) with event_id and start_time_utc.

    On Streamlit Cloud (DATA_SOURCE='supabase'), fetches from sofascore_events table.
    For local development, falls back to CSV file.
    """
    # Try Supabase first if configured
    if DATA_SOURCE == "supabase":
        try:
            client = _get_supabase_client()
            all_data = _fetch_all_rows(client, 'sofascore_events')
            if all_data:
                df = pd.DataFrame(all_data)
                if 'start_time_utc' in df.columns:
                    df['match_date'] = pd.to_datetime(df['start_time_utc'], errors='coerce').dt.date
                return df
        except Exception as e:
            # Log error but continue to CSV fallback for local dev
            import logging
            logging.warning(f"Failed to load sofascore_events from Supabase: {e}")

    # Fallback to CSV (local development)
    data_dir = get_data_dir().parent
    events_path = data_dir / 'raw' / 'sofascore' / 'events.csv'
    if not events_path.exists():
        return pd.DataFrame()

    df = pd.read_csv(events_path)
    if 'start_time_utc' in df.columns:
        df['match_date'] = pd.to_datetime(df['start_time_utc'], errors='coerce').dt.date
    return df


@st.cache_data(ttl=3600, show_spinner="Caricamento dati...")
def load_sofascore_player_ratings() -> pd.DataFrame:
    """
    Load SofaScore player ratings per match from Supabase.

    Raises an exception if Supabase fails (no fallback to CSV).
    """
    client = _get_supabase_client()
    # Fetch all data with pagination
    all_data = _fetch_all_rows(client, 'sofascore_player_ratings')
    if not all_data:
        return pd.DataFrame()

    df = pd.DataFrame(all_data)
    # Rename columns to match expected format (sofascore_team_id -> team_id, etc.)
    column_mapping = {
        'sofascore_team_id': 'team_id',
        'sofascore_player_id': 'player_id',
    }
    df = df.rename(columns=column_mapping)
    return df


@st.cache_data(ttl=3600, show_spinner="Caricamento eventi giocatore...")
def load_player_events_for_player(player_id: int) -> pd.DataFrame:
    """
    Load player events for a specific player (passes, carries, duels).

    Filters server-side for efficiency - only loads events for the specified player.

    Args:
        player_id: StatsBomb player ID

    Returns:
        DataFrame with columns: player_id, match_id, team_id, event_type,
        start_x, start_y, end_x, end_y, outcome, subtype
    """
    # Try Supabase first if configured
    if DATA_SOURCE == "supabase":
        try:
            client = _get_supabase_client()
            # Filter server-side for this player only
            response = client.table('player_events').select('*').eq('player_id', player_id).execute()
            if response.data:
                return pd.DataFrame(response.data)
            return pd.DataFrame()
        except Exception as e:
            import logging
            logging.warning(f"Failed to load player_events from Supabase: {e}")

    # Fallback to CSV (local development)
    data_dir = get_data_dir()
    events_path = data_dir / 'player_events.csv'
    if not events_path.exists():
        return pd.DataFrame()

    df = pd.read_csv(events_path)
    return df[df['player_id'] == player_id]


def load_player_events() -> pd.DataFrame:
    """
    Load ALL player events - USE WITH CAUTION, very slow!
    Prefer load_player_events_for_player() for single player queries.
    """
    # Fallback to CSV only for local development
    data_dir = get_data_dir()
    events_path = data_dir / 'player_events.csv'
    if not events_path.exists():
        return pd.DataFrame()
    return pd.read_csv(events_path)


@st.cache_data(ttl=3600, show_spinner="Caricamento partite...")
def load_matches_for_events() -> pd.DataFrame:
    """
    Load match metadata for filtering player events by date/round.

    Returns:
        DataFrame with columns: match_id, match_date, match_week
    """
    # Try Supabase first if configured
    if DATA_SOURCE == "supabase":
        try:
            client = _get_supabase_client()
            all_data = _fetch_all_rows(client, 'matches', 'match_id, match_date, match_week')
            if all_data:
                df = pd.DataFrame(all_data)
                if 'match_date' in df.columns:
                    df['match_date'] = pd.to_datetime(df['match_date'], errors='coerce')
                return df
        except Exception as e:
            import logging
            logging.warning(f"Failed to load matches from Supabase: {e}")

    # Fallback to CSV (local development)
    data_dir = get_data_dir().parent
    matches_path = data_dir / 'raw' / 'matches' / 'all_matches.csv'
    if not matches_path.exists():
        return pd.DataFrame()

    df = pd.read_csv(matches_path)
    if 'match_date' in df.columns:
        df['match_date'] = pd.to_datetime(df['match_date'], errors='coerce')
    cols = ['match_id', 'match_date']
    if 'match_week' in df.columns:
        cols.append('match_week')
    return df[cols] if 'match_id' in df.columns else pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def _get_local_player_image_path(player_id_int: int) -> Path:
    for local_dir in _get_player_images_dirs():
        for ext in ['png', 'jpg', 'jpeg', 'webp', 'img']:
            local_path = local_dir / f"{player_id_int}.{ext}"
            if local_path.exists():
                return local_path
    return None


def _download_player_images_with_script(player_ids) -> None:
    """Download player images using scraping/download_player_images.py.

    NOTE: This is disabled on Streamlit Cloud (DATA_SOURCE=supabase)
    because the environment is read-only and subprocess is not supported.
    All required images should be pre-included in streamlit_app/assets/player_images/
    """
    # Disable on Streamlit Cloud - environment is read-only
    if DATA_SOURCE == "supabase":
        return

    if not player_ids:
        return

    # Avoid repeated attempts for same IDs
    ids_to_download = []
    for pid in player_ids:
        try:
            pid_int = int(pid)
        except Exception:
            continue
        if pid_int in _PLAYER_IMAGE_DOWNLOAD_ATTEMPTED:
            continue
        _PLAYER_IMAGE_DOWNLOAD_ATTEMPTED.add(pid_int)
        ids_to_download.append(pid_int)

    if not ids_to_download:
        return

    project_root = Path(__file__).resolve().parents[2]
    script_path = project_root / "scraping" / "download_player_images.py"
    if not script_path.exists():
        return

    images_dir = _get_player_images_dirs()[0]
    try:
        images_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        # Read-only filesystem
        return

    cmd = [
        sys.executable,
        str(script_path),
        "--player-ids",
        ",".join(str(pid) for pid in ids_to_download),
        "--images-dir",
        str(images_dir),
    ]
    try:
        subprocess.run(
            cmd,
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except Exception:
        return


@st.cache_data(ttl=3600, show_spinner=False)
def _load_player_face_from_disk(path_str: str, mtime: float):
    """Load player face image from disk and return as numpy array."""
    from PIL import Image
    import numpy as np
    img = Image.open(path_str).convert("RGBA")
    return np.array(img)


def get_player_face_image(sofascore_player_id: int):
    """
    Return a player's face image as a numpy array (RGBA), or None if not available.
    Tries local cache first, otherwise downloads via download_player_images.py.
    """
    if sofascore_player_id is None:
        return None

    try:
        player_id_int = int(sofascore_player_id)
    except Exception:
        return None

    local_path = _get_local_player_image_path(player_id_int)
    if local_path is None:
        _download_player_images_with_script([player_id_int])
        local_path = _get_local_player_image_path(player_id_int)

    if local_path is None:
        return None

    try:
        mtime = local_path.stat().st_mtime
    except Exception:
        mtime = 0
    return _load_player_face_from_disk(str(local_path), mtime)


def get_player_faces_by_slot(player_id_to_slot: dict) -> dict:
    """
    Build a dict slot -> face image (numpy array) for players in formation.
    """
    faces = {}
    if not player_id_to_slot:
        return faces

    sb_to_sofa = get_sofascore_player_id_map()
    sofa_ids_needed = []
    slot_by_sofa_id = {}
    for sb_player_id, slot in player_id_to_slot.items():
        sofa_id = sb_to_sofa.get(sb_player_id)
        if not sofa_id:
            continue
        sofa_ids_needed.append(sofa_id)
        slot_by_sofa_id[int(sofa_id)] = slot

    # Download missing images in batch via script (if needed)
    missing_ids = []
    for sofa_id in sofa_ids_needed:
        try:
            pid_int = int(sofa_id)
        except Exception:
            continue
        if _get_local_player_image_path(pid_int) is None:
            missing_ids.append(pid_int)

    if missing_ids:
        _download_player_images_with_script(missing_ids)

    # Load images from disk
    for sofa_id in sofa_ids_needed:
        img = get_player_face_image(sofa_id)
        if img is not None:
            slot = slot_by_sofa_id.get(int(sofa_id))
            if slot is not None:
                faces[slot] = img
    return faces


def _normalize_team_name(name: str) -> str:
    if not name or not isinstance(name, str):
        return ""
    return re.sub(r'[^a-z0-9]', '', name.lower())


def _build_team_name_map(teams_df: pd.DataFrame) -> dict:
    """Build normalized team name -> team_id map with common aliases."""
    team_name_map = {}
    if teams_df is None or 'team_id' not in teams_df.columns:
        return team_name_map

    for _, row in teams_df.iterrows():
        name = row.get('team_name', '')
        key = _normalize_team_name(name)
        if key:
            team_name_map[key] = int(row['team_id'])

    # Common aliases in matches.csv
    aliases = {
        'acmilan': 'milan',
        'asroma': 'roma',
        'intermilan': 'inter',
    }
    for alias_key, canonical_key in aliases.items():
        if alias_key in team_name_map:
            continue
        if canonical_key in team_name_map:
            team_name_map[alias_key] = team_name_map[canonical_key]

    return team_name_map


def _normalize_player_name(name: str) -> str:
    if not name or not isinstance(name, str):
        return ""
    name = unicodedata.normalize('NFKD', name)
    name = ''.join(c for c in name if not unicodedata.combining(c))
    name = name.lower()
    return re.sub(r'[^a-z0-9]', '', name)


def _player_surname(name: str) -> str:
    if not name or not isinstance(name, str):
        return ""
    parts = name.strip().split()
    if not parts:
        return ""
    return _normalize_player_name(parts[-1])


def get_sofascore_event_ids_for_manager(
    team_id: int,
    manager_name: str,
    matches_df: pd.DataFrame,
    teams_df: pd.DataFrame
) -> set:
    """
    Map StatsBomb matches for a team+manager to SofaScore event_ids.
    Uses date + home/away team IDs matching.
    """
    if matches_df is None or teams_df is None or manager_name is None:
        return set()

    team_name_map = _build_team_name_map(teams_df)
    if not team_name_map:
        return set()

    events_df = load_sofascore_events()
    if events_df is None or events_df.empty:
        return set()

    # Build lookup: (date, home_id, away_id) -> event_id
    event_lookup = {}
    for _, row in events_df.iterrows():
        try:
            home_id = int(row['home_team_id'])
            away_id = int(row['away_team_id'])
            match_date = row.get('match_date')
            if pd.isna(match_date):
                continue
            key = (match_date, home_id, away_id)
            event_lookup[key] = int(row['event_id'])
        except Exception:
            continue

    event_ids = set()

    target_managers = _split_manager_names(manager_name)
    if not target_managers:
        return set()

    for _, row in matches_df.iterrows():
        match_date = row.get('match_date')
        if pd.isna(match_date):
            continue
        try:
            match_date = pd.to_datetime(match_date, errors='coerce').date()
        except Exception:
            continue

        home_team = row.get('home_team', '')
        away_team = row.get('away_team', '')
        home_key = _normalize_team_name(home_team)
        away_key = _normalize_team_name(away_team)

        # Manager-specific filtering (robust normalization)
        home_managers = row.get('home_managers', '')
        away_managers = row.get('away_managers', '')

        home_set = _split_manager_names(str(home_managers))
        away_set = _split_manager_names(str(away_managers))

        home_sb_id = team_name_map.get(home_key)
        away_sb_id = team_name_map.get(away_key)

        if home_sb_id == team_id and (home_set & target_managers):
            home_sb_id = team_id
            home_sofa = get_sofascore_team_id(home_sb_id)
            away_sofa = get_sofascore_team_id(away_sb_id) if away_sb_id else None
            if home_sofa and away_sofa:
                event_id = event_lookup.get((match_date, home_sofa, away_sofa))
                if event_id:
                    event_ids.add(event_id)

        if away_sb_id == team_id and (away_set & target_managers):
            home_sofa = get_sofascore_team_id(home_sb_id) if home_sb_id else None
            away_sofa = get_sofascore_team_id(away_sb_id)
            if home_sofa and away_sofa:
                event_id = event_lookup.get((match_date, home_sofa, away_sofa))
                if event_id:
                    event_ids.add(event_id)

    return event_ids


def get_sofascore_player_ratings_for_team_manager(
    team_id: int,
    manager_name: str,
    matches_df: pd.DataFrame,
    teams_df: pd.DataFrame
) -> dict:
    """
    Return dict mapping StatsBomb player_id -> average SofaScore rating
    for matches coached by the given manager.
    """
    event_ids = get_sofascore_event_ids_for_manager(team_id, manager_name, matches_df, teams_df)
    if not event_ids:
        return {}

    ratings_df = load_sofascore_player_ratings()
    if ratings_df is None or ratings_df.empty:
        return {}

    team_sofa_id = get_sofascore_team_id(team_id)
    if team_sofa_id:
        ratings_df = ratings_df[ratings_df['team_id'] == team_sofa_id]

    ratings_df = ratings_df[ratings_df['event_id'].isin(event_ids)]
    if ratings_df.empty:
        return {}

    try:
        avg_by_player = ratings_df.groupby('player_id')['rating'].mean().to_dict()
    except Exception:
        return {}

    sb_to_sofa = get_sofascore_player_id_map()
    sb_ratings = {}
    for sb_player_id, sofa_player_id in sb_to_sofa.items():
        rating = avg_by_player.get(sofa_player_id)
        if rating is not None:
            try:
                sb_ratings[sb_player_id] = float(rating)
            except Exception:
                continue

    return sb_ratings


def get_player_ratings_by_slot(
    team_id: int,
    manager_name: str,
    matches_df: pd.DataFrame,
    teams_df: pd.DataFrame,
    player_id_to_slot: dict
) -> dict:
    """
    Build a dict slot -> average SofaScore rating for players in formation.
    """
    if not player_id_to_slot:
        return {}

    sb_ratings = get_sofascore_player_ratings_for_team_manager(
        team_id, manager_name, matches_df, teams_df
    )
    if not sb_ratings:
        return {}

    slot_ratings = {}
    for sb_player_id, slot in player_id_to_slot.items():
        rating = sb_ratings.get(sb_player_id)
        if rating is not None:
            slot_ratings[slot] = rating
    return slot_ratings


# =============================================================================
# PLAYER PROFILE FUNCTIONS
# =============================================================================

@st.cache_data(ttl=3600, show_spinner="Caricamento dati...")
def load_player_external_ids() -> pd.DataFrame:
    """
    Load player_external_ids table from Supabase.
    Maps StatsBomb player_id to SofaScore external_id.
    """
    client = _get_supabase_client()
    data = _fetch_all_rows(client, 'player_external_ids')
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


@st.cache_data(ttl=3600)
def get_sofascore_names_map() -> Dict[int, str]:
    """
    Get a mapping from StatsBomb player_id to SofaScore player name.

    Returns:
        Dict mapping StatsBomb player_id (int) to SofaScore player name (str).
        Only includes entries with external_name available.

    The SofaScore names are typically more user-friendly (e.g., "Maicon" instead of
    "Marcos Rogerio Rizzo Lopes") and handle nicknames for Brazilian players, etc.
    """
    df = load_player_external_ids()
    if df.empty:
        return {}

    # Filter for sofascore provider and entries with external_name
    sofascore_df = df[
        (df['provider'] == 'sofascore') &
        (df['external_name'].notna()) &
        (df['external_name'] != '')
    ]

    if sofascore_df.empty:
        return {}

    # Create mapping: StatsBomb player_id -> SofaScore name
    name_map = {}
    for _, row in sofascore_df.iterrows():
        player_id = row.get('player_id')
        external_name = row.get('external_name')
        if player_id is not None and external_name:
            try:
                name_map[int(player_id)] = str(external_name)
            except (ValueError, TypeError):
                continue

    return name_map


def get_player_display_name(player_id: int, statsbomb_name: str, sofascore_map: Optional[Dict[int, str]] = None) -> str:
    """
    Get the best display name for a player, preferring SofaScore names.

    Args:
        player_id: StatsBomb player ID
        statsbomb_name: Original StatsBomb player name (full name)
        sofascore_map: Optional pre-loaded mapping. If None, loads fresh.

    Returns:
        SofaScore name if available, otherwise StatsBomb name.
    """
    if sofascore_map is None:
        sofascore_map = get_sofascore_names_map()

    sofascore_name = sofascore_map.get(player_id)
    if sofascore_name:
        return sofascore_name

    return statsbomb_name


def get_player_data_for_team(sofascore_player_id: int, sofascore_team_id: int) -> pd.DataFrame:
    """
    Get all SofaScore data for a specific player with a specific team.
    Returns DataFrame filtered by player_id and team_id.
    """
    df = load_sofascore_player_ratings()
    if df is None or df.empty:
        return pd.DataFrame()
    return df[(df['player_id'] == sofascore_player_id) & (df['team_id'] == sofascore_team_id)]


def calculate_usage_score(df_player: pd.DataFrame, df_all: pd.DataFrame) -> dict:
    """
    Calculate comprehensive usage score (0-100) for evaluating loan player utilization.

    The score is a weighted composite of multiple factors that together indicate
    whether a player is being properly utilized by their team. This is designed
    specifically for evaluating loan players.

    Algorithm:
    - Minutes Rate (40%): minutes_played / minutes_possible
    - Match Participation (25%): matches_played / matches_available
    - Starter Quality (20%): weighted combination of starter rate and avg minutes when starting
    - Consistency (15%): regularity of playing time (penalizes sporadic usage)

    Returns dict with:
        - score: float (0-100) - Overall utilization score
        - minutes_played: int - Total minutes played
        - minutes_possible: int - Maximum possible minutes
        - matches_played: int - Number of matches with any minutes
        - matches_available: int - Number of matches available to play
        - starts: int - Number of times started
        - avg_minutes_per_match: float - Average minutes when playing
        - minutes_rate: float - Minutes usage percentage
        - match_rate: float - Match participation percentage
        - starter_rate: float - Percentage of appearances as starter
        - consistency_score: float - Regularity of playing time (0-100)
        - component_scores: dict - Breakdown of weighted components
    """
    # Default empty result
    empty_result = {
        'score': 0, 'minutes_played': 0, 'minutes_possible': 0,
        'matches_played': 0, 'matches_available': 0, 'starts': 0,
        'avg_minutes_per_match': 0, 'minutes_rate': 0, 'match_rate': 0,
        'starter_rate': 0, 'consistency_score': 0,
        'component_scores': {'minutes': 0, 'participation': 0, 'starter': 0, 'consistency': 0}
    }

    if df_player.empty:
        return empty_result

    # === BASIC METRICS ===

    # Round of first appearance for this player+team
    round_first = df_player['round'].min()

    # Current round (max round in all data)
    round_current = df_all['round'].max() if not df_all.empty else 38

    # Matches available since first appearance
    matches_available = round_current - round_first + 1

    # Maximum possible minutes
    minutes_possible = matches_available * 90

    # Actual minutes played
    minutes_played = int(df_player['minutes_played'].sum())

    # Matches with any playing time
    matches_played = int(df_player[df_player['minutes_played'] > 0].shape[0])

    # Starts (if column exists)
    if 'is_starter' in df_player.columns:
        starts = int(df_player[df_player['is_starter'] == True].shape[0])
    else:
        # Estimate: if played >= 60 minutes, likely started
        starts = int(df_player[df_player['minutes_played'] >= 60].shape[0])

    # Average minutes per match when playing
    avg_minutes_per_match = (minutes_played / matches_played) if matches_played > 0 else 0

    # === COMPONENT CALCULATIONS ===

    # 1. MINUTES RATE (40% weight)
    # Core metric: what percentage of possible minutes did they play?
    minutes_rate = (minutes_played / minutes_possible * 100) if minutes_possible > 0 else 0
    minutes_component = min(100, minutes_rate)  # Already 0-100

    # 2. MATCH PARTICIPATION RATE (25% weight)
    # In what percentage of available matches did they play at all?
    # This captures consistency of selection (are they in the squad?)
    match_rate = (matches_played / matches_available * 100) if matches_available > 0 else 0
    participation_component = min(100, match_rate)  # Already 0-100

    # 3. STARTER QUALITY (20% weight)
    # Combines two factors:
    # - Starter rate: What % of their appearances are starts?
    # - Quality minutes: When they start, do they play full matches?
    if matches_played > 0:
        starter_rate = (starts / matches_played * 100)

        # Average minutes when starting (quality of starts)
        if starts > 0 and 'is_starter' in df_player.columns:
            starter_minutes = df_player[df_player['is_starter'] == True]['minutes_played'].mean()
        else:
            starter_minutes = avg_minutes_per_match

        # Normalize starter minutes (90 = perfect, 45 = half credit)
        starter_minutes_factor = min(100, (starter_minutes / 90) * 100)

        # Weighted combination: 60% starter rate, 40% quality of starts
        starter_component = (0.6 * starter_rate) + (0.4 * starter_minutes_factor)
    else:
        starter_rate = 0
        starter_component = 0

    # 4. CONSISTENCY (15% weight)
    # Measures regularity of playing time. A player who plays every week
    # is more valuable than one who plays sporadically.
    # Uses coefficient of variation: lower is better (more consistent)
    if matches_played >= 3:
        # Get minutes per round for rounds where player could have played
        rounds_available = list(range(round_first, round_current + 1))
        minutes_by_round = []

        for r in rounds_available:
            round_data = df_player[df_player['round'] == r]
            if not round_data.empty:
                minutes_by_round.append(round_data['minutes_played'].iloc[0])
            else:
                minutes_by_round.append(0)  # Didn't play this round

        # Calculate coefficient of variation (std / mean)
        import numpy as np
        mean_minutes = np.mean(minutes_by_round)
        std_minutes = np.std(minutes_by_round)

        if mean_minutes > 0:
            cv = std_minutes / mean_minutes
            # Lower CV = more consistent. CV of 0 = perfect, CV > 1.5 = very inconsistent
            # Transform to 0-100 scale where 100 = perfectly consistent
            consistency_score = max(0, min(100, (1 - cv / 1.5) * 100))
        else:
            consistency_score = 0
    else:
        # Not enough data for consistency calculation
        consistency_score = 50  # Neutral

    consistency_component = consistency_score

    # === WEIGHTED COMPOSITE SCORE ===
    # Weights chosen based on importance for loan player evaluation:
    # - Minutes (40%): Most important - are they actually playing?
    # - Participation (25%): Are they consistently in the squad?
    # - Starter Quality (20%): Are they trusted to start?
    # - Consistency (15%): Is usage regular or sporadic?

    WEIGHT_MINUTES = 0.40
    WEIGHT_PARTICIPATION = 0.25
    WEIGHT_STARTER = 0.20
    WEIGHT_CONSISTENCY = 0.15

    score = (
        WEIGHT_MINUTES * minutes_component +
        WEIGHT_PARTICIPATION * participation_component +
        WEIGHT_STARTER * starter_component +
        WEIGHT_CONSISTENCY * consistency_component
    )

    # Clamp to 0-100
    score = max(0, min(100, score))

    return {
        'score': round(score, 1),
        'minutes_played': minutes_played,
        'minutes_possible': minutes_possible,
        'matches_played': matches_played,
        'matches_available': matches_available,
        'starts': starts,
        'avg_minutes_per_match': round(avg_minutes_per_match, 1),
        'minutes_rate': round(minutes_rate, 1),
        'match_rate': round(match_rate, 1),
        'starter_rate': round(starter_rate, 1) if matches_played > 0 else 0,
        'consistency_score': round(consistency_score, 1),
        'component_scores': {
            'minutes': round(minutes_component * WEIGHT_MINUTES, 1),
            'participation': round(participation_component * WEIGHT_PARTICIPATION, 1),
            'starter': round(starter_component * WEIGHT_STARTER, 1),
            'consistency': round(consistency_component * WEIGHT_CONSISTENCY, 1)
        }
    }


def get_player_season_data(sofascore_player_id: int, sofascore_team_id: int) -> list:
    """
    Prepare data for the 38-round season chart.

    Returns list of 38 dicts, one per round:
        - round: int (1-38)
        - played: bool
        - rating: float or None
        - minutes: int
        - goals: int
        - assists: int
        - yellow_cards: int
        - red_cards: int
    """
    df = get_player_data_for_team(sofascore_player_id, sofascore_team_id)

    result = []
    for round_num in range(1, 39):
        match_data = df[df['round'] == round_num] if not df.empty else pd.DataFrame()

        if match_data.empty or match_data['minutes_played'].sum() == 0:
            # Did not play this round
            result.append({
                'round': round_num,
                'played': False,
                'rating': None,
                'minutes': 0,
                'goals': 0,
                'assists': 0,
                'yellow_cards': 0,
                'red_cards': 0
            })
        else:
            row = match_data.iloc[0]
            result.append({
                'round': round_num,
                'played': True,
                'rating': float(row['rating']) if pd.notna(row.get('rating')) else None,
                'minutes': int(row.get('minutes_played', 0) or 0),
                'goals': int(row.get('goals', 0) or 0),
                'assists': int(row.get('assists', 0) or 0),
                'yellow_cards': int(row.get('yellow_cards', 0) or 0),
                'red_cards': int(row.get('red_cards', 0) or 0)
            })

    return result


def get_roster_for_team(sofascore_team_id: int) -> pd.DataFrame:
    """
    Get aggregated roster data for a team.

    Returns DataFrame with one row per player containing:
        - player_id: int (SofaScore)
        - player_name: str
        - position: str (G, D, M, F)
        - shirt_number: int
        - matches: int (number of matches played)
        - minutes_total: int
        - avg_rating: float
        - goals: int
        - assists: int
    """
    df = load_sofascore_player_ratings()
    if df is None or df.empty:
        return pd.DataFrame()

    # Filter by team
    team_df = df[df['team_id'] == sofascore_team_id]
    if team_df.empty:
        return pd.DataFrame()

    # Filter players with at least 1 minute played
    team_df = team_df[team_df['minutes_played'] > 0]
    if team_df.empty:
        return pd.DataFrame()

    # Aggregate by player
    roster = team_df.groupby('player_id').agg({
        'player_name': 'first',
        'position': 'first',
        'shirt_number': 'first',
        'minutes_played': 'sum',
        'rating': 'mean',
        'goals': 'sum',
        'assists': 'sum'
    }).reset_index()

    # Count matches
    matches_count = team_df.groupby('player_id').size().reset_index(name='matches')
    roster = roster.merge(matches_count, on='player_id', how='left')

    # Rename columns
    roster = roster.rename(columns={
        'minutes_played': 'minutes_total',
        'rating': 'avg_rating'
    })

    # Fill NaN
    roster['avg_rating'] = roster['avg_rating'].fillna(0)
    roster['goals'] = roster['goals'].fillna(0).astype(int)
    roster['assists'] = roster['assists'].fillna(0).astype(int)
    roster['matches'] = roster['matches'].fillna(0).astype(int)
    roster['shirt_number'] = roster['shirt_number'].fillna(0).astype(int)

    return roster


def get_player_basic_info(sofascore_player_id: int, sofascore_team_id: int) -> dict:
    """
    Get basic info for a player.

    Returns dict with:
        - player_name: str
        - team_name: str
        - position: str
        - shirt_number: int
    """
    df = get_player_data_for_team(sofascore_player_id, sofascore_team_id)
    if df.empty:
        return None

    row = df.iloc[0]
    return {
        'player_name': row.get('player_name', 'Giocatore'),
        'team_name': row.get('team_name', 'Squadra'),
        'position': row.get('position', ''),
        'shirt_number': int(row.get('shirt_number', 0) or 0)
    }


def get_player_summary_stats(df_player: pd.DataFrame) -> dict:
    """
    Calculate summary statistics for a player's season.

    Returns dict with:
        - matches: int
        - minutes_total: int
        - avg_rating: float
        - starter_count: int
        - starter_pct: float
        - goals: int
        - assists: int
        - yellow_cards: int
        - red_cards: int
    """
    if df_player.empty:
        return {
            'matches': 0, 'minutes_total': 0, 'avg_rating': 0,
            'starter_count': 0, 'starter_pct': 0,
            'goals': 0, 'assists': 0, 'yellow_cards': 0, 'red_cards': 0
        }

    played = df_player[df_player['minutes_played'] > 0]
    matches = len(played)
    minutes_total = int(df_player['minutes_played'].sum())

    # Average rating (only where rating is not null)
    ratings = df_player[df_player['rating'].notna()]['rating']
    avg_rating = float(ratings.mean()) if len(ratings) > 0 else 0

    # Starter stats
    starter_count = int(df_player[df_player['is_starter'] == True].shape[0]) if 'is_starter' in df_player.columns else 0
    starter_pct = (starter_count / matches * 100) if matches > 0 else 0

    return {
        'matches': matches,
        'minutes_total': minutes_total,
        'avg_rating': round(avg_rating, 2),
        'starter_count': starter_count,
        'starter_pct': round(starter_pct, 1),
        'goals': int(df_player['goals'].sum()) if 'goals' in df_player.columns else 0,
        'assists': int(df_player['assists'].sum()) if 'assists' in df_player.columns else 0,
        'yellow_cards': int(df_player['yellow_cards'].sum()) if 'yellow_cards' in df_player.columns else 0,
        'red_cards': int(df_player['red_cards'].sum()) if 'red_cards' in df_player.columns else 0
    }
