"""
PDF Report Dialog Component for Serie A Analytics.

Provides a Streamlit dialog for configuring and generating PDF reports.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Any

from components.metrics_panel import METRIC_NAMES
from services.pdf_report import (
    PDFReportConfig,
    PDFReportGenerator,
    PDFReportError,
    get_strength_metrics,
    get_weakness_metrics,
    get_metrics_with_contributions,
)
from utils.data_helpers import is_average, is_weakness


def render_pdf_report_dialog(
    team_id: int,
    manager_id: int,
    team_name: str,
    manager_name: str,
    matches_count: int,
    formation: str,
    cluster_name: str,
    data: Dict[str, Any],
    team_metrics: pd.DataFrame,
    player_metrics: pd.DataFrame,
    formation_stats: Optional[Dict[str, Any]] = None,
    logo_base64: Optional[str] = None,
    radar_base64: Optional[str] = None,
    pitch_base64: Optional[str] = None,
    team_analysis: Optional[str] = None,
    player_profiles: Optional[List[Dict]] = None,
    player_names: Optional[Dict[int, str]] = None,
    player_id_to_slot: Optional[Dict[int, int]] = None,
    player_faces: Optional[Dict[int, Any]] = None,
    player_ratings: Optional[Dict[int, float]] = None,
):
    """
    Render the PDF report configuration dialog.

    This function should be called inside a st.dialog() context.
    """
    st.markdown("### Configura Report PDF")
    st.markdown(f"**{team_name}** - {manager_name}")

    total_combinations = len(data.get('combinations', []))

    # Get available metrics
    strength_metrics = get_strength_metrics(team_metrics, total_combinations)
    weakness_metrics = get_weakness_metrics(team_metrics, total_combinations)

    # Section 1: Positive Metrics Selection
    st.markdown("---")
    st.markdown("#### Metriche Positive (opzionale, max 10)")
    st.caption("Le metriche sono ordinate dalla migliore. Seleziona quelle da includere nel report.")

    # Create options with display names
    positive_options = {
        METRIC_NAMES.get(m, m.replace('_', ' ').title()): m
        for m in strength_metrics
    }

    # Default: empty (user can optionally select metrics)
    default_positive = []

    selected_positive_display = st.multiselect(
        "Metriche positive",
        options=list(positive_options.keys()),
        default=default_positive,
        max_selections=10,
        key="pdf_positive_metrics",
        label_visibility="collapsed"
    )
    selected_positive = [positive_options[d] for d in selected_positive_display]

    # Section 2: Negative Metrics Selection
    st.markdown("---")
    st.markdown("#### Metriche Negative (opzionale, max 10)")
    st.caption("Le metriche includono Negative e Nella Media, ordinate dalla peggiore.")

    # Include weaknesses + average metrics, ordered by worst rank
    negative_candidates = []
    for _, row in team_metrics.iterrows():
        try:
            rank = int(row.get('metric_rank', 0))
        except Exception:
            rank = 0
        if is_weakness(rank, total_combinations) or is_average(rank, total_combinations):
            negative_candidates.append((rank, row.get('metric_name')))

    negative_candidates.sort(key=lambda x: x[0], reverse=True)
    negative_metric_names = [m for _, m in negative_candidates]

    negative_options = {
        METRIC_NAMES.get(m, m.replace('_', ' ').title()): m
        for m in negative_metric_names
    }

    # Default: empty (user can optionally select metrics)
    default_negative = []

    selected_negative_display = st.multiselect(
        "Metriche negative",
        options=list(negative_options.keys()),
        default=default_negative,
        max_selections=10,
        key="pdf_negative_metrics",
        label_visibility="collapsed"
    )
    selected_negative = [negative_options[d] for d in selected_negative_display]

    # Section 3: Positive Contributions Detail
    st.markdown("---")
    st.markdown("#### Dettaglio Contributi Positivi")
    st.caption("Seleziona una o più metriche positive per vedere la classifica dei contributori.")

    # Filter to metrics with contributions
    positive_with_contrib = get_metrics_with_contributions(
        player_metrics, team_id, manager_id, selected_positive
    )

    if len(positive_with_contrib) > 0:
        positive_contrib_options = {
            METRIC_NAMES.get(m, m.replace('_', ' ').title()): m
            for m in positive_with_contrib
        }

        selected_positive_detail_display = st.multiselect(
            "Metriche per dettaglio contributi positivi",
            options=list(positive_contrib_options.keys()),
            default=list(positive_contrib_options.keys())[:2],
            key="pdf_positive_detail",
            label_visibility="collapsed"
        )
        selected_positive_detail = [positive_contrib_options[d] for d in selected_positive_detail_display]
    else:
        st.info("Nessuna delle metriche selezionate ha contributi giocatori disponibili.")
        selected_positive_detail = []

    # Section 4: Negative Contributions Detail
    st.markdown("---")
    st.markdown("#### Dettaglio Contributi Negativi")
    st.caption("Seleziona una o più metriche negative per vedere la classifica dei contributori.")

    negative_with_contrib = get_metrics_with_contributions(
        player_metrics, team_id, manager_id, selected_negative
    )

    if len(negative_with_contrib) > 0:
        negative_contrib_options = {
            METRIC_NAMES.get(m, m.replace('_', ' ').title()): m
            for m in negative_with_contrib
        }

        selected_negative_detail_display = st.multiselect(
            "Metriche per dettaglio contributi negativi",
            options=list(negative_contrib_options.keys()),
            default=list(negative_contrib_options.keys())[:2],
            key="pdf_negative_detail",
            label_visibility="collapsed"
        )
        selected_negative_detail = [negative_contrib_options[d] for d in selected_negative_detail_display]
    else:
        st.info("Nessuna delle metriche selezionate ha contributi giocatori disponibili.")
        selected_negative_detail = []

    # Generate button
    st.markdown("---")

    # Count total metrics for button label
    total_metrics_count = len(selected_positive) + len(selected_negative)
    button_label = f"Genera Report PDF ({total_metrics_count})"

    # Always allow generation (0 metrics is now valid)
    if st.button(button_label, type="primary", use_container_width=True):
        try:
            missing_sections = []
            if not team_analysis:
                missing_sections.append("Analisi Tattica Squadra")
            if not player_profiles:
                missing_sections.append("Analisi Tattica Singoli Giocatori")
            if total_metrics_count == 0:
                missing_sections.append("Rank Metriche Squadra")

            if missing_sections:
                warning_text = (
                    "Attenzione: nel report non saranno presenti "
                    + ", ".join(missing_sections)
                    + " perché non sono state generate nella dashboard."
                )
                try:
                    st.toast(warning_text, icon="⚠️")
                except Exception:
                    pass
                st.warning(warning_text)

            with st.spinner("Generazione report in corso..."):
                # Create config
                config = PDFReportConfig(
                    team_id=team_id,
                    manager_id=manager_id,
                    team_name=team_name,
                    manager_name=manager_name,
                    matches_count=matches_count,
                    formation=formation,
                    cluster_name=cluster_name,
                    formation_stats=formation_stats,
                    positive_metrics=selected_positive,
                    negative_metrics=selected_negative,
                    positive_detail_metrics=selected_positive_detail,
                    negative_detail_metrics=selected_negative_detail,
                )

                # Create generator
                generator = PDFReportGenerator(
                    config=config,
                    data=data,
                    team_metrics=team_metrics,
                    player_metrics=player_metrics,
                    logo_base64=logo_base64,
                    radar_base64=radar_base64,
                    pitch_base64=pitch_base64,
                    team_analysis=team_analysis,
                    player_profiles=player_profiles,
                    player_names=player_names,
                    player_id_to_slot=player_id_to_slot,
                    player_faces=player_faces,
                    player_ratings=player_ratings,
                    performances_df=data.get('performances'),
                    valid_pairs=data.get('valid_pairs', set()),
                )

                # Generate PDF
                pdf_bytes = generator.generate()

                # Store in session state for download
                st.session_state.pdf_report_bytes = pdf_bytes
                st.session_state.pdf_report_filename = f"report_{team_name.replace(' ', '_')}_{manager_name.replace(' ', '_')}.pdf"

                st.success("Report generato con successo!")
                st.rerun()

        except PDFReportError as e:
            st.error(f"Errore: {str(e)}")
        except Exception as e:
            st.error(f"Errore imprevisto: {str(e)}")


@st.dialog("Genera Report PDF", width="large")
def show_pdf_report_dialog(
    team_id: int,
    manager_id: int,
    team_name: str,
    manager_name: str,
    matches_count: int,
    formation: str,
    cluster_name: str,
    data: Dict[str, Any],
    team_metrics: pd.DataFrame,
    player_metrics: pd.DataFrame,
    formation_stats: Optional[Dict[str, Any]] = None,
    logo_base64: Optional[str] = None,
    radar_base64: Optional[str] = None,
    pitch_base64: Optional[str] = None,
    team_analysis: Optional[str] = None,
    player_profiles: Optional[List[Dict]] = None,
    player_names: Optional[Dict[int, str]] = None,
    player_id_to_slot: Optional[Dict[int, int]] = None,
    player_faces: Optional[Dict[int, Any]] = None,
    player_ratings: Optional[Dict[int, float]] = None,
):
    """
    Show the PDF report dialog as a Streamlit dialog.

    This is the main entry point for the PDF report dialog.
    """
    render_pdf_report_dialog(
        team_id=team_id,
        manager_id=manager_id,
        team_name=team_name,
        manager_name=manager_name,
        matches_count=matches_count,
        formation=formation,
        cluster_name=cluster_name,
        formation_stats=formation_stats,
        data=data,
        team_metrics=team_metrics,
        player_metrics=player_metrics,
        logo_base64=logo_base64,
        radar_base64=radar_base64,
        pitch_base64=pitch_base64,
        team_analysis=team_analysis,
        player_profiles=player_profiles,
        player_names=player_names,
        player_id_to_slot=player_id_to_slot,
        player_faces=player_faces,
        player_ratings=player_ratings,
    )
