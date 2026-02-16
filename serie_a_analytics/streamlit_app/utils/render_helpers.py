"""
Render helper functions for Serie A Analytics.

This module contains all rendering functions that are shared between
the main app and dashboard pages. These functions contain Streamlit-specific
code for rendering UI components.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path

from components.metrics_panel import METRIC_NAMES, CATEGORY_NAMES
from components.metrics_info import render_metrics_info_button
from utils.data_helpers import (
    is_strength, is_average, is_weakness, MIN_MATCHES, get_team_playing_style,
    get_sofascore_player_id_map, get_sofascore_team_id,
    get_sofascore_names_map, get_player_display_name, extract_surname
)
from services.player_analysis import (
    PlayerAnalyzer,
    METRIC_NAMES_IT,
)
# Keep scatter/violin orientation consistent for "lower is better" metrics.
from utils.constants import LOWER_IS_BETTER_METRICS


# ============================================
# GAME PHASE METRICS - Excluded from Rank Metriche panel (shown in dedicated section)
# ============================================
GAME_PHASE_METRICS = {
    # Shots creati per fase
    'shots_direct_sp', 'shots_indirect_sp', 'shots_counter', 'shots_fast_attack',
    'shots_cross', 'shots_long_range', 'shots_buildup_progressive', 'shots_buildup_direct',
    # xG creato per fase
    'xg_direct_sp', 'xg_indirect_sp', 'xg_counter', 'xg_fast_attack',
    'xg_cross', 'xg_long_range', 'xg_buildup_progressive', 'xg_buildup_direct',
    # Shots subiti per fase
    'shots_conceded_direct_sp', 'shots_conceded_indirect_sp', 'shots_conceded_counter',
    'shots_conceded_fast_attack', 'shots_conceded_cross', 'shots_conceded_long_range',
    'shots_conceded_buildup_progressive', 'shots_conceded_buildup_direct',
    # xG subito per fase
    'xg_conceded_direct_sp', 'xg_conceded_indirect_sp', 'xg_conceded_counter',
    'xg_conceded_fast_attack', 'xg_conceded_cross', 'xg_conceded_long_range',
    'xg_conceded_buildup_progressive', 'xg_conceded_buildup_direct',
    # Totali shot analysis
    'shots_made_total', 'shots_conceded_total',
}


# ============================================
# PDF BUTTON CALLBACKS - Must be at module level for Streamlit to find them
# ============================================
def _toggle_pdf_metric(sk, mn):
    """Toggle metric in PDF selection. Creates new dict/set to force state detection."""
    if 'pdf_selected_metrics' not in st.session_state:
        st.session_state.pdf_selected_metrics = {'positive': set(), 'average': set(), 'negative': set()}
    # Create new dict with new set to force Streamlit to detect change
    new_dict = {k: v.copy() for k, v in st.session_state.pdf_selected_metrics.items()}
    if sk not in new_dict:
        new_dict[sk] = set()
    if mn in new_dict[sk]:
        new_dict[sk].discard(mn)
    else:
        new_dict[sk].add(mn)
    st.session_state.pdf_selected_metrics = new_dict
    # No st.rerun() - let fragment handle rerun to prevent left column flickering


def _toggle_detail_metric(sk, mn):
    """Toggle metric in PDF detail selection. Creates new dict/set to force state detection."""
    if 'pdf_detail_metrics' not in st.session_state:
        st.session_state.pdf_detail_metrics = {'positive': set(), 'average': set(), 'negative': set()}
    # Create new dict with new set to force Streamlit to detect change
    new_dict = {k: v.copy() for k, v in st.session_state.pdf_detail_metrics.items()}
    if sk not in new_dict:
        new_dict[sk] = set()
    if mn in new_dict[sk]:
        new_dict[sk].discard(mn)
    else:
        new_dict[sk].add(mn)
    st.session_state.pdf_detail_metrics = new_dict
    # No st.rerun() - let fragment handle rerun to prevent left column flickering


@st.fragment
def render_metrics_with_filter(team_metrics, total_combinations, all_team_metrics=None):
    """
    Render the filter segmented control and metrics list.
    Now includes selection counts in tab labels.
    """
    # Calculate selection counts from session state
    positive_count = len(st.session_state.get('pdf_selected_metrics', {}).get('positive', set()))
    average_count = len(st.session_state.get('pdf_selected_metrics', {}).get('average', set()))
    negative_count = len(st.session_state.get('pdf_selected_metrics', {}).get('negative', set()))

    # Create labels with counts (only show count if > 0)
    positive_label = f"Positive ({positive_count})" if positive_count > 0 else "Positive"
    average_label = f"Nella Media ({average_count})" if average_count > 0 else "Nella Media"
    negative_label = f"Negative ({negative_count})" if negative_count > 0 else "Negative"

    # Dynamic mapping between display labels and internal filter types
    filter_options = [positive_label, average_label, negative_label]
    filter_mapping = {
        positive_label: "strength",
        average_label: "average",
        negative_label: "weakness"
    }

    # Initialize session state for the segmented control if not present
    # Use a separate state key to track which category is selected (independent of label text)
    if 'metrics_filter_category' not in st.session_state:
        st.session_state.metrics_filter_category = "strength"

    # Determine default index based on saved category
    category_to_index = {"strength": 0, "average": 1, "weakness": 2}
    default_index = category_to_index.get(st.session_state.metrics_filter_category, 0)

    # Simple segmented control with dynamic labels
    selected_filter = st.segmented_control(
        "Filtra metriche",
        options=filter_options,
        default=filter_options[default_index],
        key="metrics_filter_selection_dynamic",
        label_visibility="collapsed"
    )

    # Info button with metric explanations
    render_metrics_info_button()

    # Get the filter type from the selected value
    if selected_filter:
        current_filter = filter_mapping.get(selected_filter, "strength")
        st.session_state.metrics_filter_category = current_filter
    else:
        current_filter = st.session_state.metrics_filter_category

    # Render the metrics list using the current selection
    render_filtered_metrics(team_metrics, total_combinations, current_filter, all_team_metrics=all_team_metrics)


# Metric normalization labels (how each metric is normalized)
METRIC_NORMALIZATIONS = {
    # Percentage metrics (%)
    'goal_conversion_rate': '%',
    'goal_conversion_sot': '%',
    'big_chances_conversion': '%',
    'possession_percentage': '%',
    'buildup_progressive_ratio': '%',
    'buildup_success_rate': '%',
    'pressing_success_rate': '%',

    # Per 100 opponent passes in defensive third
    'tackles': 'per 100 pass. avv.',
    'interceptions': 'per 100 pass. avv.',
    'clearances': 'per 100 pass. avv.',
    'blocks': 'per 100 pass. avv.',
    'ground_duels_defensive': 'per 100 pass. avv.',

    # Per 100 long passes (aerial duels)
    'aerial_duels_offensive': 'per 100 lanci',
    'aerial_duels_defensive': 'per 100 lanci',

    # Per 100 lost balls (ground duels offensive)
    'ground_duels_offensive': 'per 100 turnover',

    # Per corners/set pieces
    'sot_per_100_corners': 'per 100 corner',
    'sot_per_100_indirect_sp': 'per 100 inattive',

    # PPDA (ratio)
    'ppda': 'tasso',

    # Per touch
    'turnovers_per_touch': 'per tocco',
    'shots_per_box_touch': 'per tocco',

    # xA per key pass
    'xa_per_key_pass': 'per pass. chiave',
    'goals_per_xa': 'gol/xA',

    # Difference metrics
    'xg_goals_difference': 'diff.',
    'xga_difference': 'diff.',
}


def _lighten_hex(hex_color: str, amount: float = 0.6) -> str:
    """Lighten a hex color by mixing with white."""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    r = int(r + (255 - r) * amount)
    g = int(g + (255 - g) * amount)
    b = int(b + (255 - b) * amount)
    return f"#{r:02x}{g:02x}{b:02x}"


def _render_metric_distribution_sparkline(
    values,
    selected_value,
    color: str,
    metric_key: str,
    lower_is_better: bool = False,
    height: int = 70
):
    """Render a compact scatter + half violin distribution with highlighted value."""
    if not values:
        return

    # CRITICAL FIX: Ensure selected_value is ALWAYS in the values list
    # This guarantees the violin chart extends to cover selected_value
    # and the scatter plot includes it, making the highlighted point always visible
    # NOTE: Always append without checking 'not in' - float comparison is unreliable
    # and duplicates don't affect the visualization negatively
    values = list(values)  # Create a copy to avoid modifying original

    # DEBUG: Log values range and selected_value
    import streamlit as st
    sel_str = f"{selected_value:.2f}" if selected_value is not None else "None"
    st.caption(f"DEBUG: values range [{min(values):.2f}, {max(values):.2f}], selected={sel_str}")

    if selected_value is not None:
        values.append(selected_value)

    # Deterministic jitter based on metric key (tight vertical spread)
    seed = abs(hash(metric_key)) % (2**32)
    rng = np.random.default_rng(seed)
    jitter = rng.normal(0, 0.01, size=len(values))

    # Build figure
    fig = go.Figure()

    violin_color = _lighten_hex(color, 0.6)
    violin_line = _lighten_hex(color, 0.2)

    fig.add_trace(go.Violin(
        x=values,
        y=[0] * len(values),
        orientation="h",
        side="positive",
        fillcolor=violin_color,
        line_color=violin_line,
        opacity=0.32,
        width=0.25,
        points=False,
        spanmode="hard",
        meanline_visible=False,
        hoverinfo="skip",
        showlegend=False
    ))

    fig.add_trace(go.Scatter(
        x=values,
        y=jitter,
        mode="markers",
        marker=dict(color="#4b5563", size=5, opacity=0.8),
        hoverinfo="skip",
        showlegend=False
    ))

    if selected_value is not None:
        fig.add_trace(go.Scatter(
            x=[selected_value],
            y=[0],
            mode="markers",
            marker=dict(color=color, size=10, line=dict(color="white", width=1.5)),
            hoverinfo="skip",
            showlegend=False
        ))

    # Pad x-range so distribution/violin isn't clipped
    vmin = min(values)
    vmax = max(values)

    # CRITICAL FIX: Include selected_value in range calculation
    # This ensures the highlighted point is ALWAYS visible
    if selected_value is not None:
        vmin = min(vmin, selected_value)
        vmax = max(vmax, selected_value)

    span = max(vmax - vmin, 1e-6)
    pad = span * 0.15  # Increased from 0.08 to 0.15 for marker visibility

    # Invert axis for metrics where lower is better (so "better" is to the right)
    if lower_is_better:
        x_range = [vmax + pad, vmin - pad]
    else:
        x_range = [vmin - pad, vmax + pad]

    fig.update_layout(
        height=height,
        margin=dict(l=4, r=4, t=2, b=2),
        xaxis=dict(
            visible=False,
            showgrid=False,
            zeroline=False,
            range=x_range,
            fixedrange=True
        ),
        yaxis=dict(
            visible=False,
            showgrid=False,
            zeroline=False,
            range=[-0.18, 0.18],
            fixedrange=True
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def render_filtered_metrics(team_metrics, total_combinations, filter_type="strength", all_team_metrics=None):
    """Render metrics filtered by strength/average/weakness with colored bars and clickable rows.

    Uses native Streamlit widgets with colored progress bars (emoji-based) and clickable cards.

    Args:
        filter_type: "strength" (top 25%), "average" (25-75%), "weakness" (bottom 25%)
    """
    if len(team_metrics) == 0:
        st.info("Nessuna metrica disponibile", icon=":material/info:")
        return

    # Filter metrics based on type
    filtered_metrics = []
    for _, m in team_metrics.iterrows():
        metric_name = m.get('metric_name', '')

        # Skip game phase metrics (shown in dedicated section)
        if metric_name in GAME_PHASE_METRICS:
            continue

        rank = int(m.get('metric_rank', 0))
        if filter_type == "strength" and is_strength(rank, total_combinations):
            filtered_metrics.append(m)
        elif filter_type == "average" and is_average(rank, total_combinations):
            filtered_metrics.append(m)
        elif filter_type == "weakness" and is_weakness(rank, total_combinations):
            filtered_metrics.append(m)

    if len(filtered_metrics) == 0:
        messages = {
            "strength": "Nessun punto di forza (top 25%)",
            "average": "Nessuna metrica nella media (25-75%)",
            "weakness": "Nessun punto debole (bottom 25%)"
        }
        st.info(messages[filter_type], icon=":material/info:")
        return

    # Color config based on filter type
    bar_config = {
        "strength": {"filled": "🟩", "empty": "⬜", "badge": "green"},
        "average": {"filled": "🟧", "empty": "⬜", "badge": "orange"},
        "weakness": {"filled": "🟥", "empty": "⬜", "badge": "red"},
    }
    config = bar_config[filter_type]

    # Category icons (Material icons work in native st.markdown)
    category_icons = {
        'attacking': ':material/sports_soccer:',
        'defending': ':material/shield:',
        'possession': ':material/swap_horiz:',
        'pressing': ':material/speed:',
        'buildup': ':material/arrow_upward:',  # Build-up from defensive zone
        'transition': ':material/bolt:',  # Fast transitions
        'conceded': ':material/gpp_bad:',  # Vulnerabilità - scudo rotto
    }

    # Group by category (with buildup_* override to separate from transition)
    metrics_by_category = {}
    for m in filtered_metrics:
        metric_name = m['metric_name']
        # Override: metriche buildup_* vanno nella categoria 'buildup' (Costruzione)
        if metric_name.startswith('buildup_'):
            cat = 'buildup'
        else:
            cat = m['metric_category']
        if cat not in metrics_by_category:
            metrics_by_category[cat] = []
        metrics_by_category[cat].append(m)

    # Sort metrics within each category by rank
    # - Positive (strength): rank migliore (1) prima (ascending)
    # - Nella Media e Negative: rank peggiore (più alto) prima (descending)
    sort_ascending = (filter_type == "strength")
    for cat in metrics_by_category:
        metrics_by_category[cat] = sorted(
            metrics_by_category[cat],
            key=lambda x: int(x.get('metric_rank', 999)),
            reverse=(not sort_ascending)
        )

    # Colors based on filter type
    progress_colors = {
        "strength": "#22c55e",  # Green
        "average": "#f59e0b",   # Orange
        "weakness": "#ef4444",  # Red
    }
    progress_color = progress_colors.get(filter_type, "#22c55e")

    # Badge colors for value display
    badge_colors = {
        "strength": "#28a745",
        "average": "#fd7e14",
        "weakness": "#dc3545",
    }
    badge_color = badge_colors.get(filter_type, "#28a745")

    # Map filter type to session state key for PDF selection
    state_key_map = {
        "strength": "positive",
        "average": "average",
        "weakness": "negative"
    }
    state_key = state_key_map.get(filter_type, "positive")

    # Precompute distributions if available
    metric_values_map = None
    if all_team_metrics is not None and len(all_team_metrics) > 0 and 'metric_value_p90' in all_team_metrics.columns:
        metric_values_map = (
            all_team_metrics.groupby('metric_name')['metric_value_p90']
            .apply(lambda s: s.dropna().tolist())
            .to_dict()
        )

    # Custom category order (as requested by user)
    CATEGORY_ORDER = [
        'buildup',      # Costruzione
        'transition',   # Transizioni
        'conceded',     # Vulnerabilità (tiri/xG subiti per fase)
        'pressing',     # Pressing
        'possession',   # Possesso
        'defending',    # Difesa
        'attacking',    # Attacco
        'set_pieces',   # Palle Inattive
        # Categories below are less common but included for completeness
        'chance_creation',
        'goalkeeping',
        'shot_analysis',
    ]

    # Render each category in custom order (only categories with metrics)
    ordered_categories = [c for c in CATEGORY_ORDER if c in metrics_by_category]
    # Add any remaining categories not in CATEGORY_ORDER (safety fallback)
    for c in metrics_by_category:
        if c not in ordered_categories:
            ordered_categories.append(c)

    for category in ordered_categories:
        cat_name = CATEGORY_NAMES.get(category, category.title())
        cat_icon = category_icons.get(category, ':material/analytics:')

        # Category header with icon
        st.markdown(f"### {cat_icon} {cat_name}")

        category_metrics = metrics_by_category[category]

        # Render each metric row - all elements in one container with button inside
        for idx, m in enumerate(category_metrics):
            metric_name = m['metric_name']
            display_name = METRIC_NAMES.get(metric_name, metric_name.replace('_', ' ').title())
            value = m['metric_value_p90']
            rank = int(m.get('metric_rank', 0))

            # Format value
            if value >= 100:
                value_str = f"{value:.0f}"
            elif value >= 10:
                value_str = f"{value:.1f}"
            else:
                value_str = f"{value:.2f}"

            # Progress percentage
            progress_pct = (total_combinations - rank + 1) / total_combinations if total_combinations > 0 else 0
            pct_width = int(progress_pct * 100)

            # Container with border for all rows
            with st.container(border=True):
                # Initialize session state sets if not present
                if 'pdf_selected_metrics' not in st.session_state:
                    st.session_state.pdf_selected_metrics = {'positive': set(), 'average': set(), 'negative': set()}
                if 'pdf_detail_metrics' not in st.session_state:
                    st.session_state.pdf_detail_metrics = {'positive': set(), 'average': set(), 'negative': set()}

                is_pdf_selected = metric_name in st.session_state.pdf_selected_metrics.get(state_key, set())
                is_detail_selected = metric_name in st.session_state.pdf_detail_metrics.get(state_key, set())

                # Top row: PDF buttons on the LEFT side
                # Keys for CSS targeting (Streamlit generates .st-key-{key} classes)
                pdf_btn_key = f"pdf_btn_{filter_type}_{metric_name}"
                detail_btn_key = f"detail_btn_{filter_type}_{metric_name}"
                metric_btn_key = f"metric_btn_{filter_type}_{metric_name}"

                # Inject CSS for buttons (small font)
                st.html(f"""
                <style>
                .st-key-{pdf_btn_key} .stButton button,
                .st-key-{detail_btn_key} .stButton button,
                .st-key-{metric_btn_key} .stButton button {{
                    font-size: 0.65rem !important;
                    padding: 4px 10px !important;
                    min-height: 24px !important;
                    border-radius: 12px !important;
                    line-height: 1.2 !important;
                }}
                .st-key-{pdf_btn_key} .stButton button p,
                .st-key-{detail_btn_key} .stButton button p,
                .st-key-{metric_btn_key} .stButton button p {{
                    font-size: 0.65rem !important;
                    line-height: 1.2 !important;
                    margin: 0 !important;
                }}
                </style>
                """)

                # PDF selection buttons with on_click callbacks (no st.rerun needed)
                col_pdf_btn, col_detail_btn, col_spacer_top = st.columns([0.18, 0.18, 0.64], gap="small")

                with col_pdf_btn:
                    pdf_btn_type = "primary" if is_pdf_selected else "secondary"
                    st.button(
                        "Includi nel PDF",
                        key=pdf_btn_key,
                        type=pdf_btn_type,
                        on_click=_toggle_pdf_metric,
                        args=(state_key, metric_name)
                    )

                with col_detail_btn:
                    detail_btn_type = "primary" if is_detail_selected else "secondary"
                    st.button(
                        "Dettagli in PDF",
                        key=detail_btn_key,
                        type=detail_btn_type,
                        on_click=_toggle_detail_metric,
                        args=(state_key, metric_name)
                    )

                # Main metric info row
                col_name, col_bar, col_spacer, col_val, col_rank, col_btn = st.columns(
                    [2.3, 1.4, 0.1, 1.3, 1.1, 0.8],
                    vertical_alignment="center",
                    gap="small"
                )

                with col_name:
                    st.markdown(f"**{display_name}**")

                with col_bar:
                    if metric_values_map and metric_name in metric_values_map:
                        _render_metric_distribution_sparkline(
                            metric_values_map[metric_name],
                            value,
                            progress_color,
                            metric_key=f"{filter_type}_{metric_name}",
                            lower_is_better=metric_name in LOWER_IS_BETTER_METRICS,
                            height=70
                        )
                    else:
                        # Fallback: simple progress bar
                        bar_html = (
                            f'<div style="background:#e0e0e0;border-radius:3px;height:8px;width:100%;">'
                            f'<div style="background:{progress_color};width:{pct_width}%;height:100%;border-radius:3px;"></div>'
                            f'</div>'
                        )
                        st.markdown(bar_html, unsafe_allow_html=True)

                with col_spacer:
                    st.write("")

                with col_val:
                    # Get normalization label for this metric
                    norm_label = METRIC_NORMALIZATIONS.get(metric_name, 'p90')
                    norm_label_display = norm_label
                    norm_label_style = "color:#9ca3af;font-size:0.75rem;"
                    # If label is long, stack words vertically to avoid overflow
                    if " " in norm_label and (norm_label.startswith("per 100") or len(norm_label) >= 12):
                        if norm_label.startswith("per 100 "):
                            remainder = norm_label[len("per 100 "):]
                            norm_label_display = "per 100<br>" + remainder.replace(" ", "<br>")
                        else:
                            norm_label_display = norm_label.replace(" ", "<br>")
                        norm_label_style += "line-height:1.05;"
                    # Value badge (larger) + normalization (smaller, lighter gray)
                    val_html = (
                        f'<div style="display:flex;flex-direction:column;align-items:flex-end;gap:2px;'
                        f'width:100%;margin-top:-4px;">'
                        f'<span style="background:{badge_color};color:#fff;padding:4px 10px;border-radius:4px;'
                        f'font-size:1rem;font-weight:600;">{value_str}</span>'
                        f'<span style="{norm_label_style}text-align:right;">{norm_label_display}</span>'
                        f'</div>'
                    )
                    st.markdown(val_html, unsafe_allow_html=True)

                with col_rank:
                    # Large rank number (not bold) + smaller total
                    st.markdown(
                        "<span style='display:inline-flex;align-items:baseline;white-space:nowrap;'>"
                        f"<span style='color:#374151;font-size:1.4rem;font-weight:400;'>#</span>"
                        f"<span style=\"color:#374151;font-size:1.7rem;font-weight:600;margin-left:2px;"
                        f"font-family:'Avenir Next','Helvetica Neue',sans-serif;\">{rank}</span>"
                        f"<span style='color:#9ca3af;font-size:0.8rem;margin-left:2px;'>/{total_combinations}</span>"
                        "</span>",
                        unsafe_allow_html=True
                    )

                with col_btn:
                    if st.button("Dettagli", key=f"metric_btn_{filter_type}_{metric_name}",
                                help=f"Dettagli {display_name}", use_container_width=True):
                        st.session_state.selected_metric = metric_name
                        st.rerun()


def render_full_team_ranking(all_team_metrics, metric_name, current_team_id, current_manager_id, combinations_df):
    """Render FULL ranking of all teams for a specific metric with clickable rows."""
    metric_data = all_team_metrics[all_team_metrics['metric_name'] == metric_name].copy()

    if len(metric_data) == 0:
        st.info("Classifica non disponibile", icon=":material/info:")
        return

    metric_data = metric_data.sort_values('metric_value_p90', ascending=False)

    # Build team info map (include manager name for navigation)
    # Uses combinations_df passed as parameter (from Supabase or CSV via load_data())
    team_info_map = {}

    # Italian surname prefixes (CAPITALIZED = part of surname)
    surname_prefixes_capitalized = {'Di', 'De', 'Del', 'Della', 'Dello', 'Dei', 'Degli',
                                    'Da', 'Dal', 'Dalla', 'Dallo', 'Dai',
                                    'Lo', 'La', 'Li', 'Le', 'Van', 'Von'}

    for _, row in combinations_df.iterrows():
        if row['matches_count'] >= MIN_MATCHES:
            manager_name = row['manager_name']
            if manager_name:
                parts = manager_name.split()
                if len(parts) >= 2 and parts[-2] in surname_prefixes_capitalized:
                    manager_surname = f"{parts[-2]} {parts[-1]}"
                else:
                    manager_surname = parts[-1]
            else:
                manager_surname = ""
            manager_id = row.get('manager_id', row.name + 1) if 'manager_id' in row else row.name + 1
            team_info_map[(row['team_id'], manager_id)] = {
                'display_name': f"{row['team_name']} ({manager_surname})",
                'team_name': row['team_name'],
                'manager_name': manager_name
            }

    total = len(metric_data)

    # Render each team row with clickable button
    for rank, (_, row) in enumerate(metric_data.iterrows(), 1):
        team_id = row['team_id']
        manager_id = row['manager_id']
        info = team_info_map.get((team_id, manager_id), {})
        team_display = info.get('display_name', f"Team {team_id}")
        manager_name = info.get('manager_name', '')
        value = row['metric_value_p90']

        is_current = (team_id == current_team_id and manager_id == current_manager_id)

        # Badge color based on rank position
        if rank <= total * 0.25:
            badge_bg = "#28a745"
        elif rank <= total * 0.75:
            badge_bg = "#fd7e14"
        else:
            badge_bg = "#dc3545"

        # Background: yellow for selected, zebra for others
        if is_current:
            bg_color = "#fff3cd"
        elif rank % 2 == 0:
            bg_color = "#f5f5f5"
        else:
            bg_color = "#ffffff"

        name_style = "font-weight:700;" if is_current else ""

        # Use columns: info (clickable) + value
        col_info, col_value, col_btn = st.columns([3.5, 1, 0.5], gap="small")

        with col_info:
            st.markdown(
                f'<div style="background:{bg_color};border-radius:4px;padding:8px 12px;'
                f'display:flex;align-items:center;gap:12px;height:100%;">'
                f'<span style="background:{badge_bg};color:#fff;padding:2px 8px;border-radius:4px;'
                f'font-size:0.85em;font-weight:600;">#{rank}</span>'
                f'<span style="{name_style}">{team_display}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

        with col_value:
            st.markdown(
                f'<div style="background:{bg_color};border-radius:4px;padding:8px 12px;'
                f'text-align:right;height:100%;">'
                f'<span style="font-weight:700;color:#111;">{value:.2f}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

        with col_btn:
            # Don't show button for current team (already viewing)
            if not is_current:
                if st.button("→", key=f"team_rank_{metric_name}_{team_id}_{manager_id}",
                            help=f"Vai a {team_display}"):
                    st.session_state.selected_team = team_id
                    st.session_state.selected_manager = manager_name
                    st.session_state.selected_metric = None  # Reset metric view
                    st.rerun()


def render_all_players_ranking(player_metrics, metric_name, all_player_metrics=None, team_id=None):
    """Render ALL players for a specific metric with clickable rows.

    Filters out players who played less than max_minutes/4 of the top player in the league.
    For rate metrics (collective efficiency), shows explanation instead of player list.

    Args:
        player_metrics: DataFrame with player metrics for current team
        metric_name: Name of the metric to display
        all_player_metrics: DataFrame with all player metrics (for threshold calculation)
        team_id: StatsBomb team_id (for player profile navigation)
    """
    # Check if this metric needs contribution implementation
    if metric_name in METRICS_NEEDING_CONTRIBUTION_IMPL:
        desc = METRICS_NEEDING_CONTRIBUTION_IMPL[metric_name]
        st.info(f"⚙️ **Contributi non ancora implementati**\n\nQuesta metrica potrebbe mostrare: {desc}", icon=":material/construction:")
        return

    metric_data = player_metrics[player_metrics['metric_name'] == metric_name].copy()

    if len(metric_data) == 0:
        st.info("Nessun dato giocatori", icon=":material/info:")
        return

    # Calculate minutes threshold: max_minutes / 4 across ALL players in the league
    if all_player_metrics is not None and 'total_minutes' in all_player_metrics.columns:
        max_minutes_league = all_player_metrics['total_minutes'].max()
    elif 'total_minutes' in metric_data.columns:
        max_minutes_league = metric_data['total_minutes'].max()
    else:
        max_minutes_league = 0

    min_minutes_threshold = max_minutes_league / 4 if max_minutes_league > 0 else 0

    # Filter players by minutes threshold
    filtered_count = 0
    if 'total_minutes' in metric_data.columns and min_minutes_threshold > 0:
        original_count = len(metric_data)
        metric_data = metric_data[metric_data['total_minutes'] >= min_minutes_threshold]
        filtered_count = original_count - len(metric_data)

    if len(metric_data) == 0:
        st.info(f"Nessun giocatore con almeno {int(min_minutes_threshold)} minuti", icon=":material/info:")
        return

    metric_data = metric_data.sort_values('contribution_percentage', ascending=False)

    # Get max contribution for color scaling
    max_contribution = metric_data['contribution_percentage'].max() if len(metric_data) > 0 else 1

    # Store filter info for footer
    filter_info = f"Min. {int(min_minutes_threshold)} minuti ({len(metric_data)} giocatori)"

    # Get ID mappings for player profile navigation
    sb_to_sofa_player = get_sofascore_player_id_map() if team_id else {}
    sofa_team_id = get_sofascore_team_id(team_id) if team_id else None

    # Load SofaScore names mapping for better display names
    sofascore_names = get_sofascore_names_map()

    # Render each player row with clickable button
    for rank, (_, row) in enumerate(metric_data.iterrows(), 1):
        statsbomb_name = row['player_name']
        player_id = row.get('player_id')  # StatsBomb player_id

        # Use SofaScore name if available, otherwise StatsBomb name
        display_name = get_player_display_name(int(player_id), statsbomb_name, sofascore_names) if player_id else statsbomb_name
        surname = extract_surname(display_name) if display_name else 'Unknown'

        contribution = row['contribution_percentage']

        # Calculate color: red (high) → blue (low) gradient
        ratio = contribution / max_contribution if max_contribution > 0 else 0

        # RGB interpolation: red (220, 53, 69) → blue (13, 110, 253)
        r = int(220 - (220 - 13) * (1 - ratio))
        g = int(53 + (110 - 53) * (1 - ratio))
        b = int(69 + (253 - 69) * (1 - ratio))

        bg_color = f"rgba({r}, {g}, {b}, 0.15)"
        border_color = f"rgb({r},{g},{b})"

        # Get SofaScore player_id for navigation
        sofa_player_id = sb_to_sofa_player.get(player_id) if player_id else None

        # Use columns: info + contribution + button
        col_info, col_contrib, col_btn = st.columns([3, 1.2, 0.5], gap="small")

        with col_info:
            st.markdown(
                f'<div style="background:{bg_color};border-left:4px solid {border_color};'
                f'border-radius:4px;padding:8px 12px;display:flex;align-items:center;gap:12px;">'
                f'<span style="color:#666;font-size:0.85em;">#{rank}</span>'
                f'<span style="font-weight:600;">{surname}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

        with col_contrib:
            st.markdown(
                f'<div style="background:{bg_color};border-radius:4px;padding:8px 12px;text-align:right;">'
                f'<span style="font-size:1.3em;font-weight:700;color:#111;">{contribution:.1f}%</span>'
                f'</div>',
                unsafe_allow_html=True
            )

        with col_btn:
            # Show button only if we have valid SofaScore IDs for navigation
            if sofa_player_id and sofa_team_id:
                if st.button("→", key=f"player_rank_{metric_name}_{player_id}",
                            help=f"Vai al profilo di {display_name}"):
                    st.session_state.player_profile_id = sofa_player_id
                    st.session_state.player_profile_team = sofa_team_id
                    st.switch_page("pages/player_profile.py")

    # Footer with filter info
    st.caption(filter_info)


# Metrics that need player contribution implementation
# These could have contributions but aren't implemented yet
# NOTE: Most metrics should have contributions - if showing "Nessun dato giocatori",
# the issue is likely in data generation (need to re-run calculate_metrics script)
METRICS_NEEDING_CONTRIBUTION_IMPL = {
    # Currently empty - all metrics should have contributions implemented
    # If a metric shows no player data, re-run: python scripts/03_calculate_metrics_optimized.py
}


# Tactical descriptions for metrics (strength_desc, weakness_desc)
TACTICAL_DESCRIPTIONS = {
    # Attacking - descrizioni oneste su cosa misurano
    'shots_total': ('tira molto', 'tira poco'),
    'shots_on_target': ('tiri in porta', 'pochi tiri in porta'),
    'xg_total': ('crea pericolo (xG)', 'poco pericoloso (xG)'),
    'goals_scored': ('segna molto', 'segna poco'),
    'goal_conversion_rate': ('efficiente sotto porta', 'spreca occasioni'),
    'big_chances': ('molte occasioni nitide', 'poche occasioni nitide'),
    'touches_in_box': ('presente in area', 'poco presente in area'),

    # Defending - quantità di azioni difensive
    'tackles': ('molti contrasti', 'pochi contrasti'),
    'interceptions': ('molte intercettazioni', 'poche intercettazioni'),
    'clearances': ('molte respinte', 'poche respinte'),
    'blocks': ('molti blocchi', 'pochi blocchi'),
    'aerial_duels_open_play': ('attivo di testa', 'poco attivo di testa'),
    'aerial_duels_set_pieces': ('attivo sui calci piazzati', 'poco attivo sui piazzati'),
    'ground_duels_defensive': ('molti duelli a terra', 'pochi duelli a terra'),

    # Possession - quantità, NON qualità (tranne progressive che è qualitativa)
    'passes_total': ('molti passaggi', 'pochi passaggi'),
    'passes_short': ('molti passaggi corti', 'pochi passaggi corti'),
    'passes_medium': ('molti passaggi medi', 'pochi passaggi medi'),
    'passes_long': ('molti lanci lunghi', 'pochi lanci lunghi'),
    'progressive_passes': ('verticalizza bene', 'fatica a verticalizzare'),  # Questa è qualitativa
    'progressive_carries': ('conduzioni in avanti', 'poche conduzioni'),  # Questa è qualitativa
    'crosses_total': ('crossa molto', 'crossa poco'),
    'dribbles_total': ('dribbla molto', 'dribbla poco'),
    'key_passes': ('passaggi chiave', 'pochi passaggi chiave'),  # Qualitativa
    'through_balls': ('molti filtranti', 'pochi filtranti'),
    'xa_total': ('alto xA', 'basso xA'),  # Expected Assists - qualitativa
    'ball_recoveries': ('recupera palloni', 'pochi recuperi'),
    'switches_of_play': ('cambia gioco', 'pochi cambi di gioco'),
}


def get_tactical_insight(metric_name: str, is_strength_flag: bool) -> str:
    """Get tactical description for a metric."""
    if metric_name in TACTICAL_DESCRIPTIONS:
        strength_desc, weakness_desc = TACTICAL_DESCRIPTIONS[metric_name]
        return strength_desc if is_strength_flag else weakness_desc
    # Fallback: use metric name
    metric_it = METRIC_NAMES_IT.get(metric_name, metric_name.replace('_', ' '))
    return f"buono in {metric_it}" if is_strength_flag else f"debole in {metric_it}"


def render_player_analysis(
    player_metrics_df: pd.DataFrame,
    player_minutes_df: pd.DataFrame,
    team_id: int,
    manager_id: int,
    player_id_to_slot: dict,
    player_names: dict,
    formation: str = "4-3-3"
):
    """
    Render the player analysis section with AI-generated tactical profiles.
    Uses OpenRouter AI to determine player archetype and description.
    """
    from services.player_analysis import RoleGrouping
    from services.ai_insights import generate_tactical_profile, generate_fallback_profile
    from config import FORMATION_COORDINATES

    # Position mapping: English abbreviation -> Italian
    POSITION_IT = {
        "GK": "Portiere",
        "RB": "Terzino Destro",
        "LB": "Terzino Sinistro",
        "CB": "Difensore Centrale",
        "RWB": "Esterno Destro",
        "LWB": "Esterno Sinistro",
        "CDM": "Mediano",
        "CM": "Centrocampista",
        "CAM": "Trequartista",
        "RAM": "Trequartista Destro",
        "LAM": "Trequartista Sinistro",
        "RM": "Esterno Destro",
        "LM": "Esterno Sinistro",
        "RW": "Ala Destra",
        "LW": "Ala Sinistra",
        "ST": "Punta",
        "CF": "Centravanti",
    }

    # Check data
    if player_metrics_df is None or player_minutes_df is None:
        st.info("Dati giocatori non disponibili")
        return

    # Load team playing style from clustering (uses Supabase data)
    team_style = None
    try:
        style_info = get_team_playing_style(team_id, manager_id)
        if style_info:
            team_style = style_info.get('cluster_name')
    except Exception:
        pass  # If we can't load style, proceed without it

    # Create analyzer
    try:
        analyzer = PlayerAnalyzer(
            player_metrics_df=player_metrics_df,
            player_minutes_df=player_minutes_df,
            min_minutes=270
        )
    except Exception:
        st.warning("Errore nell'analisi")
        return

    formation_player_ids = list(player_id_to_slot.keys())
    if not formation_player_ids:
        st.info("Nessun giocatore nella formazione")
        return

    # Get formation coordinates for position names
    coords = FORMATION_COORDINATES.get(formation, FORMATION_COORDINATES.get("4-3-3", {}))

    # PHASE 1: Collect all player data first
    players_data = []
    TEAM_DEPENDENT = {'passes_total', 'passes_short', 'passes_medium', 'passes_long', 'ball_recoveries', 'touches_in_box'}

    for player_id in formation_player_ids:
        player_role = analyzer.get_player_role(player_id)
        if player_role is None:
            continue

        position_name, role = player_role
        slot = player_id_to_slot.get(player_id)
        surname = player_names.get(slot, "Unknown")

        # Get position from formation coordinates
        slot_info = coords.get(slot, {})
        formation_position = slot_info.get("position", position_name)
        position_it = POSITION_IT.get(formation_position, formation_position)

        analysis = analyzer.calculate_player_z_scores(player_id, team_id, manager_id)

        if analysis is None:
            continue

        # Filter team-dependent metrics for fallback
        filtered_strengths = [s for s in analysis.strengths if s.metric_name not in TEAM_DEPENDENT]
        filtered_weaknesses = [w for w in analysis.weaknesses if w.metric_name not in TEAM_DEPENDENT]

        players_data.append({
            'surname': surname,
            'position_it': position_it,
            'analysis': analysis,
            'filtered_strengths': filtered_strengths,
            'filtered_weaknesses': filtered_weaknesses,
        })

    if not players_data:
        st.info("Nessun giocatore con dati sufficienti")
        return

    # Cache key for storing results
    cache_key = (team_id, manager_id, tuple(sorted(player_id_to_slot.items())))

    # Initialize cache if not present
    if 'cached_player_profiles' not in st.session_state:
        st.session_state.cached_player_profiles = {}

    # PHASE 2: Generate and render each player PROGRESSIVELY (one by one)
    # Each card appears as soon as its AI profile is generated
    # Use st.status() to show spinner while generating, with progressive content

    # List to store generated profiles for caching
    generated_profiles = []

    with st.status("⏳ Generazione analisi giocatori...", expanded=True) as status:
        for i, player in enumerate(players_data):
            # Generate AI profile for this player
            profile = generate_tactical_profile(
                player_name=player['surname'],
                role_name_it=player['position_it'],
                all_z_scores=player['analysis'].all_z_scores,
                team_style=team_style
            )

            # Fallback if AI unavailable
            if profile is None:
                profile = generate_fallback_profile(
                    player_name=player['surname'],
                    role_name_it=player['position_it'],
                    strengths=player['filtered_strengths'],
                    weaknesses=player['filtered_weaknesses'],
                    all_z_scores=player['analysis'].all_z_scores
                )

            # Store for caching
            generated_profiles.append({
                'surname': player['surname'],
                'position_it': player['position_it'],
                'archetype': profile.archetype,
                'description': profile.description,
            })

            # Render this player's card IMMEDIATELY inside status
            with st.container(border=True):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"### {player['surname']}")
                with col2:
                    st.markdown(
                        f"<p style='text-align:right;margin:0;padding-top:8px;'>"
                        f"<span style='color:#6b7280;font-size:0.85rem;'>{player['position_it']}</span> · "
                        f"<span style='font-weight:600;font-size:0.85rem;'>{profile.archetype}</span>"
                        f"</p>",
                        unsafe_allow_html=True
                    )

                st.markdown(f"<p style='font-size:0.9rem;color:#374151;margin:0;'>{profile.description}</p>", unsafe_allow_html=True)

        # Mark as complete when all players are done
        status.update(label="✅ Analisi completata", state="complete", expanded=True)

    # Cache the generated profiles for future use
    st.session_state.cached_player_profiles[cache_key] = generated_profiles
