"""
Team Dashboard Page.

This is a separate page for the team dashboard to avoid DOM ghosting issues
when transitioning from the team selection grid.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="Dashboard Squadra - Serie A 2015-2016",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Import shared modules AFTER page config
from utils.styles import apply_custom_css
from utils.data_helpers import (
    load_data,
    get_team_playing_style,
    get_xg_by_opponent_cluster,
    get_formation_stats,
    get_top_11_players,
    get_all_available_players,
    apply_player_overrides,
    extract_surname,
    is_strength,
    is_average,
    is_weakness,
    get_team_logo_html,
    get_team_logo_base64,
    get_player_faces_by_slot,
    get_player_ratings_by_slot,
    get_roster_for_team,
    get_player_face_image,
    get_sofascore_team_id,
)
from utils.render_helpers import (
    render_metrics_with_filter,
    render_full_team_ranking,
    render_all_players_ranking,
    render_player_analysis,
)
from components.pitch import render_formation, render_formation_to_base64
from components.metrics_panel import METRIC_NAMES, CATEGORY_NAMES
from components.team_radar import (
    render_team_radar_minimal,
    render_team_radar_comparison,
    calculate_radar_values,
    get_metrics_by_category,
    render_radar_to_base64,
)
from components.performance_scatterplot import render_performance_section
from components.game_phases import render_game_phases_section
from services.ai_insights import (
    generate_team_tactical_profile,
    generate_fallback_team_profile
)
from config import FORMATION_COORDINATES, POSITION_MAPPING

# Apply custom CSS
apply_custom_css()


# =============================================================================
# ROSTER DIALOG
# =============================================================================

def get_position_label(position: str) -> str:
    """Convert position code to Italian label."""
    labels = {
        'G': 'Portieri',
        'D': 'Difensori',
        'M': 'Centrocampisti',
        'F': 'Attaccanti'
    }
    return labels.get(position, 'Altri')


@st.dialog("Rosa Squadra", width="large")
def show_roster_dialog(sofascore_team_id: int, team_name: str):
    """
    Show team roster dialog grouped by position.
    Clicking a player navigates to their profile page.
    """
    st.markdown(f"### Rosa {team_name}")

    roster = get_roster_for_team(sofascore_team_id)

    if roster.empty:
        st.warning("Nessun giocatore trovato per questa squadra.")
        return

    # Group by position
    position_order = ['G', 'D', 'M', 'F']

    for position in position_order:
        group = roster[roster['position'] == position].copy()
        if group.empty:
            continue

        # Sort by minutes (descending)
        group = group.sort_values('minutes_total', ascending=False)

        st.markdown(f'<div class="roster-group-title">{get_position_label(position)}</div>', unsafe_allow_html=True)

        for _, player in group.iterrows():
            player_id = int(player['player_id'])
            player_name = player['player_name']
            matches = int(player['matches'])
            minutes = int(player['minutes_total'])
            avg_rating = player['avg_rating']

            # Create columns for player row
            col_img, col_info, col_btn = st.columns([1, 5, 1])

            with col_img:
                # Try to get player image
                try:
                    img = get_player_face_image(player_id)
                    if img is not None:
                        st.image(img, width=40)
                    else:
                        st.markdown("👤", help="Immagine non disponibile")
                except Exception:
                    st.markdown("👤")

            with col_info:
                rating_str = f"{avg_rating:.2f}" if avg_rating and avg_rating > 0 else "N/A"
                st.markdown(f"""
                    <div class="roster-player-info">
                        <span class="roster-player-name">{player_name}</span>
                        <span class="roster-player-stats">
                            <span class="roster-stat"><span class="roster-stat-label">Partite:</span> <span class="roster-stat-value">{matches}</span></span>
                            <span class="roster-stat"><span class="roster-stat-label">Min:</span> <span class="roster-stat-value">{minutes}</span></span>
                            <span class="roster-stat"><span class="roster-stat-label">Voto:</span> <span class="roster-stat-value">{rating_str}</span></span>
                        </span>
                    </div>
                """, unsafe_allow_html=True)

            with col_btn:
                if st.button("→", key=f"player_{player_id}", help=f"Vai al profilo di {player_name}"):
                    st.session_state.player_profile_id = player_id
                    st.session_state.player_profile_team = sofascore_team_id
                    st.switch_page("pages/player_profile.py")

        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)


# =============================================================================
# PDF NO PLAYERS WARNING DIALOG
# =============================================================================

@st.dialog("Attenzione", width="small")
def show_pdf_no_players_dialog():
    """
    Show warning when generating PDF without player analysis.
    User can choose to proceed or cancel.
    """
    st.markdown("""
        ### Analisi Giocatori Non Generata

        Non è stata generata l'analisi tattica dei singoli giocatori.

        Il report PDF verrà creato **senza** la sezione "Analisi Singoli Giocatori".

        Vuoi procedere comunque?
    """)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Annulla", use_container_width=True, type="secondary"):
            st.session_state.show_pdf_no_players_dialog = False
            st.session_state.generate_pdf_report = False
            st.rerun()
    with col2:
        if st.button("Prosegui", use_container_width=True, type="primary"):
            st.session_state.show_pdf_no_players_dialog = False
            st.session_state.pdf_skip_players_confirmed = True
            st.session_state.generate_pdf_report = True
            st.rerun()


@st.fragment
def render_radar_section(
    data: dict,
    team_metrics: pd.DataFrame,
    team_id: int,
    manager_name: str,
    manager_id: int,
    team_name: str,
):
    """Render radar chart + comparison dropdown as an isolated fragment."""
    # Radar chart + comparison dropdown (top-right)
    comparison_df = data['combinations'].copy()
    comparison_df['label'] = comparison_df.apply(
        lambda r: f"{r['team_name']} — {r['manager_name']} ({int(r['matches_count'])} partite)",
        axis=1
    )
    comparison_df = comparison_df[
        ~((comparison_df['team_id'] == team_id) & (comparison_df['manager_name'] == manager_name))
    ]
    comparison_options = ["Nessuno"] + comparison_df['label'].tolist()

    col_radar_title, col_radar_select = st.columns([3, 1])
    with col_radar_title:
        st.markdown("### :material/analytics: Profilo Tattico Squadra")
    with col_radar_select:
        selected_label = st.selectbox(
            "Confronta con",
            options=comparison_options,
            index=0,
            key="radar_compare_select"
        )

    comparison_available = False
    other_team_metrics = None
    other_label = ""

    if selected_label != "Nessuno" and len(comparison_df) > 0:
        selected_row = comparison_df[comparison_df['label'] == selected_label].iloc[0]
        other_team_id = int(selected_row['team_id'])
        other_manager_name = selected_row['manager_name']

        other_manager_id = data['manager_id_map'].get((other_team_id, other_manager_name))
        if other_manager_id is not None:
            other_team_metrics = data['team_metrics'][
                (data['team_metrics']['team_id'] == other_team_id) &
                (data['team_metrics']['manager_id'] == other_manager_id)
            ]
            if len(other_team_metrics) > 0:
                comparison_available = True
                other_label = f"{selected_row['team_name']} · {other_manager_name}"

    if comparison_available:
        render_team_radar_comparison(
            team_metrics_a=team_metrics,
            team_metrics_b=other_team_metrics,
            label_a=f"{team_name} · {manager_name}",
            label_b=other_label,
            color_a="#3b82f6",
            color_b="#ef4444",
            height=360,
            show_values=True
        )
    else:
        render_team_radar_minimal(team_metrics, height=380)


@st.fragment
def render_player_analysis_section(
    data: dict,
    team_id: int,
    manager_id: int,
    player_id_to_slot: dict,
    player_names: dict,
    formation: str,
):
    """Render player analysis with isolated reruns to prevent UI ghosting."""
    st.markdown("### :material/person: Analisi Tattica Singoli Giocatori")

    # Cache key for storing results
    player_cache_key = (team_id, manager_id, tuple(sorted(player_id_to_slot.items())))

    # Initialize cache if not present
    if 'cached_player_profiles' not in st.session_state:
        st.session_state.cached_player_profiles = {}

    # If cached, render directly
    if player_cache_key in st.session_state.cached_player_profiles:
        cached_data = st.session_state.cached_player_profiles[player_cache_key]
        for player_profile in cached_data:
            with st.container(border=True):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"### {player_profile['surname']}")
                with col2:
                    st.markdown(
                        f"<p style='text-align:right;margin:0;padding-top:8px;'>"
                        f"<span style='color:#6b7280;font-size:0.85rem;'>{player_profile['position_it']}</span> · "
                        f"<span style='font-weight:600;font-size:0.85rem;'>{player_profile['archetype']}</span>"
                        f"</p>",
                        unsafe_allow_html=True
                    )
                st.markdown(
                    f"<p style='font-size:0.9rem;color:#374151;margin:0;'>{player_profile['description']}</p>",
                    unsafe_allow_html=True
                )
        return

    # Generate on demand
    if st.button(
        "🎯 Genera Analisi Giocatori",
        use_container_width=True,
        type="primary",
        key=f"gen_player_analysis_{team_id}_{manager_id}"
    ):
        render_player_analysis(
            player_metrics_df=data['player_metrics'],
            player_minutes_df=data.get('player_minutes'),
            team_id=team_id,
            manager_id=manager_id,
            player_id_to_slot=player_id_to_slot,
            player_names=player_names,
            formation=formation
        )


def dashboard_main():
    """Dashboard page main function."""

    # Check if a team is selected
    if 'selected_team' not in st.session_state or st.session_state.selected_team is None:
        st.warning("Nessuna squadra selezionata. Torna alla pagina principale.")
        if st.button("← Torna alla selezione squadre"):
            st.switch_page("app.py")
        return

    # Load data
    data = load_data()
    if data is None:
        st.warning("Dati non trovati. Esegui prima gli script di elaborazione.")
        return

    # Initialize session state
    if 'selected_manager' not in st.session_state:
        st.session_state.selected_manager = None
    if 'selected_metric' not in st.session_state:
        st.session_state.selected_metric = None
    if 'metric_filter' not in st.session_state:
        st.session_state.metric_filter = "strength"
    if 'player_overrides' not in st.session_state:
        st.session_state.player_overrides = {}
    if 'cached_team_profile' not in st.session_state:
        st.session_state.cached_team_profile = {}

    # PDF metric selection state - tracks which metrics are selected for PDF inclusion
    if 'pdf_selected_metrics' not in st.session_state:
        st.session_state.pdf_selected_metrics = {
            'positive': set(),
            'average': set(),
            'negative': set()
        }

    # PDF detail metrics - tracks which metrics should have detail contribution pages
    if 'pdf_detail_metrics' not in st.session_state:
        st.session_state.pdf_detail_metrics = {
            'positive': set(),
            'average': set(),
            'negative': set()
        }

    # PDF no players warning dialog state
    if 'show_pdf_no_players_dialog' not in st.session_state:
        st.session_state.show_pdf_no_players_dialog = False
    if 'pdf_skip_players_confirmed' not in st.session_state:
        st.session_state.pdf_skip_players_confirmed = False

    # Show warning dialog if triggered
    if st.session_state.get('show_pdf_no_players_dialog', False):
        show_pdf_no_players_dialog()

    team_id = st.session_state.selected_team
    team_name = data['teams'][data['teams']['team_id'] == team_id]['team_name'].values[0]

    # Header
    st.markdown('<div class="main-header">Serie A 2015-2016 Data Analytics</div>', unsafe_allow_html=True)

    # Back button - returns to team selection
    if st.button("← Torna alle squadre"):
        st.session_state.selected_team = None
        st.session_state.selected_manager = None
        st.session_state.selected_metric = None
        st.session_state.selected_player_id = None
        st.session_state.player_overrides = {}
        st.session_state.cached_team_profile = {}
        st.session_state.metric_filter = "strength"
        # Reset PDF selection state
        st.session_state.pdf_selected_metrics = {'positive': set(), 'average': set(), 'negative': set()}
        st.session_state.pdf_detail_metrics = {'positive': set(), 'average': set(), 'negative': set()}
        st.session_state.pdf_report_bytes = None
        st.session_state.pdf_skip_players_confirmed = False
        st.session_state.show_pdf_no_players_dialog = False
        st.switch_page("app.py")

    # Manager selection
    team_managers = data['combinations'][data['combinations']['team_id'] == team_id]

    if len(team_managers) == 0:
        st.warning("Nessun allenatore con abbastanza partite per questa squadra")
        return

    if len(team_managers) > 1:
        manager_options = {
            f"{row['manager_name']} ({row['matches_count']} partite)": row['manager_name']
            for _, row in team_managers.iterrows()
        }
        selected_manager_label = st.selectbox("Allenatore", options=list(manager_options.keys()))
        manager_name = manager_options[selected_manager_label]
        manager_info = team_managers[team_managers['manager_name'] == manager_name].iloc[0]
    else:
        manager_info = team_managers.iloc[0]
        manager_name = manager_info['manager_name']

    # Get manager_id from map
    manager_id = data['manager_id_map'].get((team_id, manager_name), 1)
    matches_count = manager_info['matches_count']

    # Team info header - centered layout with team logo
    team_logo = get_team_logo_html(team_id, size=100)

    # Get SofaScore team ID for roster
    sofascore_team_id = get_sofascore_team_id(team_id)

    # Header with Rosa button (left) and PDF buttons (right)
    col_roster, col_header, col_pdf = st.columns([1, 5, 1])

    with col_roster:
        st.markdown("<div style='height: 60px'></div>", unsafe_allow_html=True)  # Spacer
        if st.button(
            "Rosa",
            icon=":material/groups:",
            use_container_width=True,
            help="Visualizza la rosa della squadra"
        ):
            if sofascore_team_id:
                show_roster_dialog(sofascore_team_id, team_name)
            else:
                st.warning("ID squadra SofaScore non trovato")

    with col_header:
        st.markdown(f'''
            <div class="team-info-container">
                <div class="team-header">{team_name}</div>
                <div class="team-logo">{team_logo}</div>
                <div class="manager-name">{manager_name} <span class="manager-matches">({matches_count} partite)</span></div>
            </div>
        ''', unsafe_allow_html=True)

    with col_pdf:
        st.markdown("<div style='height: 60px'></div>", unsafe_allow_html=True)  # Spacer

        # Calculate total selected metrics for PDF
        total_selected = sum(
            len(st.session_state.get('pdf_selected_metrics', {}).get(cat, set()))
            for cat in ['positive', 'average', 'negative']
        )

        # Button to apply selections (triggers full rerun to update counter)
        if st.button(
            "Applica Selezioni",
            icon=":material/sync:",
            use_container_width=True,
            type="secondary",
            help="Clicca per aggiornare il conteggio delle metriche selezionate"
        ):
            st.rerun()

        # Generate PDF button (always enabled, 0 metrics is valid)
        button_label = f"Genera Report PDF ({total_selected})"
        if st.button(
            button_label,
            icon=":material/picture_as_pdf:",
            use_container_width=True,
            help="Genera report PDF. Seleziona metriche dalle card per includerle nel report."
        ):
            st.session_state.generate_pdf_report = True

        # Show download button if PDF was generated
        if st.session_state.get('pdf_report_bytes'):
            st.download_button(
                label="Scarica PDF Generato",
                data=st.session_state.pdf_report_bytes,
                file_name=st.session_state.get('pdf_report_filename', 'report.pdf'),
                mime="application/pdf",
                use_container_width=True,
                type="secondary",
                key="download_pdf_report"
            )

    # Playing style cluster box + xG by opponent cluster
    playing_style = get_team_playing_style(team_id, manager_id)
    xg_by_cluster = get_xg_by_opponent_cluster(team_id, manager_name)

    # Layout: Cluster box (left) + xG tabs (right)
    col_cluster, col_xg = st.columns([1, 2.5])

    with col_cluster:
        if playing_style and playing_style.get('cluster_name'):
            cluster_name = playing_style['cluster_name']
        else:
            cluster_name = "Non disponibile"

        st.markdown(f'''
            <div class="cluster-box">
                <div class="cluster-box-title">Stile di Gioco</div>
                <div class="cluster-box-name">{cluster_name}</div>
            </div>
        ''', unsafe_allow_html=True)
        if st.button("Approfondisci Clustering", icon=":material/hub:", use_container_width=True):
            st.switch_page("pages/_stili_di_gioco.py")

    with col_xg:
        if xg_by_cluster:
            st.markdown("**xG medio per cluster avversario**")
            cluster_names = ["Possesso Dominante", "Pressing e Verticalità", "Blocco Basso e Ripartenza", "Ampiezza e Inserimenti"]
            tabs = st.tabs(cluster_names)

            for i, tab in enumerate(tabs):
                with tab:
                    cluster_name = cluster_names[i]
                    if cluster_name in xg_by_cluster:
                        stats = xg_by_cluster[cluster_name]
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.markdown(f'''
                                <div class="xg-cluster-card">
                                    <div class="xg-value xg-for">{stats["xg_for_avg"]:.2f}</div>
                                    <div class="xg-label">xG Fatti</div>
                                </div>
                            ''', unsafe_allow_html=True)
                        with col2:
                            st.markdown(f'''
                                <div class="xg-cluster-card">
                                    <div class="xg-value xg-against">{stats["xg_against_avg"]:.2f}</div>
                                    <div class="xg-label">xG Subiti</div>
                                </div>
                            ''', unsafe_allow_html=True)
                        with col3:
                            diff = stats["xg_diff"]
                            diff_color = "#10b981" if diff > 0 else "#ef4444"
                            diff_sign = "+" if diff > 0 else ""
                            st.markdown(f'''
                                <div class="xg-cluster-card">
                                    <div class="xg-value" style="color:{diff_color}">{diff_sign}{diff:.2f}</div>
                                    <div class="xg-label">Differenza</div>
                                    <div class="xg-matches">{stats["matches"]} partite</div>
                                </div>
                            ''', unsafe_allow_html=True)
                    else:
                        st.caption("Nessuna partita contro questo cluster")

    # Get team metrics and other data
    team_metrics = data['team_metrics'][
        (data['team_metrics']['team_id'] == team_id) &
        (data['team_metrics']['manager_id'] == manager_id)
    ]

    total_combinations = len(data['combinations'])

    # Formation stats
    formation_stats = get_formation_stats(team_id, manager_name)
    formation = formation_stats.get('primary_formation', '4-3-3') if formation_stats else '4-3-3'

    # Get top 11 players
    try:
        player_names, player_id_to_slot = get_top_11_players(
            data['players'],
            data.get('player_minutes'),
            team_id,
            manager_id,
            formation,
            matches_df=data.get('matches'),
            teams_df=data.get('teams'),
            manager_name=manager_name,
            formation_coordinates=FORMATION_COORDINATES,
            position_mapping=POSITION_MAPPING
        )
    except Exception as e:
        player_names = {}
        player_id_to_slot = {}

    # Get all available players for substitution
    try:
        all_available_players = get_all_available_players(
            data.get('player_minutes'),
            team_id,
            matches_df=data.get('matches'),
            teams_df=data.get('teams'),
            manager_name=manager_name
        )
    except Exception:
        all_available_players = []

    # Apply player overrides
    if st.session_state.player_overrides and all_available_players:
        player_names, player_id_to_slot = apply_player_overrides(
            player_names, player_id_to_slot,
            st.session_state.player_overrides,
            all_available_players
        )

    # Player faces and SofaScore ratings (per team+manager)
    player_faces = get_player_faces_by_slot(player_id_to_slot)
    player_ratings = get_player_ratings_by_slot(
        team_id=team_id,
        manager_name=manager_name,
        matches_df=data.get('matches'),
        teams_df=data.get('teams'),
        player_id_to_slot=player_id_to_slot
    )

    # Radar values for AI profile
    radar_values = calculate_radar_values(team_metrics)
    metrics_by_category_df = get_metrics_by_category(team_metrics)

    # Get playing style string
    playing_style_str = "Equilibrato"
    if playing_style and playing_style.get('cluster_name'):
        playing_style_str = playing_style['cluster_name']

    # PDF Report Generation (direct, no dialog)
    if st.session_state.get('generate_pdf_report', False):
        # Generate base64 images for PDF
        try:
            logo_base64 = get_team_logo_base64(team_id)
            radar_base64 = render_radar_to_base64(team_metrics)
            pitch_base64 = render_formation_to_base64(
                formation,
                player_names=player_names,
                player_faces=player_faces,
                player_ratings=player_ratings,
                show_ratings=True,
                width=1200,
                height=900
            )
        except Exception:
            logo_base64 = None
            radar_base64 = None
            pitch_base64 = None

        # Get cached team analysis if available
        profile_cache_key = (team_id, manager_id)
        cached_profile = st.session_state.cached_team_profile.get(profile_cache_key)
        team_analysis = cached_profile.analysis if cached_profile else None

        # Get cached player profiles if available
        player_cache_key = (team_id, manager_id, tuple(sorted(player_id_to_slot.items())))
        player_profiles = st.session_state.get('cached_player_profiles', {}).get(player_cache_key, [])

        # Check if player profiles are empty and user hasn't confirmed to skip
        if not player_profiles and not st.session_state.get('pdf_skip_players_confirmed', False):
            st.session_state.generate_pdf_report = False
            st.session_state.show_pdf_no_players_dialog = True
            st.rerun()

        # Import PDF generator
        from services.pdf_report import PDFReportConfig, PDFReportGenerator, PDFReportError

        # Build config from session state selections
        config = PDFReportConfig(
            team_id=team_id,
            manager_id=manager_id,
            team_name=team_name,
            manager_name=manager_name,
            matches_count=int(matches_count),
            formation=formation,
            cluster_name=playing_style_str,
            formation_stats=formation_stats,
            positive_metrics=list(st.session_state.pdf_selected_metrics.get('positive', set())),
            average_metrics=list(st.session_state.pdf_selected_metrics.get('average', set())),
            negative_metrics=list(st.session_state.pdf_selected_metrics.get('negative', set())),
            positive_detail_metrics=list(st.session_state.pdf_detail_metrics.get('positive', set())),
            average_detail_metrics=list(st.session_state.pdf_detail_metrics.get('average', set())),
            negative_detail_metrics=list(st.session_state.pdf_detail_metrics.get('negative', set())),
        )

        try:
            with st.spinner("Generazione report PDF in corso..."):
                generator = PDFReportGenerator(
                    config=config,
                    data=data,
                    team_metrics=team_metrics,
                    player_metrics=data['player_metrics'],
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

                pdf_bytes = generator.generate()

                st.session_state.pdf_report_bytes = pdf_bytes
                st.session_state.pdf_report_filename = f"report_{team_name.replace(' ', '_')}_{manager_name.replace(' ', '_')}.pdf"
                st.success("Report PDF generato con successo!")

        except PDFReportError as e:
            st.error(f"Errore generazione PDF: {str(e)}")
        except Exception as e:
            st.error(f"Errore imprevisto: {str(e)}")
        finally:
            st.session_state.generate_pdf_report = False
            st.session_state.pdf_skip_players_confirmed = False
            st.rerun()

    # Main dashboard layout
    if st.session_state.selected_metric is None:
        # Two column layout: Pitch (left) | Metrics (right)
        # ORDINE RENDERING: col_metrics viene processato PRIMA di col_pitch
        # Questo garantisce che Rank Metriche sia visualizzato PRIMA dei contenuti AI
        col_pitch, col_metrics = st.columns([1.4, 1])

        with col_metrics:
            st.markdown("### :material/insights: Rank Metriche Squadra")
            render_metrics_with_filter(team_metrics, total_combinations, all_team_metrics=data['team_metrics'])

        with col_pitch:
            # ============================================================
            # CONTENUTI PRINCIPALI (prima) + ANALISI AI (dopo)
            # ============================================================

            # === Performance Scatterplot (sopra il radar) ===
            if 'performances' in data and len(data['performances']) > 0:
                render_performance_section(
                    performances_df=data['performances'],
                    team_id=team_id,
                    manager_id=manager_id,
                    team_name=team_name,
                    valid_pairs=data.get('valid_pairs', set())
                )
                st.divider()

            # === Fasi di Gioco (tra Mappa Prestazioni e Profilo Tattico) ===
            render_game_phases_section(team_metrics, total_combinations)
            st.divider()

            render_radar_section(
                data=data,
                team_metrics=team_metrics,
                team_id=team_id,
                manager_name=manager_name,
                manager_id=manager_id,
                team_name=team_name
            )

            st.markdown(f"**Stile:** :blue-background[{playing_style_str}]")

            # Placeholder per Analisi Tattica Squadra: verrà riempito DOPO
            # il rendering della formazione, ma apparirà QUI (sopra la formazione)
            team_ai_placeholder = st.empty()

            st.divider()

            # Formation section - carica subito
            st.markdown("### :material/stadium: Formazione")

            if formation_stats and formation_stats.get('formations'):
                formations = formation_stats['formations']

                formations_html = '<div class="formation-container">'
                primary = formations[0]
                formations_html += (
                    f'<div class="formation-primary">'
                    f'{primary["formation"]}'
                    f'<span class="formation-pct">{primary["percentage"]}%</span>'
                    f'</div>'
                )

                for f in formations[1:3]:
                    if f['percentage'] >= 5:
                        formations_html += (
                            f'<div class="formation-secondary">'
                            f'{f["formation"]}'
                            f'<span class="formation-pct">{f["percentage"]}%</span>'
                            f'</div>'
                        )

                formations_html += '</div>'
                st.markdown(formations_html, unsafe_allow_html=True)

                # Timeline in popover
                if formation_stats.get('timeline'):
                    with st.popover("Cronologia partite", use_container_width=True):
                        timeline = formation_stats['timeline']
                        formation_colors = {
                            '3-5-2': ('#1a472a', '#e8f5e9', 'white'),
                            '3-4-3': ('#1565c0', '#e3f2fd', 'white'),
                            '3-4-1-2': ('#7b1fa2', '#f3e5f5', 'white'),
                            '4-3-3': ('#c62828', '#ffebee', 'white'),
                            '4-4-2': ('#ef6c00', '#fff3e0', 'white'),
                            '4-2-3-1': ('#00838f', '#e0f7fa', 'white'),
                            '4-1-4-1': ('#558b2f', '#f1f8e9', 'white'),
                            '4-1-2-1-2': ('#5d4037', '#efebe9', 'white'),
                            '4-3-1-2': ('#455a64', '#eceff1', 'white'),
                            '5-3-2': ('#ad1457', '#fce4ec', 'white'),
                            '5-4-1': ('#6a1b9a', '#f3e5f5', 'white'),
                        }
                        default_color = ('#64748b', '#f1f5f9', 'white')

                        timeline_html = '<div class="formation-timeline">'
                        for match in timeline:
                            mw = match['match_week']
                            f = match['formation']
                            opponent = match.get('opponent', '')
                            colors = formation_colors.get(f, default_color)
                            bg_color, light_bg, text_color = colors

                            formation_parts = f.split('-')
                            vertical_formation = ''.join(
                                f'<span>{part}</span>' for part in formation_parts
                            )

                            timeline_html += (
                                f'<div class="formation-match-wrapper">'
                                f'<div class="formation-match" '
                                f'style="background:linear-gradient(135deg, {bg_color} 0%, {bg_color}dd 100%);color:{text_color};" '
                                f'title="Giornata {mw}: {opponent} - {f}">'
                                f'<div class="formation-match-code" style="color:{text_color};">{vertical_formation}</div>'
                                f'</div>'
                                f'<span class="formation-match-week">G{mw}</span>'
                                f'</div>'
                            )
                        timeline_html += '</div>'
                        st.markdown(timeline_html, unsafe_allow_html=True)
                        st.caption(f"Totale: {formation_stats['total_matches']} partite")
            else:
                st.markdown(f"**{formation}**")

            render_formation(
                formation,
                player_values=None,
                player_names=player_names,
                player_faces=player_faces,
                player_ratings=player_ratings,
                show_ratings=True
            )

            # Player swap expander
            with st.expander("🔄 Sostituisci giocatore", expanded=False):
                st.caption("Seleziona un titolare da sostituire e scegli una riserva")

                slot_to_player_id = {v: k for k, v in player_id_to_slot.items()}
                starting_11_ids = set(player_id_to_slot.keys())

                bench_players = [p for p in all_available_players if p['player_id'] not in starting_11_ids]
                bench_options = {
                    f"{p['surname']} ({p['position'][:3].upper()}) - {p['total_minutes']} min": p['player_id']
                    for p in bench_players
                }
                bench_options_list = ["-- Seleziona riserva --"] + list(bench_options.keys())

                col_slot, col_player = st.columns(2)

                with col_slot:
                    slot_options = {}
                    for slot, surname in sorted(player_names.items()):
                        current_pid = slot_to_player_id.get(slot)
                        current_player = next((p for p in all_available_players if p['player_id'] == current_pid), None)
                        pos_label = current_player['position'][:3].upper() if current_player else "???"
                        mins = current_player['total_minutes'] if current_player else 0
                        slot_options[f"{surname} ({pos_label}) - {mins} min"] = slot

                    selected_slot_label = st.selectbox(
                        "Titolare da sostituire",
                        options=list(slot_options.keys()),
                        key="swap_slot_select"
                    )
                    selected_slot = slot_options.get(selected_slot_label)

                with col_player:
                    new_player_label = st.selectbox(
                        "Riserva da inserire",
                        options=bench_options_list,
                        key="swap_player_select"
                    )

                if st.button("✓ Applica sostituzione", use_container_width=True):
                    if new_player_label != "-- Seleziona riserva --" and selected_slot is not None:
                        new_player_id = bench_options.get(new_player_label)
                        if new_player_id:
                            st.session_state.player_overrides[selected_slot] = new_player_id
                            st.rerun()

                if st.session_state.player_overrides:
                    if st.button("↩ Ripristina formazione originale", use_container_width=True):
                        st.session_state.player_overrides = {}
                        st.rerun()

            # Riempie il placeholder dell'analisi squadra DOPO la formazione
            with team_ai_placeholder.container():
                st.markdown("### :material/insights: Analisi Tattica Squadra")
                profile_cache_key = (team_id, manager_id)
                if profile_cache_key in st.session_state.cached_team_profile:
                    st.markdown(st.session_state.cached_team_profile[profile_cache_key].analysis)
                else:
                    with st.spinner("Generazione analisi tattica..."):
                        metrics_by_category_text = {}
                        for cat, df in metrics_by_category_df.items():
                            if len(df) > 0:
                                lines = []
                                for _, row in df.head(5).iterrows():
                                    metric_display = METRIC_NAMES.get(row['metric_name'], row['metric_name'])
                                    lines.append(f"- {metric_display}: {row['percentile']:.0f}° percentile")
                                metrics_by_category_text[cat] = "\n".join(lines)

                        team_profile = generate_team_tactical_profile(
                            team_name=team_name,
                            manager_name=manager_name,
                            cluster_name=playing_style_str,
                            radar_values=radar_values,
                            metrics_by_category=metrics_by_category_text
                        )

                        if team_profile is None:
                            team_profile = generate_fallback_team_profile(
                                team_name=team_name,
                                manager_name=manager_name,
                                cluster_name=playing_style_str,
                                radar_values=radar_values
                            )

                        st.session_state.cached_team_profile[profile_cache_key] = team_profile
                    st.markdown(team_profile.analysis)

            st.divider()

            # Player Analysis Section - isolata per evitare rerun di tutta la pagina
            render_player_analysis_section(
                data=data,
                team_id=team_id,
                manager_id=manager_id,
                player_id_to_slot=player_id_to_slot,
                player_names=player_names,
                formation=formation
            )

    else:
        # Metric detail view
        metric_name = st.session_state.selected_metric
        display_name = METRIC_NAMES.get(metric_name, metric_name.replace('_', ' ').title())

        if st.button("← Torna alla dashboard"):
            st.session_state.selected_metric = None
            st.rerun()

        metric_info = team_metrics[team_metrics['metric_name'] == metric_name]
        if len(metric_info) > 0:
            mi = metric_info.iloc[0]
            rank = int(mi['metric_rank'])
            is_str = is_strength(rank, total_combinations)
            is_avg = is_average(rank, total_combinations)
            is_weak = is_weakness(rank, total_combinations)

            badge = ""
            badge_color = ""
            if is_str:
                badge = "POSITIVA"
                badge_color = "#10b981"
            elif is_avg:
                badge = "NELLA MEDIA"
                badge_color = "#f59e0b"
            elif is_weak:
                badge = "NEGATIVA"
                badge_color = "#ef4444"

            # Determine normalization label based on metric type
            # Comprehensive mapping based on how each metric is calculated
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
                'tackles': 'per 100 pass. avv. in dif.',
                'interceptions': 'per 100 pass. avv. in dif.',
                'clearances': 'per 100 pass. avv. in dif.',
                'blocks': 'per 100 pass. avv. in dif.',
                'ground_duels_defensive': 'per 100 pass. avv. in dif.',
                'opp_passes_def_third': 'per 90 min',

                # Per 100 long passes (aerial duels)
                'aerial_duels_offensive': 'per 100 lanci nostri',
                'aerial_duels_defensive': 'per 100 lanci avv.',
                'aerial_duels_open_play': 'per 90 min',
                'aerial_duels_set_pieces': 'per 90 min',

                # Per 100 lost balls (ground duels offensive)
                'ground_duels_offensive': 'per 100 palle perse',

                # Per corners/set pieces
                'sot_per_100_corners': 'per 100 corner',
                'sot_per_100_indirect_sp': 'per 100 palle inattive',

                # PPDA (ratio - lower is more aggressive)
                'ppda': 'tasso',

                # Per touch
                'turnovers_per_touch': 'per tocco',
                'shots_per_box_touch': 'per tocco in area',

                # xA per key pass
                'xa_per_key_pass': 'per pass. chiave',
                'goals_per_xa': 'gol per xA',

                # Difference metrics (no normalization needed)
                'xg_goals_difference': 'differenza',
                'xga_difference': 'differenza',
            }

            norm_label = METRIC_NORMALIZATIONS.get(metric_name, 'per 90 min')
            if norm_label != '%':
                norm_label = f"({norm_label})"
            else:
                norm_label = "(%)"

            st.markdown(f'''
            <div class="metric-header">
                <h1 style="font-size:2.2rem;margin-bottom:0.3rem;">{display_name} <span style="font-size:1rem;color:#9ca3af;font-weight:400;">{norm_label}</span></h1>
                <p style="font-size:1.2rem;margin-top:0;">Posizione <strong>#{rank}</strong> su {total_combinations} squadre
                <span style="background:{badge_color};padding:4px 12px;border-radius:4px;font-size:0.85rem;margin-left:10px;color:white;">{badge}</span></p>
            </div>
            ''', unsafe_allow_html=True)

            # Layout for metric detail - THREE columns: Teams | Players | Pitch
            col_teams, col_players, col_pitch = st.columns([1, 1, 1.3])

            with col_teams:
                st.markdown('<div class="section-title">Classifica Squadre</div>', unsafe_allow_html=True)
                all_team_metrics = data['team_metrics']
                render_full_team_ranking(
                    all_team_metrics,
                    metric_name,
                    team_id,
                    manager_id,
                    data['combinations']
                )

            with col_players:
                st.markdown('<div class="section-title">Contributo Giocatori</div>', unsafe_allow_html=True)
                # Filter player metrics by team_id and manager_id
                player_metrics_filtered = data['player_metrics'][
                    (data['player_metrics']['team_id'] == team_id) &
                    (data['player_metrics']['manager_id'] == manager_id) &
                    (data['player_metrics']['metric_name'] == metric_name)
                ]
                # Pass all player metrics for correct minutes threshold calculation
                render_all_players_ranking(
                    player_metrics_filtered,
                    metric_name,
                    all_player_metrics=data['player_metrics'],
                    team_id=team_id
                )

            with col_pitch:
                st.markdown('<div class="section-title">Contributo nel Campo</div>', unsafe_allow_html=True)

                # Map player contributions to formation slots
                slot_values = {}
                if len(player_metrics_filtered) > 0:
                    for _, row in player_metrics_filtered.iterrows():
                        pid = row['player_id']
                        if pid in player_id_to_slot:
                            slot = player_id_to_slot[pid]
                            slot_values[slot] = row['contribution_percentage']

                render_formation(
                    formation,
                    player_values=slot_values,
                    player_names=player_names,
                    selected_metric=metric_name,
                    player_faces=player_faces
                )


if __name__ == "__main__":
    dashboard_main()
else:
    # When imported as a page, run the main function
    dashboard_main()
