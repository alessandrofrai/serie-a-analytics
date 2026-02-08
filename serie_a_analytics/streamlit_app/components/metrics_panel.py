"""
Metrics Panel Component

Displays team metrics organized by category with progress bars and rankings.
"""

import streamlit as st
import pandas as pd


# Category display names in Italian
CATEGORY_NAMES = {
    'attacking': 'Attacco',
    'chance_creation': 'Creazione',
    'buildup': 'Costruzione',  # Metriche build-up (Z1 -> Z2/Z3)
    'transition': 'Transizioni',  # Metriche transizione (Z2/Z3, contropiedi)
    'possession': 'Possesso',
    'defending': 'Difesa',
    'pressing': 'Pressing',
    'set_pieces': 'Palle Inattive',
    'goalkeeping': 'Portiere',
    'shot_analysis': 'Analisi Tiri',
    'conceded': 'Vulnerabilità',  # Tiri e xG subiti per fase di gioco
}

# Metric display names
METRIC_NAMES = {
    # Attacking
    'shots_total': 'Tiri Totali',
    'shots_on_target': 'Tiri in Porta',
    'xg_total': 'xG Totale',
    'xg_open_play': 'xG Gioco Aperto',
    'goals_scored': 'Gol Segnati',
    'goal_conversion_rate': '% Conversione Gol',
    'goal_conversion_sot': '% Conversione SOT',
    'big_chances': 'Grandi Occasioni',
    'big_chances_against': 'Grandi Occasioni Subite',
    'big_chances_conversion': '% Conv. Grandi Occ.',
    'xg_goals_difference': 'Gol vs xG Atteso',
    'shots_per_box_touch': 'Tiri ogni 100 Tocchi Area',
    'touches_in_box': 'Tocchi in Area',

    # Defending
    'tackles': 'Contrasti Vinti',
    'interceptions': 'Intercetti',
    'clearances': 'Respinte',
    'blocks': 'Blocchi',
    'aerial_duels_open_play': 'Duelli Aerei Gioco Aperto',
    'aerial_duels_set_pieces': 'Duelli Aerei Palle Inattive',
    'aerial_duels_offensive': 'Duelli Aerei in Attacco',
    'aerial_duels_defensive': 'Duelli Aerei in Difesa',
    'ground_duels_offensive': 'Contrasti Offensivi',
    'ground_duels_defensive': 'Contrasti Difensivi',
    'fouls_committed': 'Falli Commessi',
    'yellow_cards': 'Cartellini Gialli',
    'red_cards': 'Cartellini Rossi',
    'opp_passes_def_third': 'Pass. Avv. in Dif.',
    'goals_conceded': 'Gol Subiti',
    'shots_against': 'Tiri Subiti',
    'shots_on_target_against': 'Tiri in Porta Subiti',
    'xga_total': 'xGA Totale',
    'xga_open_play': 'xGA Gioco Aperto',
    'xga_difference': 'xGA - Gol Subiti',

    # Possession
    'possession_percentage': '% Possesso',
    'passes_total': 'Passaggi Completati',
    'passes_short': 'Passaggi Corti',
    'passes_medium': 'Passaggi Medi',
    'passes_long': 'Passaggi Lunghi',
    'progressive_passes': 'Passaggi Progressivi',
    'progressive_carries': 'Conduzioni Progressive',
    'crosses_total': 'Cross Riusciti',
    'dribbles_total': 'Dribbling Riusciti',
    'key_passes': 'Passaggi Chiave',
    'through_balls': 'Filtranti',
    'switches_of_play': 'Cambi Gioco',
    'xa_total': 'xA Totale',
    'xa_per_key_pass': 'Qualità Passaggi Chiave',
    'goals_per_xa': 'Efficienza Assist',
    'ball_recoveries': 'Recuperi Palla',
    'turnovers_per_touch': '% Palle Perse',

    # Transition / Build-up
    'buildup_sequences': 'Pazienza in Build-up',  # Invertita: meno sequenze = più pazienza
    'buildup_direct': 'Build-up Diretto (Z1→Z3)',
    'buildup_direct_goals': 'Gol Build-up Diretto',
    'buildup_direct_sot': 'Tiri in Porta Build-up Dir.',
    'buildup_direct_xg': 'xG Build-up Diretto',
    'buildup_progressive': 'Build-up Progressivo (Z1→Z2→Z3)',
    'buildup_progressive_goals': 'Gol Build-up Progressivo',
    'buildup_progressive_sot': 'Tiri in Porta Build-up Prog.',
    'buildup_progressive_xg': 'xG Build-up Progressivo',
    'buildup_progressive_ratio': '% Stile Progressivo',
    'buildup_goals': 'Gol Totali da Build-up',
    'buildup_success_rate': '% Build-up Riusciti',
    'transition_z2_sequences': 'Azioni da Centrocampo (Z2)',
    'transition_z2_xg': 'xG da Centrocampo',
    'transition_z3_sequences': 'Azioni da Trequarti (Z3)',
    'transition_z3_xg': 'xG da Trequarti',
    'counter_attacks': 'Contropiedi',
    'fast_attacks': 'Attacchi Rapidi (<15s)',
    'sot_from_counters': 'Tiri in Porta da Contropiede',
    'sot_from_fast_attacks': 'Tiri in Porta da Att. Rapidi',
    'sot_per_recovery_z2': 'Efficienza Recupero Z2',
    'sot_per_recovery_z3': 'Efficienza Recupero Z3',

    # Set pieces
    'penalties_taken': 'Rigori Calciati',
    'direct_free_kicks': 'Punizioni Dirette',
    'xg_direct_set_pieces': 'xG Palle Inattive Dir.',
    'corners_taken': 'Calci d\'Angolo',
    'indirect_free_kicks': 'Punizioni Indirette',
    'throw_ins': 'Rimesse Laterali',
    'xg_indirect_set_pieces': 'xG Palle Inattive Ind.',
    'xg_indirect_set_pieces_conceded': 'xG Subito da Inattive',
    'sot_per_100_corners': 'Efficienza Corner',
    'sot_per_100_indirect_sp': 'Efficienza Inattive Ind.',
    'set_piece_shots_total': 'Tiri per 100 Inattive',

    # Pressing
    'ppda': 'PPDA (Pass per Az. Dif.)',
    'high_press_recoveries': 'Recuperi da Pressing Alto',
    'counterpressing_recoveries': 'Recuperi da Gegenpressing',
    'counterpressing': 'Azioni Gegenpressing',
    'pressing_sequences': 'Sequenze di Pressing',
    'pressing_actions': 'Azioni di Pressing',
    'pressing_high': 'Pressing in Z3 (Alto)',
    'pressing_middle': 'Pressing in Z2 (Medio)',
    'pressing_regains': 'Palle Riconquistate',
    'pressing_success_rate': '% Successo Pressing',
    'pressing_xg': 'xG da Pressing',

    # Shot Analysis - Attacking
    'shots_direct_sp': 'Tiri da Inattive Dirette',
    'shots_indirect_sp': 'Tiri da Inattive Indirette',
    'shots_counter': 'Tiri da Contropiede',
    'shots_fast_attack': 'Tiri da Attacco Rapido',
    'shots_cross': 'Tiri da Cross',
    'shots_long_range': 'Tiri da Fuori',
    'shots_buildup_progressive': 'Tiri da Build-up Prog.',
    'shots_buildup_direct': 'Tiri da Build-up Dir.',
    'xg_direct_sp': 'xG da Inattive Dirette',
    'xg_indirect_sp': 'xG da Inattive Indirette',
    'xg_counter': 'xG da Contropiede',
    'xg_fast_attack': 'xG da Attacco Rapido',
    'xg_cross': 'xG da Cross',
    'xg_long_range': 'xG da Fuori',
    'xg_buildup_progressive': 'xG da Build-up Prog.',
    'xg_buildup_direct': 'xG da Build-up Dir.',
    'shots_made_total': 'Tiri Effettuati Totali',

    # Shot Analysis - Defending (Conceded)
    'shots_conceded_direct_sp': 'Tiri Subiti da Inattive Dir.',
    'shots_conceded_indirect_sp': 'Tiri Subiti da Inattive Ind.',
    'shots_conceded_counter': 'Tiri Subiti da Contropiede',
    'shots_conceded_fast_attack': 'Tiri Subiti da Attacco Rapido',
    'shots_conceded_cross': 'Tiri Subiti da Cross',
    'shots_conceded_long_range': 'Tiri Subiti da Fuori',
    'shots_conceded_buildup_progressive': 'Tiri Subiti da Build-up Prog.',
    'shots_conceded_buildup_direct': 'Tiri Subiti da Build-up Dir.',
    'xg_conceded_direct_sp': 'xG Subito da Inattive Dir.',
    'xg_conceded_indirect_sp': 'xG Subito da Inattive Ind.',
    'xg_conceded_counter': 'xG Subito da Contropiede',
    'xg_conceded_fast_attack': 'xG Subito da Attacco Rapido',
    'xg_conceded_cross': 'xG Subito da Cross',
    'xg_conceded_long_range': 'xG Subito da Fuori',
    'xg_conceded_buildup_progressive': 'xG Subito da Build-up Prog.',
    'xg_conceded_buildup_direct': 'xG Subito da Build-up Dir.',
    'shots_conceded_total': 'Tiri Subiti Totali',
}


