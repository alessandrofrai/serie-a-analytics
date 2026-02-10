"""
Pitch Visualizations Component for Player Profile.

Uses mplsoccer to create pass maps, carry maps, and duel maps
with transparent backgrounds for the player profile page.
"""

import io
import base64
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import streamlit as st
from typing import Optional, Tuple, Dict
from mplsoccer import Pitch

# Color palette for visualizations
COLORS = {
    'pass_success': '#22c55e',      # Green - completed passes
    'pass_fail': '#ef4444',          # Red - failed passes
    'carry_positive': '#3b82f6',     # Blue - positive carries
    'carry_negative': '#f97316',     # Orange - negative carries
    # Defensive actions
    'def_intercept': '#22c55e',      # Green - interceptions
    'def_aerial': '#8b5cf6',         # Purple - aerial duels
    'def_tackle': '#06b6d4',         # Cyan - tackles
    'def_recovery': '#3b82f6',       # Blue - ball recoveries
    'def_block': '#f59e0b',          # Yellow - blocks
    'def_clearance': '#ec4899',      # Pink - clearances
    'line_color': '#9ca3af',         # Gray - pitch lines
}


def create_empty_pitch() -> Tuple[plt.Figure, plt.Axes, Pitch]:
    """
    Create an empty StatsBomb pitch with transparent background.

    Returns:
        Tuple of (figure, axes, pitch)
    """
    pitch = Pitch(
        pitch_type='statsbomb',
        pitch_color='none',
        line_color=COLORS['line_color'],
        linewidth=1,
        goal_type='box',
        corner_arcs=True
    )

    fig, ax = pitch.draw(figsize=(8, 5.2))
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    return fig, ax, pitch


def create_pass_pitch(df_events: pd.DataFrame, player_id: int) -> plt.Figure:
    """
    Create pass map showing successful (green) and failed (red) passes.

    Only includes open play passes (set pieces and throw-ins already filtered
    during extraction).

    Args:
        df_events: DataFrame with player events (from player_events table)
        player_id: StatsBomb player ID

    Returns:
        Matplotlib figure with pass visualization
    """
    fig, ax, pitch = create_empty_pitch()

    # Filter passes for this player
    passes = df_events[
        (df_events['player_id'] == player_id) &
        (df_events['event_type'] == 'pass')
    ].copy()

    if passes.empty:
        ax.text(60, 40, 'Nessun passaggio', ha='center', va='center',
                fontsize=12, color='#6b7280')
        return fig

    # Convert coordinates back from SMALLINT (divide by 10)
    passes['start_x'] = passes['start_x'] / 10.0
    passes['start_y'] = passes['start_y'] / 10.0
    passes['end_x'] = passes['end_x'] / 10.0
    passes['end_y'] = passes['end_y'] / 10.0

    # Split by outcome
    successful = passes[passes['outcome'] == 1]
    failed = passes[passes['outcome'] == 0]

    # Draw failed passes first (so successful are on top)
    if not failed.empty:
        pitch.arrows(
            failed['start_x'].values,
            failed['start_y'].values,
            failed['end_x'].values,
            failed['end_y'].values,
            width=2,
            headwidth=6,
            headlength=5,
            color=COLORS['pass_fail'],
            alpha=0.5,
            ax=ax,
            label=f'Falliti ({len(failed)})'
        )

    # Draw successful passes
    if not successful.empty:
        pitch.arrows(
            successful['start_x'].values,
            successful['start_y'].values,
            successful['end_x'].values,
            successful['end_y'].values,
            width=2,
            headwidth=6,
            headlength=5,
            color=COLORS['pass_success'],
            alpha=0.6,
            ax=ax,
            label=f'Riusciti ({len(successful)})'
        )

    # Add legend
    ax.legend(loc='upper right', fontsize=7, framealpha=0.8)

    return fig


