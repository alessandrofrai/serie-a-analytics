"""
Strengths & Weaknesses Analysis Component

Visualizes team strengths and weaknesses based on metric rankings.
Designed for creating reports that highlight what a team does well and poorly.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Tuple

from utils.data_helpers import (
    get_sofascore_names_map,
    get_player_display_name,
    extract_surname
)


# Metric display names in Italian
METRIC_DISPLAY = {
    # Attacking
    'shots_total': ('Tiri Totali', '⚽'),
    'shots_on_target': ('Tiri in Porta', '🎯'),
    'xg_total': ('Expected Goals (xG)', '📊'),
    'xg_open_play': ('xG Gioco Aperto', '⚽'),
    'goals_scored': ('Gol Segnati', '🥅'),
    'goal_conversion_rate': ('% Conversione Gol', '📈'),
    'goal_conversion_sot': ('% Conversione SOT', '🎯'),
    'big_chances': ('Grandi Occasioni', '💎'),
    'big_chances_conversion': ('% Conv. Grandi Occ.', '💯'),
    'xg_goals_difference': ('Gol - xG (Over/Under)', '📊'),
    'shots_per_box_touch': ('Tiri per Tocco in Area', '📐'),
    'touches_in_box': ('Tocchi in Area', '🦶'),

    # Defending
    'tackles': ('Contrasti Vinti', '🦵'),
    'interceptions': ('Intercetti', '🖐️'),
    'clearances': ('Respinte', '🧹'),
    'blocks': ('Blocchi', '🧱'),
    'aerial_duels_open_play': ('Duelli Aerei (Gioco)', '✈️'),
    'aerial_duels_set_pieces': ('Duelli Aerei (Inattive)', '📐'),
    'ground_duels_offensive': ('Duelli Terra (Off.)', '⚔️'),
    'ground_duels_defensive': ('Duelli Terra (Dif.)', '🛡️'),
    'fouls_committed': ('Falli Commessi', '⚠️'),
    'yellow_cards': ('Cartellini Gialli', '🟨'),
    'red_cards': ('Cartellini Rossi', '🟥'),

    # Possession
    'possession_percentage': ('% Possesso', '⚽'),
    'passes_total': ('Passaggi Completati', '📨'),
    'passes_short': ('Passaggi Corti', '📨'),
    'passes_medium': ('Passaggi Medi', '📨'),
    'passes_long': ('Passaggi Lunghi', '📨'),
    'progressive_passes': ('Passaggi Progressivi', '⬆️'),
    'progressive_carries': ('Conduzioni Progressive', '🏃'),
    'crosses_total': ('Cross Riusciti', '↗️'),
    'dribbles_total': ('Dribbling Riusciti', '💨'),
    'key_passes': ('Passaggi Chiave', '🔑'),
    'through_balls': ('Filtranti', '🎯'),
    'switches_of_play': ('Cambi Gioco', '↔️'),
    'xa_total': ('Expected Assists (xA)', '🅰️'),
    'xa_per_key_pass': ('xA per Key Pass', '📊'),
    'goals_per_xa': ('Gol per xA', '📈'),
    'ball_recoveries': ('Recuperi Palla', '🔄'),

    # Transition
    'buildup_sequences': ('Sequenze Build-up', '🔄'),
    'buildup_xg': ('xG da Build-up', '📊'),
    'transition_z2_sequences': ('Transizioni Zona 2', '⚡'),
    'transition_z2_xg': ('xG da Zona 2', '📊'),
    'transition_z3_sequences': ('Transizioni Zona 3', '⚡'),
    'transition_z3_xg': ('xG da Zona 3', '📊'),
    'counter_attacks': ('Contropiedi', '💨'),
    'fast_attacks': ('Attacchi Rapidi', '⚡'),
    'sot_from_counters': ('SOT da Contropiedi', '🎯'),
    'sot_from_fast_attacks': ('SOT da Attacchi Rapidi', '🎯'),
    'sot_per_recovery_z2': ('SOT per Recupero Z2', '📊'),
    'sot_per_recovery_z3': ('SOT per Recupero Z3', '📊'),

    # Set pieces
    'penalties_taken': ('Rigori Calciati', '🥅'),
    'direct_free_kicks': ('Punizioni Dirette', '⚽'),
    'xg_direct_set_pieces': ('xG Palle Inattive Dirette', '📊'),
    'corners_taken': ('Calci d\'Angolo', '📐'),
    'indirect_free_kicks': ('Punizioni Indirette', '📐'),
    'throw_ins': ('Rimesse Laterali', '🤲'),
    'xg_indirect_set_pieces': ('xG Palle Inattive Ind.', '📊'),
    'xg_indirect_set_pieces_conceded': ('xG Subito da Inattive', '⚠️'),
    'sot_per_100_corners': ('SOT per 100 Corner', '📊'),
    'sot_per_100_indirect_sp': ('SOT per 100 Inattive', '📊'),

    # Pressing
    'ppda': ('PPDA (Passes per Def. Action)', '📊'),
    'high_press_recoveries': ('Recuperi Pressing Alto', '⬆️'),
    'counterpressing_recoveries': ('Recuperi Gegenpressing', '🔄'),
    'pressing_sequences': ('Sequenze Pressing', '💨'),

    # Shot Analysis - Attacking
    'shots_direct_sp': ('Tiri da Inattive Dirette', '⚽'),
    'shots_indirect_sp': ('Tiri da Inattive Indirette', '📐'),
    'shots_transition': ('Tiri da Transizione', '⚡'),
    'shots_cross': ('Tiri da Cross', '↗️'),
    'shots_long_range': ('Tiri da Fuori Area', '🎯'),
    'shots_buildup': ('Tiri da Build-up', '🔄'),
    'xg_direct_sp': ('xG da Inattive Dirette', '📊'),
    'xg_indirect_sp': ('xG da Inattive Indirette', '📊'),
    'xg_transition': ('xG da Transizione', '📊'),
    'xg_cross': ('xG da Cross', '📊'),
    'xg_long_range': ('xG da Fuori Area', '📊'),
    'xg_buildup': ('xG da Build-up', '📊'),
    'shots_made_total': ('Tiri Effettuati Totali', '⚽'),

    # Shot Analysis - Defending (Conceded)
    'shots_conceded_direct_sp': ('Tiri Subiti da Inattive Dir.', '⚠️'),
    'shots_conceded_indirect_sp': ('Tiri Subiti da Inattive Ind.', '⚠️'),
    'shots_conceded_transition': ('Tiri Subiti da Transizione', '⚠️'),
    'shots_conceded_cross': ('Tiri Subiti da Cross', '⚠️'),
    'shots_conceded_long_range': ('Tiri Subiti da Fuori Area', '⚠️'),
    'shots_conceded_buildup': ('Tiri Subiti da Build-up', '⚠️'),
    'xg_conceded_direct_sp': ('xG Subito da Inattive Dir.', '📊'),
    'xg_conceded_indirect_sp': ('xG Subito da Inattive Ind.', '📊'),
    'xg_conceded_transition': ('xG Subito da Transizione', '📊'),
    'xg_conceded_cross': ('xG Subito da Cross', '📊'),
    'xg_conceded_long_range': ('xG Subito da Fuori Area', '📊'),
    'xg_conceded_buildup': ('xG Subito da Build-up', '📊'),
    'shots_conceded_total': ('Tiri Subiti Totali', '⚠️'),
}

# Metrics where LOWER is better (invert ranking)
LOWER_IS_BETTER = {
    'fouls_committed', 'yellow_cards', 'red_cards',
    'xg_indirect_set_pieces_conceded', 'ppda',
    # Shot Analysis - conceded metrics (fewer shots conceded = better)
    'shots_conceded_direct_sp', 'shots_conceded_indirect_sp', 'shots_conceded_transition',
    'shots_conceded_cross', 'shots_conceded_long_range', 'shots_conceded_buildup',
    'xg_conceded_direct_sp', 'xg_conceded_indirect_sp', 'xg_conceded_transition',
    'xg_conceded_cross', 'xg_conceded_long_range', 'xg_conceded_buildup',
    'shots_conceded_total',
}

# Category grouping for analysis
CATEGORY_LABELS = {
    'attacking': '⚔️ ATTACCO',
    'defending': '🛡️ DIFESA',
    'possession': '🎮 POSSESSO & CREAZIONE',
    'transition': '⚡ TRANSIZIONI',
    'set_pieces': '📐 PALLE INATTIVE',
    'pressing': '💨 PRESSING',
    'shot_analysis': '🎯 ANALISI TIRI',
}


def classify_metrics(metrics_df: pd.DataFrame, percentile_threshold: float = 75) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Classify metrics into strengths, weaknesses, and neutral.

    Args:
        metrics_df: Team metrics DataFrame
        percentile_threshold: Threshold for strength/weakness (default 75 = top/bottom 25%)

    Returns:
        Tuple of (strengths_df, weaknesses_df, neutral_df)
    """
    if len(metrics_df) == 0:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    metrics_with_class = metrics_df.copy()

    # Adjust percentile for "lower is better" metrics
    def get_effective_percentile(row):
        if row['metric_name'] in LOWER_IS_BETTER:
            # For "lower is better", invert the percentile
            return 100 - row['percentile']
        return row['percentile']

    metrics_with_class['effective_percentile'] = metrics_with_class.apply(get_effective_percentile, axis=1)

    # Classify
    strengths = metrics_with_class[metrics_with_class['effective_percentile'] >= percentile_threshold]
    weaknesses = metrics_with_class[metrics_with_class['effective_percentile'] <= (100 - percentile_threshold)]
    neutral = metrics_with_class[
        (metrics_with_class['effective_percentile'] > (100 - percentile_threshold)) &
        (metrics_with_class['effective_percentile'] < percentile_threshold)
    ]

    return strengths, weaknesses, neutral


