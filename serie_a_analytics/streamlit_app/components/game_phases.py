"""
Game Phases Component - Visualizes xG/Shots by game phase.

Shows how a team creates and concedes xG/shots from different game situations:
- Direct Set Pieces (penalties, direct free kicks)
- Indirect Set Pieces (corners, throw-ins, indirect free kicks)
- Counter Attacks
- Fast Attacks (<10 seconds)
- Crosses
- Long Range shots
- Progressive Build-up (Z1->Z2->Z3)
- Direct Build-up (Z1->Z3)
"""

import streamlit as st
import pandas as pd
from typing import List, Tuple, Optional

from components.metrics_panel import METRIC_NAMES

# Le 8 fasi di gioco
GAME_PHASES = [
    'direct_sp',
    'indirect_sp',
    'counter',
    'fast_attack',
    'cross',
    'long_range',
    'buildup_progressive',
    'buildup_direct',
]

# Nomi italiani per le fasi
PHASE_NAMES = {
    'direct_sp': 'Inattive Dirette',
    'indirect_sp': 'Inattive Indirette',
    'counter': 'Contropiede',
    'fast_attack': 'Attacco Rapido',
    'cross': 'Cross',
    'long_range': 'Tiro da Fuori',
    'buildup_progressive': 'Build-up Progressivo',
    'buildup_direct': 'Build-up Diretto',
}

# Colori per ranking
COLOR_STRENGTH = "#22c55e"  # Verde - top 25%
COLOR_AVERAGE = "#9ca3af"   # Grigio - media
COLOR_WEAKNESS = "#ef4444"  # Rosso - bottom 25%


def get_phase_color(rank: int, total: int) -> str:
    """
    Determina il colore della barra in base al ranking.
    Il ranking e' gia' normalizzato (rank 1 = migliore sia per creazione che subiti).
    """
    if total == 0 or rank == 0:
        return COLOR_AVERAGE

    percentile = (total - rank + 1) / total

    if percentile >= 0.75:
        return COLOR_STRENGTH  # Top 25%
    elif percentile <= 0.25:
        return COLOR_WEAKNESS  # Bottom 25%
    else:
        return COLOR_AVERAGE   # Media


def get_metric_data(team_metrics: pd.DataFrame, metric_name: str, total: int) -> dict:
    """Estrae i dati di una singola metrica."""
    metric_row = team_metrics[team_metrics['metric_name'] == metric_name]

    if len(metric_row) > 0:
        row = metric_row.iloc[0]
        rank = int(row.get('metric_rank', 0)) or total
        bar_value = (total - rank + 1) / total if total > 0 else 0
        return {
            'rank': rank,
            'bar_value': bar_value,
            'color': get_phase_color(rank, total),
            'value_p90': row.get('metric_value_p90', 0) or 0,
        }
    else:
        return {
            'rank': 0,
            'bar_value': 0,
            'color': COLOR_AVERAGE,
            'value_p90': 0,
        }


def render_progress_bar(value: float, color: str, rank: int, total: int) -> str:
    """Genera HTML per una barra di progresso compatta con rank grande e vicino."""
    width_pct = max(5, value * 100)  # Minimo 5% per visibilita'
    rank_text = f"#{rank}" if rank > 0 else "N/A"

    return f'''
    <div style="display:flex;align-items:center;gap:4px;width:100%;">
        <div style="flex:1;background:#e5e7eb;border-radius:4px;height:22px;overflow:hidden;">
            <div style="width:{width_pct}%;height:100%;background:{color};border-radius:4px;"></div>
        </div>
        <span style="font-weight:700;font-size:1.1rem;min-width:40px;text-align:left;color:{color};">{rank_text}</span>
    </div>
    '''


@st.fragment
def render_game_phases_section(
    team_metrics: pd.DataFrame,
    total_combinations: int
):
    """
    Render the complete game phases section with row-based layout.

    Ogni fase ha una riga con:
    - Nome fase
    - Barra Creazione con rank
    - Barra Subiti con rank
    - Bottone dettaglio
    """
    st.markdown("### :material/sports_soccer: Fasi di Gioco")

    # Toggle e legenda
    col_toggle, col_legend = st.columns([1, 2])

    with col_toggle:
        show_xg = st.toggle("Mostra xG", value=True, key="game_phases_xg_toggle")

    with col_legend:
        st.markdown(
            '<span style="font-size:0.8rem;">'
            '<span style="color:#22c55e;">&#9632;</span> Top 25% · '
            '<span style="color:#9ca3af;">&#9632;</span> Media · '
            '<span style="color:#ef4444;">&#9632;</span> Bottom 25%'
            '</span>',
            unsafe_allow_html=True
        )

    prefix = "xg_" if show_xg else "shots_"
    metric_type = "xG" if show_xg else "Tiri"

    # Header della tabella con separatore verticale
    col_phase, col_creation, col_sep, col_conceded, col_btn = st.columns([2, 2.5, 0.1, 2.5, 0.8])

    with col_phase:
        st.markdown(f"**Fase**")
    with col_creation:
        st.markdown(f"**{metric_type} Creati**")
    with col_sep:
        st.markdown("")  # Spazio per il separatore
    with col_conceded:
        st.markdown(f"**{metric_type} Subiti**")
    with col_btn:
        st.markdown("")

    st.markdown("<hr style='margin:0.5rem 0;border-color:#e5e7eb;'>", unsafe_allow_html=True)

    # Righe per ogni fase
    for phase in GAME_PHASES:
        creation_metric = f"{prefix}{phase}"
        conceded_metric = f"{prefix}conceded_{phase}"

        creation_data = get_metric_data(team_metrics, creation_metric, total_combinations)
        conceded_data = get_metric_data(team_metrics, conceded_metric, total_combinations)

        col_phase, col_creation, col_sep, col_conceded, col_btn = st.columns([2, 2.5, 0.1, 2.5, 0.8])

        with col_phase:
            st.markdown(f"<div style='padding-top:2px;font-size:0.9rem;'>{PHASE_NAMES[phase]}</div>", unsafe_allow_html=True)

        with col_creation:
            st.markdown(
                render_progress_bar(
                    creation_data['bar_value'],
                    creation_data['color'],
                    creation_data['rank'],
                    total_combinations
                ),
                unsafe_allow_html=True
            )

        with col_sep:
            # Linea separatrice verticale sottile grigia
            st.markdown(
                "<div style='width:1px;height:22px;background:#d1d5db;margin:0 auto;'></div>",
                unsafe_allow_html=True
            )

        with col_conceded:
            st.markdown(
                render_progress_bar(
                    conceded_data['bar_value'],
                    conceded_data['color'],
                    conceded_data['rank'],
                    total_combinations
                ),
                unsafe_allow_html=True
            )

        with col_btn:
            # Popover per scegliere quale dettaglio vedere
            with st.popover("→", help=f"Dettaglio {PHASE_NAMES[phase]}"):
                st.markdown(f"**{PHASE_NAMES[phase]}**")

                if st.button(
                    f"📈 {metric_type} Creati (#{creation_data['rank']})",
                    key=f"detail_creation_{phase}",
                    use_container_width=True
                ):
                    st.session_state.selected_metric = creation_metric
                    st.rerun()

                if st.button(
                    f"🛡️ {metric_type} Subiti (#{conceded_data['rank']})",
                    key=f"detail_conceded_{phase}",
                    use_container_width=True
                ):
                    st.session_state.selected_metric = conceded_metric
                    st.rerun()

    st.caption(f"Ranking su {total_combinations} squadre · Creati: rank alto = più creati · Subiti: rank alto = meno subiti")
