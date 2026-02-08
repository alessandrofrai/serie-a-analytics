"""
Player Contribution Component

Displays player contributions to a specific metric,
ordered by contribution percentage (descending).
"""

import streamlit as st
import pandas as pd
from typing import Optional


def render_player_contributions(
    metric_name: str,
    team_metric: Optional[pd.Series],
    player_metrics: pd.DataFrame
):
    """
    Render player contributions for a specific metric.

    Args:
        metric_name: Name of the metric
        team_metric: Series with team metric info (for header)
        player_metrics: DataFrame with player contributions
    """
    # Header with team metric info
    metric_display = metric_name.replace('_', ' ').title()

    if team_metric is not None:
        value_p90 = team_metric.get('metric_value_p90', 0)
        rank = team_metric.get('metric_rank', '-')
        total = team_metric.get('total_teams', 0)

        st.markdown(f"""
        ### 📊 {metric_display}
        **{value_p90:.2f} p90** - Ranking: **#{rank}/{total}**
        """)
    else:
        st.markdown(f"### 📊 {metric_display}")

    st.markdown("---")
    st.markdown("**Contributo Giocatori** (ordinati per % contributo)")

    if len(player_metrics) == 0:
        st.info("Nessun contributo disponibile per questa metrica")
        return

    # Calculate min/max for color scaling (supports negative values)
    contributions = player_metrics['contribution_percentage'].tolist()
    min_contribution = min(contributions) if contributions else 0
    max_contribution = max(contributions) if contributions else 50

    # Display player contributions
    for idx, (_, player) in enumerate(player_metrics.iterrows(), 1):
        render_player_row(player, idx, min_contribution, max_contribution)


def render_player_row(player: pd.Series, rank: int, min_contribution: float = 0, max_contribution: float = 50):
    """
    Render a single player contribution row.

    Args:
        player: Series with player contribution data
        rank: Position in the ranking
        min_contribution: Minimum contribution in dataset (for color scaling)
        max_contribution: Maximum contribution in dataset (for color scaling)
    """
    player_name = player.get('player_name', 'Unknown')
    contribution_pct = player.get('contribution_percentage', 0)
    value_p90 = player.get('metric_value_p90', 0)
    minutes = player.get('total_minutes', 0)
    raw_value = player.get('metric_value', 0)

    # Color based on contribution (supports negative values with divergent scale)
    color = _get_contribution_color(contribution_pct, min_contribution, max_contribution)

    # Progress bar width (use absolute value for negative contributions)
    bar_width = min(100, abs(contribution_pct) * 2)  # Scale for visibility

    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

    with col1:
        st.markdown(f"""
        <div style="display: flex; align-items: center;">
            <div style="
                width: 30px;
                height: 30px;
                border-radius: 50%;
                background: {color};
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                margin-right: 10px;
            ">{rank}</div>
            <div>
                <strong>{player_name}</strong>
                <div style="
                    height: 6px;
                    width: 100%;
                    background: #e9ecef;
                    border-radius: 3px;
                    margin-top: 4px;
                ">
                    <div style="
                        width: {bar_width}%;
                        height: 100%;
                        background: {color};
                        border-radius: 3px;
                    "></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Format contribution with sign for divergent metrics
        if min_contribution < 0 and contribution_pct > 0:
            contribution_text = f"+{contribution_pct:.1f}"
        else:
            contribution_text = f"{contribution_pct:.1f}"

        st.markdown(f"""
        <div style="text-align: center;">
            <strong style="color: {color};">{contribution_text}</strong>
            <div style="font-size: 0.7rem; color: #666;">differenza</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        # Format value
        if value_p90 >= 10:
            value_str = f"{value_p90:.1f}"
        else:
            value_str = f"{value_p90:.2f}"

        st.markdown(f"""
        <div style="text-align: center;">
            <strong>{value_str}</strong>
            <div style="font-size: 0.7rem; color: #666;">p90</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div style="text-align: center;">
            <strong>{minutes}'</strong>
            <div style="font-size: 0.7rem; color: #666;">min</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='margin: 0.5rem 0; border: none; border-top: 1px solid #eee;'>", unsafe_allow_html=True)


def _get_contribution_color(contribution: float, min_val: float = 0, max_val: float = 50) -> str:
    """
    Get color based on contribution value.
    Supports divergent scale for metrics with negative values.

    Args:
        contribution: Contribution value
        min_val: Minimum value in dataset (can be negative)
        max_val: Maximum value in dataset

    Returns:
        Hex color string
    """
    if min_val < 0:
        # DIVERGENT SCALE: Red (negative) -> Grey (zero) -> Green (positive)
        if contribution < 0:
            # Negative values: grey -> red
            normalized = min(1.0, abs(contribution) / max(abs(min_val), 0.01))
            r = int(128 + (220 - 128) * normalized)  # 128 -> 220
            g = int(128 + (53 - 128) * normalized)   # 128 -> 53
            b = int(128 + (69 - 128) * normalized)   # 128 -> 69
        else:
            # Positive values: grey -> green
            normalized = min(1.0, contribution / max(max_val, 0.01))
            r = int(128 + (34 - 128) * normalized)   # 128 -> 34
            g = int(128 + (197 - 128) * normalized)  # 128 -> 197
            b = int(128 + (94 - 128) * normalized)   # 128 -> 94
    else:
        # STANDARD SCALE: Grey (low) -> Red (high)
        normalized = min(1.0, max(0.0, contribution / max(max_val, 50)))
        r = int(128 + (220 - 128) * normalized)
        g = int(128 + (53 - 128) * normalized)
        b = int(128 + (69 - 128) * normalized)

    return f'#{r:02x}{g:02x}{b:02x}'
