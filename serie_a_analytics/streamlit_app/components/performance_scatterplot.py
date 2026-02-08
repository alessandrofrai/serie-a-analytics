"""
Performance Scatterplot Component

Visualizes team+manager performances using a scatterplot with:
- X axis: xG - xGA (attacking dominance)
- Y axis: Field Tilt difference (territorial control)
- 4 quadrants showing performance types
- Color by match result (W/D/L)
- Filters for Home/Away and opponent cluster

Uses Plotly for interactive visualization.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Optional, List, Tuple

# Result colors
RESULT_COLORS = {
    'W': '#10b981',  # Green - Win
    'D': '#9ca3af',  # Gray - Draw
    'L': '#ef4444',  # Red - Loss
}

RESULT_LABELS = {
    'W': 'Vittoria',
    'D': 'Pareggio',
    'L': 'Sconfitta',
}

# Quadrant definitions
QUADRANTS = {
    'Q1': {
        'name': 'Prestazione Positiva',
        'color': 'rgba(16, 185, 129, 0.15)',  # Green tint
        'desc': 'Dominio xG e territorio',
        'x_positive': True,
        'y_positive': True,
    },
    'Q2': {
        'name': 'Dominio Sterile',
        'color': 'rgba(251, 191, 36, 0.15)',  # Yellow tint
        'desc': 'Campo ma poche occasioni',
        'x_positive': False,
        'y_positive': True,
    },
    'Q3': {
        'name': 'Prestazione Negativa',
        'color': 'rgba(239, 68, 68, 0.15)',  # Red tint
        'desc': 'Subisce su entrambi i fronti',
        'x_positive': False,
        'y_positive': False,
    },
    'Q4': {
        'name': 'Pragmatismo',
        'color': 'rgba(59, 130, 246, 0.15)',  # Blue tint
        'desc': 'Occasioni senza dominio territoriale',
        'x_positive': True,
        'y_positive': False,
    },
}

# Cluster names
CLUSTER_NAMES = {
    0: 'Possesso Dominante',
    1: 'Pressing e Verticalita',
    2: 'Blocco Basso e Ripartenza',
    3: 'Ampiezza e Inserimenti',
    -1: 'Non Definito',
}


@st.fragment
def render_performance_section(
    performances_df: pd.DataFrame,
    team_id: int,
    manager_id: int,
    team_name: str,
    valid_pairs: set = None,
):
    """
    Render complete performance section with filters, score card, and scatterplot.

    Args:
        performances_df: DataFrame with match performances
        team_id: Team ID
        manager_id: Manager ID
        team_name: Team name for display
        valid_pairs: Set of valid (team_id, manager_id) tuples from dashboard
    """
    st.markdown("### :material/scatter_plot: Mappa Prestazioni")

    # Filters row
    filter_home, filter_clusters = render_scatterplot_filters(
        performances_df, team_id, manager_id
    )

    # Two columns: score card + scatterplot
    col_score, col_scatter = st.columns([1, 2.5])

    with col_score:
        render_performance_score_card(
            performances_df, team_id, manager_id, valid_pairs
        )

    with col_scatter:
        render_performance_scatterplot(
            performances_df,
            team_id,
            manager_id,
            filter_home=filter_home,
            filter_clusters=filter_clusters,
            height=380
        )


def render_scatterplot_filters(
    performances_df: pd.DataFrame,
    team_id: int,
    manager_id: int,
) -> Tuple[Optional[bool], Optional[List[int]]]:
    """
    Render filters for the scatterplot.

    Returns:
        Tuple of (filter_home, filter_clusters)
    """
    # CSS per colorare i tag selezionati nel multiselect con i colori del brand
    st.markdown("""
        <style>
        /* Multiselect selected tags - brand colors */
        span[data-baseweb="tag"],
        span[data-baseweb="tag"]:hover {
            background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%) !important;
            background-color: #1e3a5f !important;
            border: none !important;
        }
        span[data-baseweb="tag"] span {
            color: white !important;
        }
        span[data-baseweb="tag"] svg,
        span[data-baseweb="tag"]:hover svg {
            fill: rgba(255, 255, 255, 0.8) !important;
        }
        /* Alternative selector for Streamlit multiselect pills */
        .stMultiSelect [data-baseweb="tag"],
        .stMultiSelect [data-baseweb="tag"]:hover {
            background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%) !important;
            background-color: #1e3a5f !important;
        }
        .stMultiSelect [data-baseweb="tag"] span {
            color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        home_options = ["Tutte", "Solo Casa", "Solo Trasferta"]
        home_option = st.selectbox(
            "Partite",
            options=home_options,
            key=f"scatter_home_filter_{team_id}_{manager_id}",
            label_visibility="collapsed"
        )

        filter_home = None
        if home_option == "Solo Casa":
            filter_home = True
        elif home_option == "Solo Trasferta":
            filter_home = False

    with col2:
        # Get available opponent clusters for this team+manager
        team_df = performances_df[
            (performances_df['team_id'] == team_id) &
            (performances_df['manager_id'] == manager_id)
        ]

        available_clusters = team_df['opponent_cluster_id'].dropna().unique()
        cluster_options = []
        for cid in sorted(available_clusters):
            cluster_name = CLUSTER_NAMES.get(int(cid), f"Cluster {int(cid)}")
            cluster_options.append(cluster_name)

        selected_options = st.multiselect(
            "Stile Avversario",
            options=cluster_options,
            default=[],  # Vuoto = tutti gli stili (sottointeso)
            key=f"scatter_cluster_filter_{team_id}_{manager_id}",
            label_visibility="collapsed",
            placeholder="Tutti gli stili"
        )

        # Se la lista e' vuota, non filtrare (mostra tutti)
        filter_clusters = None
        if selected_options:
            # Convert names back to IDs
            name_to_id = {v: k for k, v in CLUSTER_NAMES.items()}
            filter_clusters = [name_to_id.get(name, -1) for name in selected_options]

    return filter_home, filter_clusters


def render_performance_scatterplot(
    performances_df: pd.DataFrame,
    team_id: int,
    manager_id: int,
    height: int = 400,
    show_quadrants: bool = True,
    filter_home: Optional[bool] = None,
    filter_clusters: Optional[List[int]] = None,
):
    """
    Render the performance scatterplot with Plotly.

    Args:
        performances_df: DataFrame with match performances
        team_id: Team ID to display
        manager_id: Manager ID to display
        height: Chart height in pixels
        show_quadrants: Show quadrant background colors
        filter_home: Filter by home/away (None=all, True=home, False=away)
        filter_clusters: List of opponent cluster IDs to filter
    """
    # Filter data for this team+manager
    df = performances_df[
        (performances_df['team_id'] == team_id) &
        (performances_df['manager_id'] == manager_id)
    ].copy()

    # Apply filters
    if filter_home is not None:
        df = df[df['is_home'] == filter_home]

    if filter_clusters:
        df = df[df['opponent_cluster_id'].isin(filter_clusters)]

    if len(df) == 0:
        st.info("Nessuna partita con i filtri selezionati")
        return

    # Create figure
    fig = go.Figure()

    # Calculate axis ranges for quadrants
    x_abs_max = max(abs(df['xg_diff'].min()), abs(df['xg_diff'].max()), 0.5) * 1.3
    y_abs_max = max(abs(df['field_tilt_diff'].min()), abs(df['field_tilt_diff'].max()), 5) * 1.3

    # Add quadrant backgrounds
    if show_quadrants:
        _add_quadrant_backgrounds(fig, x_abs_max, y_abs_max)

    # Add axis lines at 0
    fig.add_hline(y=0, line_dash="dash", line_color="#6b7280", line_width=1.5, opacity=0.7)
    fig.add_vline(x=0, line_dash="dash", line_color="#6b7280", line_width=1.5, opacity=0.7)

    # Add scatter points for each result type
    for result in ['W', 'D', 'L']:
        result_df = df[df['result'] == result]
        if len(result_df) == 0:
            continue

        # Prepare hover text
        hover_texts = []
        for _, row in result_df.iterrows():
            venue = "Casa" if row['is_home'] else "Trasferta"
            opponent_manager = row.get('opponent_manager', '')
            opponent_manager_text = f" ({opponent_manager})" if opponent_manager else ""
            hover_texts.append(
                f"<b>vs {row['opponent_name']}</b>{opponent_manager_text} (G{int(row['match_week'])})<br>"
                f"xG: {row['xg_for']:.2f} - {row['xg_against']:.2f}<br>"
                f"Field Tilt: {row['field_tilt']:.1f}%<br>"
                f"Risultato: {int(row['goals_for'])}-{int(row['goals_against'])}<br>"
                f"{venue}"
            )

        fig.add_trace(go.Scatter(
            x=result_df['xg_diff'],
            y=result_df['field_tilt_diff'],
            mode='markers',
            name=RESULT_LABELS[result],
            marker=dict(
                size=14,
                color=RESULT_COLORS[result],
                line=dict(width=2, color='white'),
                opacity=0.9,
            ),
            text=hover_texts,
            hovertemplate='%{text}<extra></extra>',
        ))

    # Update layout
    fig.update_layout(
        height=height,
        xaxis=dict(
            title="xG - xGA",
            range=[-x_abs_max, x_abs_max],
            zeroline=False,
            gridcolor='rgba(156, 163, 175, 0.2)',
            tickformat=".1f",
        ),
        yaxis=dict(
            title="Diff. Field Tilt",
            range=[-y_abs_max, y_abs_max],
            zeroline=False,
            gridcolor='rgba(156, 163, 175, 0.2)',
            tickformat=".0f",
            ticksuffix="%",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=11),
        ),
        margin=dict(l=50, r=20, t=40, b=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="system-ui",
        ),
    )

    # Add quadrant labels
    _add_quadrant_labels(fig, x_abs_max, y_abs_max)

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def _add_quadrant_backgrounds(fig, x_range: float, y_range: float):
    """Add colored backgrounds for quadrants."""
    # Q1: Top-right (+xG, +Tilt)
    fig.add_shape(
        type="rect", x0=0, x1=x_range, y0=0, y1=y_range,
        fillcolor=QUADRANTS['Q1']['color'], line_width=0, layer="below"
    )
    # Q2: Top-left (-xG, +Tilt)
    fig.add_shape(
        type="rect", x0=-x_range, x1=0, y0=0, y1=y_range,
        fillcolor=QUADRANTS['Q2']['color'], line_width=0, layer="below"
    )
    # Q3: Bottom-left (-xG, -Tilt)
    fig.add_shape(
        type="rect", x0=-x_range, x1=0, y0=-y_range, y1=0,
        fillcolor=QUADRANTS['Q3']['color'], line_width=0, layer="below"
    )
    # Q4: Bottom-right (+xG, -Tilt)
    fig.add_shape(
        type="rect", x0=0, x1=x_range, y0=-y_range, y1=0,
        fillcolor=QUADRANTS['Q4']['color'], line_width=0, layer="below"
    )