def render_metric_badge(metric: pd.Series, is_strength: bool = True):
    """Render a metric as a colored badge."""
    name = metric['metric_name']
    display_info = METRIC_DISPLAY.get(name, (name.replace('_', ' ').title(), '📊'))
    display_name, emoji = display_info

    value = metric['metric_value_p90']
    rank = int(metric.get('metric_rank', 0))
    total = int(metric.get('total_teams', 36))
    percentile = metric.get('percentile', 50)

    # Format value
    if abs(value) >= 100:
        value_str = f"{value:.0f}"
    elif abs(value) >= 10:
        value_str = f"{value:.1f}"
    else:
        value_str = f"{value:.2f}"

    # Color based on strength/weakness
    if is_strength:
        bg_color = "#d4edda"  # Light green
        border_color = "#28a745"  # Green
        text_color = "#155724"
    else:
        bg_color = "#f8d7da"  # Light red
        border_color = "#dc3545"  # Red
        text_color = "#721c24"

    st.markdown(f"""
    <div style="
        background: {bg_color};
        border: 2px solid {border_color};
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: bold; color: {text_color};">
                {emoji} {display_name}
            </span>
            <span style="
                background: {border_color};
                color: white;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 0.8rem;
            ">
                #{rank}/{total}
            </span>
        </div>
        <div style="margin-top: 8px; font-size: 1.2rem; font-weight: bold; color: {text_color};">
            {value_str} <span style="font-size: 0.8rem; font-weight: normal;">p90</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_strengths_weaknesses_panel(metrics_df: pd.DataFrame, team_name: str):
    """
    Render the strengths and weaknesses analysis panel.

    Args:
        metrics_df: Team metrics DataFrame
        team_name: Team name for display
    """
    if len(metrics_df) == 0:
        st.warning("Nessuna metrica disponibile per l'analisi")
        return

    # Classify metrics
    strengths, weaknesses, neutral = classify_metrics(metrics_df)

    # Summary header
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1a472a 0%, #2d5a3f 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        text-align: center;
    ">
        <h2 style="margin: 0; color: white;">📋 Report Analisi: {team_name}</h2>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">
            Punti di forza: <strong>{len(strengths)}</strong> |
            Punti di debolezza: <strong>{len(weaknesses)}</strong> |
            Nella media: <strong>{len(neutral)}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Two columns for strengths and weaknesses
    col_strength, col_weakness = st.columns(2)

    with col_strength:
        st.markdown("""
        <h3 style="color: #28a745; border-bottom: 3px solid #28a745; padding-bottom: 8px;">
            ✅ PUNTI DI FORZA
        </h3>
        <p style="color: #666; font-size: 0.9rem; margin-bottom: 15px;">
            Metriche nel top 25% della Serie A
        </p>
        """, unsafe_allow_html=True)

        if len(strengths) == 0:
            st.info("Nessun punto di forza significativo identificato")
        else:
            # Group by category
            for category in CATEGORY_LABELS.keys():
                cat_metrics = strengths[strengths['metric_category'] == category]
                if len(cat_metrics) > 0:
                    st.markdown(f"**{CATEGORY_LABELS.get(category, category)}**")
                    for _, metric in cat_metrics.iterrows():
                        render_metric_badge(metric, is_strength=True)

    with col_weakness:
        st.markdown("""
        <h3 style="color: #dc3545; border-bottom: 3px solid #dc3545; padding-bottom: 8px;">
            ⚠️ PUNTI DI DEBOLEZZA
        </h3>
        <p style="color: #666; font-size: 0.9rem; margin-bottom: 15px;">
            Metriche nel bottom 25% della Serie A
        </p>
        """, unsafe_allow_html=True)

        if len(weaknesses) == 0:
            st.info("Nessun punto di debolezza significativo identificato")
        else:
            # Group by category
            for category in CATEGORY_LABELS.keys():
                cat_metrics = weaknesses[weaknesses['metric_category'] == category]
                if len(cat_metrics) > 0:
                    st.markdown(f"**{CATEGORY_LABELS.get(category, category)}**")
                    for _, metric in cat_metrics.iterrows():
                        render_metric_badge(metric, is_strength=False)

    # Expandable section for all metrics
    with st.expander("📊 Vedi tutte le metriche", expanded=False):
        render_all_metrics_table(metrics_df)


def render_all_metrics_table(metrics_df: pd.DataFrame):
    """Render a sortable table with all metrics."""
    display_data = []

    for _, row in metrics_df.iterrows():
        name = row['metric_name']
        display_info = METRIC_DISPLAY.get(name, (name.replace('_', ' ').title(), '📊'))
        display_name, emoji = display_info

        display_data.append({
            'Categoria': CATEGORY_LABELS.get(row['metric_category'], row['metric_category']),
            'Metrica': f"{emoji} {display_name}",
            'Valore (p90)': row['metric_value_p90'],
            'Rank': f"#{int(row['metric_rank'])}/{int(row['total_teams'])}",
            'Percentile': f"{row['percentile']:.0f}%"
        })

    df_display = pd.DataFrame(display_data)
    st.dataframe(df_display, use_container_width=True, hide_index=True)


def render_top_contributors(player_metrics_df: pd.DataFrame, metric_name: str, top_n: int = 5):
    """
    Render top contributors for a specific metric.

    Args:
        player_metrics_df: Player metrics DataFrame
        metric_name: Name of the metric
        top_n: Number of top contributors to show
    """
    metric_players = player_metrics_df[player_metrics_df['metric_name'] == metric_name]
    metric_players = metric_players.nlargest(top_n, 'contribution_percentage')

    display_info = METRIC_DISPLAY.get(metric_name, (metric_name.replace('_', ' ').title(), '📊'))
    display_name, emoji = display_info

    st.markdown(f"**{emoji} {display_name} - Top {top_n} Contribuenti:**")

    # Load SofaScore names mapping for better display names
    sofascore_map = get_sofascore_names_map()

    for _, player in metric_players.iterrows():
        player_id = player.get('player_id')
        statsbomb_name = player['player_name']

        # Use SofaScore name if available, otherwise StatsBomb name
        display_name_player = get_player_display_name(int(player_id), statsbomb_name, sofascore_map) if player_id else statsbomb_name
        surname = extract_surname(display_name_player) if display_name_player else 'Unknown'

        value = player['metric_value']
        pct = player['contribution_percentage']
        p90 = player['metric_value_p90']

        st.markdown(f"""
        <div style="
            display: flex;
            justify-content: space-between;
            padding: 6px 10px;
            background: #f8f9fa;
            border-radius: 4px;
            margin-bottom: 4px;
        ">
            <span><strong>{surname}</strong></span>
            <span>
                {value:.0f}
                <span style="color: #666;">({pct:.1f}%)</span>
                <span style="color: #999; font-size: 0.8rem;">| {p90:.2f} p90</span>
            </span>
        </div>
        """, unsafe_allow_html=True)
