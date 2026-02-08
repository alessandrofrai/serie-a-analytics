"""
Playing Styles Analysis Page.

This page visualizes the K-means clustering results for Serie A 2015-2016
team+manager combinations, showing playing style classifications.
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import plotly.express as px
import plotly.graph_objects as go

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from clustering.playing_style import PlayingStyleClusterer, load_clusterer_from_data

# Page configuration
st.set_page_config(
    page_title="Stili di Gioco - Serie A 2015-2016",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        text-align: center;
        padding: 1rem 1.5rem;
        background: linear-gradient(135deg, #0c1929 0%, #1a2d4a 50%, #243b5c 100%);
        color: white;
        border-radius: 12px;
        margin-bottom: 1.25rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    .cluster-card {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border: 1px solid #e5e7eb;
    }

    .cluster-header {
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }

    .cluster-description {
        color: #6b7280;
        font-size: 0.9rem;
        margin-bottom: 0.75rem;
    }

    .team-badge {
        display: inline-block;
        padding: 4px 10px;
        background: #f3f4f6;
        border-radius: 16px;
        font-size: 0.85rem;
        margin: 3px;
        border: 1px solid #e5e7eb;
    }

    .metric-explanation {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1a2d4a;
        margin-bottom: 1rem;
    }

    .blue-gradient-section {
        background: linear-gradient(135deg, #0c1929 0%, #1a2d4a 50%, #243b5c 100%);
        padding: 1.25rem 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    .blue-gradient-section h3 {
        color: white !important;
        margin-bottom: 0.75rem;
        font-weight: 700;
    }

    /* Section headers in intense blue */
    [data-testid="stMarkdown"] h3 {
        color: #0c1929 !important;
        font-weight: 700;
    }

    /* Multiselect styling */
    [data-testid="stMultiSelect"] label {
        color: #0c1929 !important;
        font-weight: 600;
    }

    /* Container borders with blue accent */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #1a2d4a !important;
        border-width: 1px !important;
    }

    /* Expander styling with blue */
    [data-testid="stExpander"] {
        border-color: #1a2d4a !important;
    }

    [data-testid="stExpander"] summary {
        color: #0c1929 !important;
    }

    /* Selectbox and multiselect pill styling */
    [data-testid="stMultiSelect"] [data-baseweb="tag"] {
        background-color: #1a2d4a !important;
    }
</style>
""", unsafe_allow_html=True)

# Cluster colors
CLUSTER_COLORS = {
    0: '#10b981',  # Green
    1: '#f59e0b',  # Orange
    2: '#3b82f6',  # Blue
    3: '#ef4444',  # Red
    4: '#8b5cf6',  # Purple
    5: '#ec4899',  # Pink
}


@st.cache_resource(show_spinner="Caricamento dati...")
def get_clusterer():
    """Load and cache the clusterer with results."""
    clusterer = load_clusterer_from_data(min_matches=5)
    clusterer.run_full_pipeline(k=4, use_pca=True)
    return clusterer


def render_pca_scatter(clusterer: PlayingStyleClusterer):
    """Render PCA scatter plot of all teams."""
    pca_data = clusterer.get_all_teams_pca()

    if len(pca_data) == 0:
        st.warning("Dati PCA non disponibili")
        return

    # Create display name
    pca_data['display_name'] = pca_data.apply(
        lambda r: f"{r['team_name']} ({r['manager_name'].split()[-1]})",
        axis=1
    )

    # Create scatter plot
    fig = px.scatter(
        pca_data,
        x='pca_1',
        y='pca_2',
        color='cluster_name',
        hover_name='display_name',
        hover_data={
            'pca_1': ':.2f',
            'pca_2': ':.2f',
            'matches_count': True,
            'cluster_name': False
        },
        color_discrete_sequence=list(CLUSTER_COLORS.values()),
        title='Mappa degli Stili di Gioco (PCA)',
    )

    fig.update_traces(
        marker=dict(size=12, line=dict(width=1, color='white')),
        textposition='top center'
    )

    fig.update_layout(
        xaxis_title='Componente Principale 1',
        yaxis_title='Componente Principale 2',
        legend_title='Stile di Gioco',
        height=500,
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.25,
            xanchor='center',
            x=0.5
        )
    )

    st.plotly_chart(fig, use_container_width=True)


