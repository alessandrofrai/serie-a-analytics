"""
Serie A 2015-2016 Analytics Dashboard - Configuration Package

This package contains all configuration settings and database connection utilities.
"""

from .settings import (
    # Paths
    BASE_DIR,
    DATA_DIR,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    ASSETS_DIR,
    LOGOS_DIR,

    # StatsBomb
    STATSBOMB_COMPETITION_ID,
    STATSBOMB_SEASON_ID,

    # Field dimensions
    FIELD_LENGTH,
    FIELD_WIDTH,
    ZONE_X_BOUNDARIES,
    ZONE_Y_BOUNDARIES,
    ZONE_BUILDUP,
    ZONE_PROGRESSION,
    ZONE_FINISHING,

    # TOPSIS
    TOPSIS_VOLUME_WEIGHT,
    TOPSIS_QUALITY_WEIGHT,

    # Metrics
    METRIC_CATEGORIES,
    TOPSIS_METRICS,
    SIMPLE_METRICS,

    # Formations
    FORMATION_COORDINATES,
    POSITION_MAPPING,

    # UI
    COLOR_SCALE_LOW,
    COLOR_SCALE_HIGH,
    PLAYER_MARKER_MIN_SIZE,
    PLAYER_MARKER_MAX_SIZE,
    TOTAL_TEAMS,

    # Teams
    SERIE_A_TEAMS_2015_16,

    # Logging
    LOGGING_CONFIG,
)

# Supabase is optional - only import if available
try:
    from .supabase_config import (
        get_supabase_client,
        test_connection,
        get_table_count,
        clear_table,
        batch_insert,
        SupabaseConnectionError,
    )
except ImportError:
    # Supabase not installed - define dummy functions
    def get_supabase_client():
        raise ImportError("supabase package not installed")
    def test_connection():
        return False
    def get_table_count(table):
        return 0
    def clear_table(table):
        pass
    def batch_insert(table, data):
        pass
    class SupabaseConnectionError(Exception):
        pass

__all__ = [
    # Paths
    "BASE_DIR",
    "DATA_DIR",
    "RAW_DATA_DIR",
    "PROCESSED_DATA_DIR",
    "ASSETS_DIR",
    "LOGOS_DIR",

    # StatsBomb
    "STATSBOMB_COMPETITION_ID",
    "STATSBOMB_SEASON_ID",

    # Field dimensions
    "FIELD_LENGTH",
    "FIELD_WIDTH",
    "ZONE_X_BOUNDARIES",
    "ZONE_Y_BOUNDARIES",
    "ZONE_BUILDUP",
    "ZONE_PROGRESSION",
    "ZONE_FINISHING",

    # TOPSIS
    "TOPSIS_VOLUME_WEIGHT",
    "TOPSIS_QUALITY_WEIGHT",

    # Metrics
    "METRIC_CATEGORIES",
    "TOPSIS_METRICS",
    "SIMPLE_METRICS",

    # Formations
    "FORMATION_COORDINATES",
    "POSITION_MAPPING",

    # UI
    "COLOR_SCALE_LOW",
    "COLOR_SCALE_HIGH",
    "PLAYER_MARKER_MIN_SIZE",
    "PLAYER_MARKER_MAX_SIZE",
    "TOTAL_TEAMS",

    # Teams
    "SERIE_A_TEAMS_2015_16",

    # Logging
    "LOGGING_CONFIG",

    # Supabase
    "get_supabase_client",
    "test_connection",
    "get_table_count",
    "clear_table",
    "batch_insert",
    "SupabaseConnectionError",
]