def create_carry_pitch(df_events: pd.DataFrame, player_id: int) -> plt.Figure:
    """
    Create carry map showing positive (blue) and negative (orange) carries.

    Uses dashed lines with directional arrowheads at the end to show
    where the carry started and ended.

    Args:
        df_events: DataFrame with player events
        player_id: StatsBomb player ID

    Returns:
        Matplotlib figure with carry visualization
    """
    fig, ax, pitch = create_empty_pitch()

    # Filter carries for this player
    carries = df_events[
        (df_events['player_id'] == player_id) &
        (df_events['event_type'] == 'carry')
    ].copy()

    if carries.empty:
        ax.text(60, 40, 'Nessuna conduzione', ha='center', va='center',
                fontsize=12, color='#6b7280')
        return fig

    # Convert coordinates back from SMALLINT
    carries['start_x'] = carries['start_x'] / 10.0
    carries['start_y'] = carries['start_y'] / 10.0
    carries['end_x'] = carries['end_x'] / 10.0
    carries['end_y'] = carries['end_y'] / 10.0

    # Split by outcome
    positive = carries[carries['outcome'] == 1]
    negative = carries[carries['outcome'] == 0]

    # Draw negative carries first (dashed lines)
    if not negative.empty:
        pitch.lines(
            negative['start_x'].values,
            negative['start_y'].values,
            negative['end_x'].values,
            negative['end_y'].values,
            lw=2,
            linestyle='--',
            color=COLORS['carry_negative'],
            alpha=0.5,
            ax=ax,
            label=f'Negativi ({len(negative)})'
        )
        # Add directional arrowheads at end points
        # Calculate angles using mplsoccer's official method
        angle_neg, _ = pitch.calculate_angle_and_distance(
            negative['start_x'].values,
            negative['start_y'].values,
            negative['end_x'].values,
            negative['end_y'].values,
            degrees=True
        )
        pitch.scatter(
            negative['end_x'].values,
            negative['end_y'].values,
            rotation_degrees=angle_neg,
            marker='^',
            s=35,
            color=COLORS['carry_negative'],
            alpha=0.7,
            ax=ax,
            zorder=3
        )

    # Draw positive carries (dashed lines)
    if not positive.empty:
        pitch.lines(
            positive['start_x'].values,
            positive['start_y'].values,
            positive['end_x'].values,
            positive['end_y'].values,
            lw=2,
            linestyle='--',
            color=COLORS['carry_positive'],
            alpha=0.6,
            ax=ax,
            label=f'Positivi ({len(positive)})'
        )
        # Add directional arrowheads at end points
        angle_pos, _ = pitch.calculate_angle_and_distance(
            positive['start_x'].values,
            positive['start_y'].values,
            positive['end_x'].values,
            positive['end_y'].values,
            degrees=True
        )
        pitch.scatter(
            positive['end_x'].values,
            positive['end_y'].values,
            rotation_degrees=angle_pos,
            marker='^',
            s=35,
            color=COLORS['carry_positive'],
            alpha=0.8,
            ax=ax,
            zorder=3
        )

    ax.legend(loc='upper right', fontsize=7, framealpha=0.8)

    return fig


def create_duel_pitch(df_events: pd.DataFrame, player_id: int) -> plt.Figure:
    """
    Create defensive actions map showing all defensive interventions.

    Includes: Interceptions, Aerial duels, Tackles, Ball Recoveries, Blocks, Clearances.

    Args:
        df_events: DataFrame with player events
        player_id: StatsBomb player ID

    Returns:
        Matplotlib figure with defensive actions visualization
    """
    fig, ax, pitch = create_empty_pitch()

    # Filter defensive actions for this player
    defensive = df_events[
        (df_events['player_id'] == player_id) &
        (df_events['event_type'] == 'duel')
    ].copy()

    if defensive.empty:
        ax.text(60, 40, 'Nessuna azione difensiva', ha='center', va='center',
                fontsize=12, color='#6b7280')
        return fig

    # Convert coordinates back from SMALLINT
    defensive['start_x'] = defensive['start_x'] / 10.0
    defensive['start_y'] = defensive['start_y'] / 10.0

    # Color mapping for defensive action types
    action_colors = {
        'Intercept': COLORS['def_intercept'],
        'Aerial': COLORS['def_aerial'],
        'Tackle': COLORS['def_tackle'],
        'Recovery': COLORS['def_recovery'],
        'Block': COLORS['def_block'],
        'Clearance': COLORS['def_clearance'],
    }

    # Italian labels for legend
    action_labels = {
        'Intercept': 'Intercetti',
        'Aerial': 'Aerei',
        'Tackle': 'Tackle',
        'Recovery': 'Recuperi',
        'Block': 'Blocchi',
        'Clearance': 'Rinvii',
    }

    # Plot each action type separately for legend
    for action_type in defensive['subtype'].unique():
        if pd.isna(action_type) or action_type == 'Other':
            continue

        type_actions = defensive[defensive['subtype'] == action_type]
        color = action_colors.get(action_type, '#9ca3af')
        label = action_labels.get(action_type, action_type)

        # Use different markers for won/lost
        won = type_actions[type_actions['outcome'] == 1]
        lost = type_actions[type_actions['outcome'] == 0]

        if not won.empty:
            pitch.scatter(
                won['start_x'].values,
                won['start_y'].values,
                s=70,
                color=color,
                edgecolors='white',
                linewidths=1.5,
                alpha=0.8,
                ax=ax,
                marker='o',
                label=f'{label} ({len(won)})'
            )

        if not lost.empty:
            pitch.scatter(
                lost['start_x'].values,
                lost['start_y'].values,
                s=50,
                color=color,
                edgecolors='white',
                linewidths=1,
                alpha=0.35,
                ax=ax,
                marker='x',
                label=f'{label} persi ({len(lost)})'
            )

    ax.legend(loc='upper right', fontsize=5, framealpha=0.8, ncol=2)

    return fig