def render_radar_chart(clusterer: PlayingStyleClusterer, cluster_ids: list):
    """Render radar chart comparing selected clusters."""
    if not cluster_ids:
        st.info("Seleziona almeno un cluster per visualizzare il radar chart")
        return

    # Get radar data for each cluster
    fig = go.Figure()

    for cluster_id in cluster_ids:
        radar_data = clusterer.get_cluster_radar_data(cluster_id)
        if not radar_data:
            continue

        cluster_info = clusterer.cluster_info.get(cluster_id, {})
        cluster_name = cluster_info.get('name', f'Cluster {cluster_id}')

        categories = list(radar_data.keys())
        values = list(radar_data.values())
        # Close the radar chart
        values.append(values[0])
        categories.append(categories[0])

        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            name=cluster_name,
            fill='toself',
            opacity=0.6,
            line=dict(color=CLUSTER_COLORS.get(cluster_id, '#666'))
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True,
        title='Profilo Tattico per Stile',
        height=450,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.2,
            xanchor='center',
            x=0.5
        )
    )

    st.plotly_chart(fig, use_container_width=True)


def render_cluster_cards(clusterer: PlayingStyleClusterer):
    """Render cards for each cluster."""
    if clusterer.cluster_info is None:
        st.warning("Informazioni cluster non disponibili")
        return

    # Sort clusters by number of teams (descending)
    sorted_clusters = sorted(
        clusterer.cluster_info.items(),
        key=lambda x: x[1]['n_teams'],
        reverse=True
    )

    for cluster_id, info in sorted_clusters:
        color = CLUSTER_COLORS.get(cluster_id, '#666')

        with st.container(border=True):
            # Header with color indicator
            col_indicator, col_title, col_count = st.columns([0.5, 5, 1])

            with col_indicator:
                st.markdown(
                    f'<div style="width:24px;height:24px;background:{color};'
                    f'border-radius:50%;margin-top:4px;"></div>',
                    unsafe_allow_html=True
                )

            with col_title:
                st.markdown(f"### {info['name']}")

            with col_count:
                st.metric("Squadre", info['n_teams'])

            # Description
            st.caption(info['description'])

            # Characteristics as badges
            if info['characteristics']:
                char_badges = " ".join([
                    f":blue-badge[{c}]" for c in info['characteristics'][:5]
                ])
                st.markdown(char_badges)

            # Teams
            with st.expander(f"Visualizza {info['n_teams']} squadre"):
                teams_html = " ".join([
                    f'<span class="team-badge">{team}</span>'
                    for team in info['teams']
                ])
                st.markdown(teams_html, unsafe_allow_html=True)


def render_metrics_explanation():
    """Render explanation of the metrics used."""
    st.markdown("""
    <div class="metric-explanation">
    <strong>Metriche utilizzate per la classificazione:</strong><br>
    <small>
    <b>Possesso:</b> % possesso, passaggi progressivi, dribbling<br>
    <b>Pressing:</b> intensità (PPDA), pressing alto, contro-pressing<br>
    <b>Transizioni:</b> contropiedi, costruzione dal basso, attacchi rapidi<br>
    <b>Attacco:</b> xG, cross, tocchi in area<br>
    <b>Difesa:</b> contrasti, intercettazioni, duelli aerei
    </small>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main page function."""
    # Back button
    if st.button("← Indietro"):
        st.switch_page("app.py")

    st.markdown('<div class="main-header">Stili di Gioco - Serie A 2015-2016</div>', unsafe_allow_html=True)

    # Load clusterer
    with st.spinner("Caricamento analisi stili di gioco..."):
        clusterer = get_clusterer()

    if clusterer.cluster_info is None:
        st.error("Errore nel caricamento dei dati di clustering")
        return

    # Two columns layout
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        render_pca_scatter(clusterer)
        render_metrics_explanation()

        # Comparison section
        st.markdown("### Confronta gli Stili di Gioco")

        cluster_options = {
            info['name']: cluster_id
            for cluster_id, info in clusterer.cluster_info.items()
        }

        selected_styles = st.multiselect(
            "Seleziona stili da confrontare",
            options=list(cluster_options.keys()),
            default=list(cluster_options.keys())
        )

        selected_ids = [cluster_options[name] for name in selected_styles]

        if selected_ids:
            render_radar_chart(clusterer, selected_ids)

    with col_right:
        st.markdown("### Stili Identificati")
        render_cluster_cards(clusterer)


if __name__ == "__main__":
    main()
