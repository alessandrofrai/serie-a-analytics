"""
Serie A 2015-2016 Analytics Dashboard - Configuration Settings

This module contains all configuration constants and settings for the application.
Supports both local development (.env) and Streamlit Cloud (st.secrets).
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple

from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()


def get_secret(key: str, default: str = "") -> str:
    """
    Get a secret value from Streamlit secrets or environment variables.

    Priority:
    1. st.secrets (Streamlit Cloud)
    2. os.environ / .env file (local development)
    3. default value

    Args:
        key: The secret key to look up
        default: Default value if not found

    Returns:
        The secret value or default
    """
    # Try Streamlit secrets first (for Streamlit Cloud deployment)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        # Streamlit not available or not initialized yet
        pass

    # Fall back to environment variables (for local dev and scripts)
    return os.getenv(key, default)

# ===========================================
# PATH CONFIGURATION
# ===========================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
ASSETS_DIR = BASE_DIR / "streamlit_app" / "assets"
LOGOS_DIR = ASSETS_DIR / "logos"

# Create directories if they don't exist
for dir_path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, LOGOS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ===========================================
# STATSBOMB CONFIGURATION
# ===========================================
STATSBOMB_COMPETITION_ID = 12  # Serie A (Italy)
STATSBOMB_SEASON_ID = 27  # 2015-2016

# ===========================================
# DATABASE CONFIGURATION
# ===========================================
SUPABASE_URL = get_secret("SUPABASE_URL", "")
SUPABASE_KEY = get_secret("SUPABASE_KEY", "")
SUPABASE_SERVICE_KEY = get_secret("SUPABASE_SERVICE_KEY", "")

# ===========================================
# APPLICATION SETTINGS
# ===========================================
DEBUG = get_secret("DEBUG", "False").lower() == "true"
LOG_LEVEL = get_secret("LOG_LEVEL", "INFO")
DATA_SOURCE = get_secret("DATA_SOURCE", "supabase")

# ===========================================
# AI INSIGHTS CONFIGURATION (OpenRouter)
# ===========================================
OPENROUTER_API_KEY = get_secret("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = get_secret("OPENROUTER_MODEL", "anthropic/claude-3.5-haiku")

# ===========================================
# FIELD DIMENSIONS (StatsBomb uses 120x80)
# ===========================================
FIELD_LENGTH = 120.0
FIELD_WIDTH = 80.0

# Zone boundaries for 18-zone system
ZONE_X_BOUNDARIES = [0, 40, 80, 120]  # Defensive, Middle, Attacking thirds
ZONE_Y_BOUNDARIES = [0, 26.67, 53.33, 80]  # Left, Center, Right

# ===========================================
# 18-ZONE MAPPING
# ===========================================
"""
     ZONA DIFENSIVA          ZONA CENTRALE           ZONA OFFENSIVA
   (Terzo Difensivo)        (Terzo Medio)          (Terzo Offensivo)

   +-----+-----+-----+    +-----+-----+-----+    +-----+-----+-----+
   |  1  |  2  |  3  |    |  7  |  8  |  9  |    | 13  | 14  | 15  |
   +-----+-----+-----+    +-----+-----+-----+    +-----+-----+-----+
   |  4  |  5  |  6  |    | 10  | 11  | 12  |    | 16  | 17  | 18  |
   +-----+-----+-----+    +-----+-----+-----+    +-----+-----+-----+

   Direzione di attacco →→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→