def render_metrics_panel(metrics_df: pd.DataFrame, total_entities: int):
    """
    Render the metrics panel with all team metrics.

    Args:
        metrics_df: DataFrame with team metrics
        total_entities: Total team+manager combinations for ranking
    """
    if len(metrics_df) == 0:
        st.info("Nessuna metrica disponibile")
        return

    # Group by category
    categories = metrics_df['metric_category'].unique()

    for category in sorted(categories):
        category_metrics = metrics_df[metrics_df['metric_category'] == category]
        category_name = CATEGORY_NAMES.get(category, category.title())

        with st.expander(category_name, expanded=True):
            for _, metric in category_metrics.iterrows():
                render_metric_card(metric, total_entities)


def render_metric_card(metric: pd.Series, total_entities: int):
    """
    Render a single metric card with progress bar and ranking.

    Args:
        metric: Series with metric data
        total_entities: Total for ranking display
    """
    metric_name = metric['metric_name']
    display_name = METRIC_NAMES.get(metric_name, metric_name.replace('_', ' ').title())
    value_p90 = metric['metric_value_p90']
    rank = metric.get('metric_rank', '-')
    percentile = metric.get('percentile', 50)

    # Format value
    if value_p90 >= 100:
        value_str = f"{value_p90:.0f}"
    elif value_p90 >= 10:
        value_str = f"{value_p90:.1f}"
    else:
        value_str = f"{value_p90:.2f}"

    # Calculate progress bar width (based on percentile)
    progress_pct = min(100, max(0, percentile))

    # Determine color based on rank (1 = best = green, last = red)
    if rank and total_entities > 0:
        rank_pct = (total_entities - rank + 1) / total_entities
        if rank_pct >= 0.75:
            bar_color = "#28a745"  # Green - top 25%
        elif rank_pct >= 0.5:
            bar_color = "#ffc107"  # Yellow - 25-50%
        elif rank_pct >= 0.25:
            bar_color = "#fd7e14"  # Orange - 50-75%
        else:
            bar_color = "#dc3545"  # Red - bottom 25%
    else:
        bar_color = "#6c757d"

    # Rank display
    rank_display = f"#{rank}/{total_entities}" if rank else "N/A"

    # Create clickable metric card
    col1, col2, col3 = st.columns([3, 2, 1])

    with col1:
        st.markdown(f"**{display_name}**")
        st.markdown(f"""
        <div style="
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 4px;
        ">
            <div style="
                width: {progress_pct}%;
                height: 100%;
                background: {bar_color};
                border-radius: 4px;
            "></div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"<span style='font-size: 1.2rem; font-weight: bold;'>{value_str}</span> <span style='color: #666; font-size: 0.8rem;'>p90</span>", unsafe_allow_html=True)

    with col3:
        st.markdown(f"<span style='color: {bar_color}; font-weight: bold;'>{rank_display}</span>", unsafe_allow_html=True)

    # Make clickable - use category + name for unique key
    category = metric.get('metric_category', 'unknown')
    if st.button(
        "👁️ Contributi",
        key=f"metric_{category}_{metric_name}",
        use_container_width=True
    ):
        st.session_state.selected_metric = metric_name
        st.rerun()

    st.markdown("---")
