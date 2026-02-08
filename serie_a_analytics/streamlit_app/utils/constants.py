"""
Constants for Serie A Analytics Dashboard.

This file contains constants used across the application.
"""

# ============================================================================
# METRICS WHERE LOWER IS BETTER (inverted ranking)
# ============================================================================
# These metrics should be ranked so that LOWER values get BETTER ranks (rank 1 = lowest value)
LOWER_IS_BETTER_METRICS = {
    # Defensive metrics (conceded)
    'big_chances_against',
    'xga_total',
    'xga_open_play',
    'shots_against',
    'shots_on_target_against',
    'goals_conceded',
    'xga_difference',  # xGA - Goals conceded (negative = conceding more than expected = bad)
    'xg_indirect_set_pieces_conceded',

    # Conceded metrics by shot type (fewer conceded = better defense)
    'shots_conceded_direct_sp',
    'shots_conceded_indirect_sp',
    'shots_conceded_counter',
    'shots_conceded_fast_attack',
    'shots_conceded_cross',
    'shots_conceded_long_range',
    'shots_conceded_buildup_progressive',
    'shots_conceded_buildup_direct',
    'shots_conceded_total',
    'xg_conceded_direct_sp',
    'xg_conceded_indirect_sp',
    'xg_conceded_counter',
    'xg_conceded_fast_attack',
    'xg_conceded_cross',
    'xg_conceded_long_range',
    'xg_conceded_buildup_progressive',
    'xg_conceded_buildup_direct',

    # Build-up frequency (lower = more patient possession = better)
    'buildup_sequences',

    # Discipline metrics (fewer = better)
    'fouls_committed',
    'yellow_cards',
    'red_cards',

    # Opponent metrics (fewer opponent passes = better defensive control)
    'opp_passes_def_third',

    # Possession quality metrics (lower = more efficient ball retention)
    'turnovers_per_touch',

    # Pressing intensity (lower PPDA = more aggressive pressing = better)
    'ppda',
}