"""

ZONE_BUILDUP = [1, 2, 3, 4, 5, 6]  # Defensive third
ZONE_PROGRESSION = [7, 8, 9, 10, 11, 12]  # Middle third
ZONE_FINISHING = [13, 14, 15, 16, 17, 18]  # Attacking third

# ===========================================
# TOPSIS WEIGHTS
# ===========================================
TOPSIS_VOLUME_WEIGHT = 0.35
TOPSIS_QUALITY_WEIGHT = 0.65

# ===========================================
# METRICS CONFIGURATION
# ===========================================
# Categories for metrics
METRIC_CATEGORIES = [
    "attacking",
    "chance_creation",
    "buildup",
    "transition",
    "possession",
    "defending",
    "pressing",
    "set_pieces",
    "goalkeeping"
]

# Metrics that use TOPSIS calculation (volume + quality)
TOPSIS_METRICS: Dict[str, Dict[str, str]] = {
    # Attacking
    "xg_total": {"volume": "shots_total", "quality": "xg_per_shot"},
    "xg_open_play": {"volume": "shots_open_play", "quality": "xg_per_shot_open"},
    "xg_set_piece": {"volume": "shots_set_piece", "quality": "xg_per_shot_set"},
    "shots_on_target": {"volume": "shots_total", "quality": "shots_on_target_pct"},
    "big_chances": {"volume": "big_chances_total", "quality": "big_chances_conversion"},

    # Chance Creation
    "xa_total": {"volume": "key_passes", "quality": "xa_per_key_pass"},
    "through_balls": {"volume": "through_balls_attempted", "quality": "through_balls_success_pct"},
    "crosses": {"volume": "crosses_attempted", "quality": "crosses_success_pct"},
    "crosses_from_left": {"volume": "crosses_left_attempted", "quality": "crosses_left_success_pct"},
    "crosses_from_right": {"volume": "crosses_right_attempted", "quality": "crosses_right_success_pct"},
    "cutbacks": {"volume": "cutbacks_attempted", "quality": "cutbacks_xa"},

    # Build-up
    "buildup_sequences": {"volume": "buildup_sequence_count", "quality": "buildup_xg_per_sequence"},
    "progressive_passes_z1": {"volume": "prog_passes_z1_attempted", "quality": "prog_passes_z1_success_pct"},
    "progressive_carries_z1": {"volume": "prog_carries_z1_count", "quality": "prog_carries_z1_distance"},
    "passes_into_final_third": {"volume": "passes_final_third_attempted", "quality": "passes_final_third_success_pct"},

    # Transition
    "transition_z2_sequences": {"volume": "transition_z2_count", "quality": "transition_z2_xg"},
    "transition_z3_sequences": {"volume": "transition_z3_count", "quality": "transition_z3_xg"},
    "counter_attacks": {"volume": "counter_attack_count", "quality": "counter_attack_xg"},
    "fast_attacks": {"volume": "fast_attack_count", "quality": "fast_attack_xg"},

    # Possession
    "passes_total": {"volume": "passes_attempted", "quality": "passes_success_pct"},
    "passes_short": {"volume": "passes_short_attempted", "quality": "passes_short_success_pct"},
    "passes_medium": {"volume": "passes_medium_attempted", "quality": "passes_medium_success_pct"},
    "passes_long": {"volume": "passes_long_attempted", "quality": "passes_long_success_pct"},
    "progressive_passes": {"volume": "prog_passes_attempted", "quality": "prog_passes_success_pct"},
    "progressive_carries": {"volume": "prog_carries_count", "quality": "prog_carries_avg_distance"},

    # Defending
    "tackles": {"volume": "tackles_attempted", "quality": "tackles_won_pct"},
    "aerial_duels": {"volume": "aerial_duels_total", "quality": "aerial_duels_won_pct"},
    "ground_duels": {"volume": "ground_duels_total", "quality": "ground_duels_won_pct"},

    # Pressing
    "high_press_recoveries": {"volume": "high_press_count", "quality": "high_press_xg_conversion"},
    "counterpressing_recoveries": {"volume": "counterpress_count", "quality": "counterpress_avg_zone"},
    "pressing_sequences": {"volume": "pressing_sequence_count", "quality": "pressing_avg_duration"},

    # Set Pieces
    "corners_taken": {"volume": "corners_count", "quality": "corners_xg"},
    "free_kicks_taken": {"volume": "free_kicks_count", "quality": "free_kicks_xg"},
    "penalties_taken": {"volume": "penalties_count", "quality": "penalties_conversion_pct"},

    # Goalkeeping
    "saves": {"volume": "shots_faced", "quality": "save_percentage"},
    "distribution_accuracy": {"volume": "gk_passes_attempted", "quality": "gk_passes_success_pct"},
}

# Simple metrics (no TOPSIS, just raw values)
SIMPLE_METRICS: List[str] = [
    "shots_total",
    "goals_scored",
    "key_passes",
    "buildup_xg",
    "transition_z2_xg",
    "transition_z3_xg",
    "possession_percentage",
    "touches_in_box",
    "ball_recoveries",
    "interceptions",
    "clearances",
    "blocks",
    "fouls_committed",
    "yellow_cards",
    "red_cards",
    "ppda",
    "set_piece_xg",
    "xg_against",
    "goals_prevented",
]

# ===========================================
# FORMATION COORDINATES (100x100 grid)
# ===========================================
FORMATION_COORDINATES: Dict[str, Dict[int, Dict[str, any]]] = {
    "4-4-2": {
        1: {"position": "GK", "x": 5, "y": 50},
        2: {"position": "RB", "x": 25, "y": 15},
        3: {"position": "CB", "x": 25, "y": 35},
        4: {"position": "CB", "x": 25, "y": 65},
        5: {"position": "LB", "x": 25, "y": 85},
        6: {"position": "RM", "x": 50, "y": 15},
        7: {"position": "CM", "x": 50, "y": 35},
        8: {"position": "CM", "x": 50, "y": 65},
        9: {"position": "LM", "x": 50, "y": 85},
        10: {"position": "ST", "x": 75, "y": 35},
        11: {"position": "ST", "x": 75, "y": 65}
    },
    "4-3-3": {
        1: {"position": "GK", "x": 5, "y": 50},
        2: {"position": "RB", "x": 25, "y": 15},
        3: {"position": "CB", "x": 25, "y": 35},
        4: {"position": "CB", "x": 25, "y": 65},
        5: {"position": "LB", "x": 25, "y": 85},
        6: {"position": "CDM", "x": 45, "y": 50},
        7: {"position": "CM", "x": 55, "y": 30},
        8: {"position": "CM", "x": 55, "y": 70},
        9: {"position": "RW", "x": 75, "y": 15},
        10: {"position": "ST", "x": 80, "y": 50},
        11: {"position": "LW", "x": 75, "y": 85}
    },
    "4-2-3-1": {
        1: {"position": "GK", "x": 5, "y": 50},
        2: {"position": "RB", "x": 25, "y": 15},
        3: {"position": "CB", "x": 25, "y": 35},
        4: {"position": "CB", "x": 25, "y": 65},
        5: {"position": "LB", "x": 25, "y": 85},
        6: {"position": "CDM", "x": 40, "y": 35},
        7: {"position": "CDM", "x": 40, "y": 65},
        8: {"position": "RAM", "x": 60, "y": 20},
        9: {"position": "CAM", "x": 60, "y": 50},
        10: {"position": "LAM", "x": 60, "y": 80},
        11: {"position": "ST", "x": 80, "y": 50}
    },
    "3-5-2": {
        1: {"position": "GK", "x": 5, "y": 50},
        2: {"position": "CB", "x": 25, "y": 25},
        3: {"position": "CB", "x": 25, "y": 50},
        4: {"position": "CB", "x": 25, "y": 75},
        5: {"position": "RWB", "x": 45, "y": 10},
        6: {"position": "CM", "x": 45, "y": 35},
        7: {"position": "CDM", "x": 40, "y": 50},
        8: {"position": "CM", "x": 45, "y": 65},
        9: {"position": "LWB", "x": 45, "y": 90},
        10: {"position": "ST", "x": 75, "y": 35},
        11: {"position": "ST", "x": 75, "y": 65}
    },
    "3-4-3": {
        1: {"position": "GK", "x": 5, "y": 50},
        2: {"position": "CB", "x": 25, "y": 25},
        3: {"position": "CB", "x": 25, "y": 50},
        4: {"position": "CB", "x": 25, "y": 75},
        5: {"position": "RWB", "x": 45, "y": 10},
        6: {"position": "CM", "x": 45, "y": 35},
        7: {"position": "CM", "x": 45, "y": 65},
        8: {"position": "LWB", "x": 45, "y": 90},
        9: {"position": "RW", "x": 75, "y": 20},
        10: {"position": "ST", "x": 80, "y": 50},
        11: {"position": "LW", "x": 75, "y": 80}
    },
    "4-1-4-1": {
        1: {"position": "GK", "x": 5, "y": 50},
        2: {"position": "RB", "x": 25, "y": 15},
        3: {"position": "CB", "x": 25, "y": 35},
        4: {"position": "CB", "x": 25, "y": 65},
        5: {"position": "LB", "x": 25, "y": 85},
        6: {"position": "CDM", "x": 40, "y": 50},
        7: {"position": "RM", "x": 55, "y": 15},
        8: {"position": "CM", "x": 55, "y": 35},
        9: {"position": "CM", "x": 55, "y": 65},
        10: {"position": "LM", "x": 55, "y": 85},
        11: {"position": "ST", "x": 80, "y": 50}
    },
    "4-3-1-2": {
        1: {"position": "GK", "x": 5, "y": 50},
        2: {"position": "RB", "x": 25, "y": 15},
        3: {"position": "CB", "x": 25, "y": 35},
        4: {"position": "CB", "x": 25, "y": 65},
        5: {"position": "LB", "x": 25, "y": 85},
        6: {"position": "CM", "x": 45, "y": 30},
        7: {"position": "CDM", "x": 40, "y": 50},
        8: {"position": "CM", "x": 45, "y": 70},
        9: {"position": "CAM", "x": 60, "y": 50},
        10: {"position": "ST", "x": 80, "y": 35},
        11: {"position": "ST", "x": 80, "y": 65}
    },
    "5-3-2": {
        1: {"position": "GK", "x": 5, "y": 50},
        2: {"position": "RWB", "x": 30, "y": 10},
        3: {"position": "CB", "x": 20, "y": 30},
        4: {"position": "CB", "x": 20, "y": 50},
        5: {"position": "CB", "x": 20, "y": 70},
        6: {"position": "LWB", "x": 30, "y": 90},
        7: {"position": "CM", "x": 50, "y": 30},
        8: {"position": "CM", "x": 50, "y": 50},
        9: {"position": "CM", "x": 50, "y": 70},
        10: {"position": "ST", "x": 75, "y": 35},
        11: {"position": "ST", "x": 75, "y": 65}
    }
}

# ===========================================
# POSITION MAPPING (StatsBomb → Formation slots)
# ===========================================
POSITION_MAPPING: Dict[str, List[str]] = {
    # Goalkeeper
    "Goalkeeper": ["GK"],

    # Defenders
    "Right Back": ["RB", "RWB"],
    "Right Wing Back": ["RWB", "RB"],
    "Right Center Back": ["CB"],
    "Center Back": ["CB"],
    "Left Center Back": ["CB"],
    "Left Back": ["LB", "LWB"],
    "Left Wing Back": ["LWB", "LB"],

    # Midfielders
    "Right Defensive Midfield": ["CDM", "CM"],
    "Center Defensive Midfield": ["CDM", "CM"],
    "Left Defensive Midfield": ["CDM", "CM"],
    "Right Midfield": ["RM", "CM"],
    "Right Center Midfield": ["CM", "CDM"],
    "Center Midfield": ["CM", "CDM"],
    "Left Center Midfield": ["CM", "CDM"],
    "Left Midfield": ["LM", "CM"],
    "Right Attacking Midfield": ["RAM", "CAM", "RW"],
    "Center Attacking Midfield": ["CAM", "CM"],
    "Left Attacking Midfield": ["LAM", "CAM", "LW"],

    # Forwards
    "Right Wing": ["RW", "RM"],
    "Left Wing": ["LW", "LM"],
    "Right Center Forward": ["ST", "CF"],
    "Center Forward": ["ST", "CF"],
    "Left Center Forward": ["ST", "CF"],
    "Striker": ["ST", "CF"]
}

# ===========================================
# UI CONFIGURATION
# ===========================================
# Color scale for player contribution (grey to red)
COLOR_SCALE_LOW = "#808080"  # Grey for low values
COLOR_SCALE_HIGH = "#FF0000"  # Red for high/important values

# Player marker size range
PLAYER_MARKER_MIN_SIZE = 15
PLAYER_MARKER_MAX_SIZE = 40

# Number of teams in Serie A
TOTAL_TEAMS = 20

# ===========================================
# SERIE A 2015-2016 TEAMS
# ===========================================
SERIE_A_TEAMS_2015_16 = {
    "Juventus": {"team_id": 171, "short_name": "JUV"},
    "Napoli": {"team_id": 175, "short_name": "NAP"},
    "Roma": {"team_id": 182, "short_name": "ROM"},
    "Inter": {"team_id": 174, "short_name": "INT"},
    "Fiorentina": {"team_id": 170, "short_name": "FIO"},
    "Milan": {"team_id": 167, "short_name": "MIL"},
    "Lazio": {"team_id": 173, "short_name": "LAZ"},
    "Sassuolo": {"team_id": 289, "short_name": "SAS"},
    "Empoli": {"team_id": 268, "short_name": "EMP"},
    "Torino": {"team_id": 186, "short_name": "TOR"},
    "Genoa": {"team_id": 172, "short_name": "GEN"},
    "Atalanta": {"team_id": 165, "short_name": "ATA"},
    "Bologna": {"team_id": 166, "short_name": "BOL"},
    "Chievo": {"team_id": 168, "short_name": "CHI"},
    "Sampdoria": {"team_id": 183, "short_name": "SAM"},
    "Udinese": {"team_id": 187, "short_name": "UDI"},
    "Palermo": {"team_id": 179, "short_name": "PAL"},
    "Carpi": {"team_id": 291, "short_name": "CAR"},
    "Frosinone": {"team_id": 292, "short_name": "FRO"},
    "Hellas Verona": {"team_id": 188, "short_name": "VER"},
}

# ===========================================
# LOGGING CONFIGURATION
# ===========================================
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": LOG_LEVEL,
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": str(BASE_DIR / "logs" / "app.log"),
            "formatter": "standard",
            "level": "DEBUG",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}