def render_pitch_visualizations(
    player_id: int,
    df_events: pd.DataFrame,
    last_n_matches: Optional[int] = None,
    match_dates: Optional[pd.DataFrame] = None
):
    """
    Render all three pitch visualizations in a horizontal layout.

    Args:
        player_id: StatsBomb player ID
        df_events: DataFrame with player events from player_events table
        last_n_matches: Filter to last N matches (None = all)
        match_dates: DataFrame with match_id and match_date for filtering
    """
    # Filter by player
    player_events = df_events[df_events['player_id'] == player_id].copy()

    if player_events.empty:
        st.info("Nessun evento disponibile per questo giocatore.")
        return

    # Filter by last N matches if specified
    if last_n_matches and match_dates is not None and not match_dates.empty:
        # Get match IDs for this player
        player_match_ids = player_events['match_id'].unique()

        # Filter match_dates to only player's matches
        player_matches = match_dates[match_dates['match_id'].isin(player_match_ids)]

        if not player_matches.empty:
            # Sort by match_week (round) descending if available, otherwise by date
            if 'match_week' in player_matches.columns:
                player_matches = player_matches.sort_values('match_week', ascending=False)
            else:
                player_matches = player_matches.sort_values('match_date', ascending=False)
            recent_match_ids = player_matches['match_id'].head(last_n_matches).tolist()
            player_events = player_events[player_events['match_id'].isin(recent_match_ids)]

    if player_events.empty:
        st.info("Nessun evento disponibile per le partite selezionate.")
        return

    # Create three columns
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Passaggi Open Play**")
        fig_pass = create_pass_pitch(player_events, player_id)
        st.pyplot(fig_pass, transparent=True, use_container_width=True)
        plt.close(fig_pass)

    with col2:
        st.markdown("**Conduzioni**")
        fig_carry = create_carry_pitch(player_events, player_id)
        st.pyplot(fig_carry, transparent=True, use_container_width=True)
        plt.close(fig_carry)

    with col3:
        st.markdown("**Azioni Difensive**")
        fig_duel = create_duel_pitch(player_events, player_id)
        st.pyplot(fig_duel, transparent=True, use_container_width=True)
        plt.close(fig_duel)


def render_match_filter(num_matches: int) -> int:
    """
    Render a horizontal slider for filtering by last N matches.

    Dynamically adapts to the number of matches the player has played.
    Default is 4 matches (or max available if less than 4).

    Args:
        num_matches: Total number of matches the player has played

    Returns:
        Number of matches to show
    """
    if num_matches <= 1:
        return num_matches

    # Default to 4, but cap at max available
    default_value = min(4, num_matches)

    selected = st.slider(
        "Ultime partite",
        min_value=1,
        max_value=num_matches,
        value=default_value,
        step=1,
        key="pitch_viz_match_filter"
    )

    return selected


def _fig_to_base64(fig: plt.Figure, dpi: int = 120) -> str:
    """
    Convert a matplotlib figure to a base64 encoded PNG string.

    Args:
        fig: Matplotlib figure
        dpi: Resolution (default 120 for good quality in HTML)

    Returns:
        Base64 encoded string (without data:image/png;base64, prefix)
    """
    buf = io.BytesIO()
    fig.savefig(buf, format='png', transparent=True, bbox_inches='tight', dpi=dpi)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    plt.close(fig)
    return img_base64


def generate_pitch_images_base64(
    player_id: int,
    df_events: pd.DataFrame,
    last_n_matches: Optional[int] = None,
    match_dates: Optional[pd.DataFrame] = None
) -> Dict[str, Optional[str]]:
    """
    Generate pitch visualization images as base64 strings for PDF export.

    Creates the same 3 visualizations as render_pitch_visualizations() but
    returns them as base64 images instead of displaying with st.pyplot().

    Args:
        player_id: StatsBomb player ID
        df_events: DataFrame with player events from player_events table
        last_n_matches: Filter to last N matches (None = all)
        match_dates: DataFrame with match_id and match_date for filtering

    Returns:
        Dict with keys 'pass', 'carry', 'duel' containing base64 strings.
        Returns empty strings for visualizations with no data.
    """
    result = {
        'pass': None,
        'carry': None,
        'duel': None
    }

    # Filter by player
    player_events = df_events[df_events['player_id'] == player_id].copy()

    if player_events.empty:
        return result

    # Filter by last N matches if specified
    if last_n_matches and match_dates is not None and not match_dates.empty:
        player_match_ids = player_events['match_id'].unique()
        player_matches = match_dates[match_dates['match_id'].isin(player_match_ids)]

        if not player_matches.empty:
            if 'match_week' in player_matches.columns:
                player_matches = player_matches.sort_values('match_week', ascending=False)
            else:
                player_matches = player_matches.sort_values('match_date', ascending=False)
            recent_match_ids = player_matches['match_id'].head(last_n_matches).tolist()
            player_events = player_events[player_events['match_id'].isin(recent_match_ids)]

    if player_events.empty:
        return result

    # Generate each pitch visualization
    fig_pass = create_pass_pitch(player_events, player_id)
    result['pass'] = _fig_to_base64(fig_pass)

    fig_carry = create_carry_pitch(player_events, player_id)
    result['carry'] = _fig_to_base64(fig_carry)

    fig_duel = create_duel_pitch(player_events, player_id)
    result['duel'] = _fig_to_base64(fig_duel)

    return result