def _add_quadrant_labels(fig, x_range: float, y_range: float):
    """Add labels for each quadrant."""
    label_offset_x = x_range * 0.7
    label_offset_y = y_range * 0.85

    labels = [
        (label_offset_x, label_offset_y, QUADRANTS['Q1']['name']),
        (-label_offset_x, label_offset_y, QUADRANTS['Q2']['name']),
        (-label_offset_x, -label_offset_y, QUADRANTS['Q3']['name']),
        (label_offset_x, -label_offset_y, QUADRANTS['Q4']['name']),
    ]

    for x, y, text in labels:
        fig.add_annotation(
            x=x, y=y, text=text,
            showarrow=False,
            font=dict(size=9, color='#6b7280'),
            opacity=0.6,
        )


def render_performance_score_card(
    performances_df: pd.DataFrame,
    team_id: int,
    manager_id: int,
    valid_pairs: set = None,
):
    """
    Render the Performance Score card with stats.

    Shows:
    - Average performance score
    - Home vs Away split
    - Comparative evaluation vs other managers
    - Key metrics (xG diff, field tilt)
    """
    # Filter for this team+manager
    team_df = performances_df[
        (performances_df['team_id'] == team_id) &
        (performances_df['manager_id'] == manager_id)
    ]

    if len(team_df) == 0:
        st.warning("Nessun dato disponibile")
        return

    # Calculate scores
    avg_score = team_df['performance_score'].mean()
    home_df = team_df[team_df['is_home'] == True]
    away_df = team_df[team_df['is_home'] == False]

    home_score = home_df['performance_score'].mean() if len(home_df) > 0 else 0
    away_score = away_df['performance_score'].mean() if len(away_df) > 0 else 0

    # Calculate z-score vs all team-managers (using valid_pairs from dashboard)
    if valid_pairs:
        # Use the exact same combinations as the dashboard
        valid_df = performances_df[
            performances_df.apply(
                lambda r: (r['team_id'], r['manager_id']) in valid_pairs, axis=1
            )
        ]
    else:
        # Fallback: filter by MIN_MATCHES
        MIN_MATCHES = 5
        match_counts = performances_df.groupby(['team_id', 'manager_id']).size()
        valid_combinations = match_counts[match_counts >= MIN_MATCHES].index
        valid_df = performances_df[
            performances_df.set_index(['team_id', 'manager_id']).index.isin(valid_combinations)
        ]

    all_avgs = valid_df.groupby(['team_id', 'manager_id'])['performance_score'].mean()

    league_mean = all_avgs.mean()
    league_std = all_avgs.std()

    if league_std > 0:
        z_score = (avg_score - league_mean) / league_std
    else:
        z_score = 0

    # Calculate ranking position
    all_avgs_sorted = all_avgs.sort_values(ascending=False)
    total_managers = len(all_avgs_sorted)
    rank = 1
    for (t_id, m_id), _ in all_avgs_sorted.items():
        if t_id == team_id and m_id == manager_id:
            break
        rank += 1

    # Determine z-score color and label
    if z_score > 0.5:
        z_color = '#10b981'  # Green
        z_label = 'Sopra media'
    elif z_score < -0.5:
        z_color = '#ef4444'  # Red
        z_label = 'Sotto media'
    else:
        z_color = '#f59e0b'  # Orange
        z_label = 'Nella media'

    z_sign = '+' if z_score > 0 else ''

    # Results breakdown
    wins = len(team_df[team_df['result'] == 'W'])
    draws = len(team_df[team_df['result'] == 'D'])
    losses = len(team_df[team_df['result'] == 'L'])
    total = len(team_df)
    win_pct = (wins / total * 100) if total > 0 else 0

    # Key metrics averages
    avg_xg_diff = team_df['xg_diff'].mean()
    avg_tilt_diff = team_df['field_tilt_diff'].mean()

    # xG diff color
    xg_color = '#10b981' if avg_xg_diff > 0 else '#ef4444' if avg_xg_diff < 0 else '#9ca3af'
    xg_sign = '+' if avg_xg_diff > 0 else ''

    # Tilt diff color
    tilt_color = '#10b981' if avg_tilt_diff > 0 else '#ef4444' if avg_tilt_diff < 0 else '#9ca3af'
    tilt_sign = '+' if avg_tilt_diff > 0 else ''

    # Tooltip CSS + info icon
    tooltip_style = '''<style>.perf-card-container{position:relative;}.perf-info-icon{position:absolute;top:12px;left:12px;width:20px;height:20px;border-radius:50%;background:#6b7280;color:white;font-size:12px;font-weight:700;display:flex;align-items:center;justify-content:center;cursor:help;font-style:italic;z-index:10;}.perf-info-icon:hover{background:#9ca3af;}.perf-tooltip{display:none;position:absolute;top:38px;left:8px;width:300px;padding:14px;background:#0f172a;color:white;font-size:0.75rem;line-height:1.5;border-radius:10px;z-index:100;box-shadow:0 6px 20px rgba(0,0,0,0.5);}.perf-info-icon:hover+.perf-tooltip,.perf-tooltip:hover{display:block;}.perf-tooltip-title{font-weight:700;margin-bottom:8px;font-size:0.85rem;color:#f1f5f9;}.perf-tooltip-section{margin-bottom:10px;}.perf-tooltip-label{font-weight:600;color:#60a5fa;margin-bottom:3px;}.perf-tooltip-desc{color:#cbd5e1;}.perf-tooltip-formula{background:#1e293b;padding:8px 10px;border-radius:6px;font-family:monospace;font-size:0.72rem;color:#e2e8f0;margin:6px 0;}.perf-tooltip-example{background:#1e3a5f;padding:10px;border-radius:6px;margin-top:8px;border-left:3px solid #3b82f6;}</style>'''

    # Tooltip content focused on calculation process with example
    tooltip_html = '''<div class="perf-info-icon">i</div><div class="perf-tooltip"><div class="perf-tooltip-title">📊 Come è calcolato</div><div class="perf-tooltip-section"><div class="perf-tooltip-desc">Per <b>ogni partita</b> si calcola uno score (0-100). Il valore mostrato è la <b>media</b> di tutte le partite gestite.</div></div><div class="perf-tooltip-section"><div class="perf-tooltip-label">Formula singola partita:</div><div class="perf-tooltip-formula">(xG_diff × 0.45 + Tilt_diff × 0.35 + Risultato × 0.20) × 100</div><div class="perf-tooltip-desc" style="font-size:0.7rem;color:#9ca3af;">• xG_diff e Tilt_diff normalizzati 0-1 sul campionato<br/>• Risultato: Vittoria=1 | Pareggio=0.5 | Sconfitta=0</div></div><div class="perf-tooltip-example"><div class="perf-tooltip-label" style="font-size:0.72rem;">📝 Esempio:</div><div class="perf-tooltip-desc" style="font-size:0.7rem;">Partita con xG_norm=0.75, Tilt_norm=0.60, Vittoria:<br/><span style="color:#60a5fa;">(0.75×0.45 + 0.60×0.35 + 1.0×0.20) × 100</span><br/>= (0.34 + 0.21 + 0.20) × 100 = <b style="color:#10b981;">75.0</b></div></div><div class="perf-tooltip-desc" style="font-size:0.68rem;color:#94a3b8;margin-top:8px;">→ Score finale = media di tutti gli score partita</div></div>'''

    # Render card - HTML su una sola riga per evitare problemi di rendering
    card_html = f'''{tooltip_style}<div class="perf-card-container" style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); border-radius: 12px; padding: 20px 16px; color: white; min-height: 340px;">{tooltip_html}<div style="text-align: center; margin-bottom: 16px;"><div style="font-size: 2.2rem; font-weight: 700;">{avg_score:.1f}</div><div style="font-size: 0.75rem; color: #94a3b8;">Performance Score</div></div><div style="display: flex; justify-content: space-around; gap: 8px; margin-bottom: 16px;"><div style="text-align: center;"><div style="font-size: 0.7rem; color: #94a3b8;">Casa</div><div style="font-size: 1.1rem; font-weight: 600;">{home_score:.1f}</div></div><div style="text-align: center;"><div style="font-size: 0.7rem; color: #94a3b8;">Trasferta</div><div style="font-size: 1.1rem; font-weight: 600;">{away_score:.1f}</div></div></div><div style="padding: 12px 0; border-top: 1px solid #475569; border-bottom: 1px solid #475569; margin-bottom: 12px;"><div style="text-align: center; margin-bottom: 8px;"><div style="font-size: 0.65rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Valutazione Comparativa</div></div><div style="display: flex; justify-content: space-around; align-items: center;"><div style="text-align: center;"><div style="font-size: 1.3rem; font-weight: 700; color: {z_color};">{z_sign}{z_score:.2f}</div><div style="font-size: 0.6rem; color: #64748b;">{z_label}</div></div><div style="text-align: center;"><div style="font-size: 1.3rem; font-weight: 700; color: #e2e8f0;">{rank}°</div><div style="font-size: 0.6rem; color: #64748b;">su {total_managers}</div></div></div></div><div style="display: flex; justify-content: space-around; gap: 8px; margin-bottom: 12px;"><div style="text-align: center;"><div style="font-size: 0.65rem; color: #64748b;">xG Diff</div><div style="font-size: 0.95rem; font-weight: 600; color: {xg_color};">{xg_sign}{avg_xg_diff:.2f}</div></div><div style="text-align: center;"><div style="font-size: 0.65rem; color: #64748b;">Tilt Diff</div><div style="font-size: 0.95rem; font-weight: 600; color: {tilt_color};">{tilt_sign}{avg_tilt_diff:.1f}%</div></div><div style="text-align: center;"><div style="font-size: 0.65rem; color: #64748b;">Win %</div><div style="font-size: 0.95rem; font-weight: 600;">{win_pct:.0f}%</div></div></div><div style="display: flex; justify-content: center; gap: 12px; font-size: 0.75rem; padding-top: 8px;"><span style="color: #10b981; font-weight: 600;">{wins}V</span><span style="color: #9ca3af; font-weight: 600;">{draws}N</span><span style="color: #ef4444; font-weight: 600;">{losses}P</span><span style="color: #64748b;">({total})</span></div></div>'''
    st.markdown(card_html, unsafe_allow_html=True)
