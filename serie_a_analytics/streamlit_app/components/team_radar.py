"""
Team Radar Chart Component

Renders a radar chart showing team+manager performance across 6 grouped metric categories:
- Attacco (Attack)
- Difesa (Defense)
- Possesso (Possession)
- Pressing
- Palle Inattive (Set Pieces)
- Transizioni (Transitions)

Values are based on average percentiles within each category.
Uses Plotly for elegant, interactive visualization.
"""

import streamlit as st
import plotly.graph_objects as go
from typing import Dict
import pandas as pd


# Map metric categories to radar groups
# Based on actual categories in team_metrics.csv: attacking, defending, possession, pressing, set_pieces, transition
RADAR_CATEGORY_MAPPING = {
    'Attacco': ['attacking'],
    'Difesa': ['defending'],
    'Possesso': ['possession'],
    'Pressing': ['pressing'],
    'Palle Inattive': ['set_pieces'],
    'Transizioni': ['transition'],
}

# Italian labels for display
RADAR_LABELS = ['Attacco', 'Difesa', 'Possesso', 'Pressing', 'Palle Inattive', 'Transizioni']


def calculate_radar_values(team_metrics: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate radar chart values from team metrics.

    Args:
        team_metrics: DataFrame with team metrics (filtered for specific team+manager)

    Returns:
        Dict mapping category name to average percentile (0-100)
    """
    if len(team_metrics) == 0:
        return {label: 50.0 for label in RADAR_LABELS}

    radar_values = {}

    for radar_label, metric_categories in RADAR_CATEGORY_MAPPING.items():
        # Get all metrics belonging to these categories
        category_metrics = team_metrics[
            team_metrics['metric_category'].isin(metric_categories)
        ]

        if len(category_metrics) > 0 and 'percentile' in category_metrics.columns:
            # Calculate average percentile for this category
            avg_percentile = category_metrics['percentile'].mean()
            radar_values[radar_label] = avg_percentile
        else:
            radar_values[radar_label] = 50.0  # Default to middle

    return radar_values


def get_metrics_by_category(team_metrics: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Group team metrics by radar category for detailed analysis.

    Args:
        team_metrics: DataFrame with team metrics

    Returns:
        Dict mapping radar category name to DataFrame of metrics
    """
    result = {}

    for radar_label, metric_categories in RADAR_CATEGORY_MAPPING.items():
        category_metrics = team_metrics[
            team_metrics['metric_category'].isin(metric_categories)
        ].copy()

        if len(category_metrics) > 0:
            result[radar_label] = category_metrics.sort_values('percentile', ascending=False)

    return result


def render_team_radar(
    team_metrics: pd.DataFrame,
    team_name: str = "",
    manager_name: str = "",
    color: str = '#3b82f6',
    height: int = 400,
    show_values: bool = True
):
    """
    Render a Plotly radar chart for team+manager performance.

    Args:
        team_metrics: DataFrame with team metrics (filtered for specific team+manager)
        team_name: Name of the team
        manager_name: Name of the manager
        color: Color for the radar fill
        height: Chart height in pixels
        show_values: Whether to show values on the chart
    """
    # Calculate radar values
    radar_values = calculate_radar_values(team_metrics)

    # Prepare data for radar
    categories = RADAR_LABELS
    values = [radar_values.get(cat, 50.0) for cat in categories]

    # Create labels with values if show_values is True (values are not percentages)
    if show_values:
        categories_with_values = [f"{cat}<br><b>{val:.0f}</b>" for cat, val in zip(categories, values)]
    else:
        categories_with_values = categories

    # Close the radar polygon
    values_closed = values + [values[0]]
    categories_closed = categories_with_values + [categories_with_values[0]]

    # Create figure
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        name=f"{team_name}" if team_name else "Team",
        fill='toself',
        opacity=0.5,
        line=dict(color=color, width=2.5),
        fillcolor=color,
        hovertemplate='%{theta}: %{r:.0f}<extra></extra>'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickvals=[25, 50, 75, 100],
                ticktext=['25', '50', '75', '100'],
                tickfont=dict(size=10, color='#888'),
                gridcolor='#d1d5db',
                linecolor='#d1d5db',
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color='#333'),
                gridcolor='#e5e7eb',
                linecolor='#d1d5db',
            ),
            bgcolor='rgba(0,0,0,0)',
        ),
        showlegend=False,
        height=height,
        margin=dict(l=80, r=80, t=40, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def render_team_radar_minimal(
    team_metrics: pd.DataFrame,
    height: int = 380,
    color: str = '#3b82f6'
):
    """
    Render a radar chart for dashboard display with values.

    Args:
        team_metrics: DataFrame with team metrics
        height: Height of the chart in pixels
        color: Color for the radar fill
    """
    render_team_radar(team_metrics, height=height, color=color, show_values=True)


def render_team_radar_comparison(
    team_metrics_a: pd.DataFrame,
    team_metrics_b: pd.DataFrame,
    label_a: str,
    label_b: str,
    color_a: str = '#3b82f6',
    color_b: str = '#ef4444',
    height: int = 380,
    show_values: bool = True
):
    """
    Render a radar chart comparing two team+manager combinations.
    """
    radar_a = calculate_radar_values(team_metrics_a)
    radar_b = calculate_radar_values(team_metrics_b)

    categories = RADAR_LABELS
    values_a = [radar_a.get(cat, 50.0) for cat in categories]
    values_b = [radar_b.get(cat, 50.0) for cat in categories]

    values_a_closed = values_a + [values_a[0]]
    values_b_closed = values_b + [values_b[0]]
    categories_closed = categories + [categories[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values_a_closed,
        theta=categories_closed,
        name=label_a,
        fill='toself',
        opacity=0.45,
        line=dict(color=color_a, width=2.5),
        fillcolor=color_a,
        hovertemplate='%{theta}: %{r:.0f}<extra></extra>'
    ))

    fig.add_trace(go.Scatterpolar(
        r=values_b_closed,
        theta=categories_closed,
        name=label_b,
        fill='toself',
        opacity=0.35,
        line=dict(color=color_b, width=2.5),
        fillcolor=color_b,
        hovertemplate='%{theta}: %{r:.0f}<extra></extra>'
    ))

    tickvals = None
    ticktext = None
    if show_values:
        # Build axis labels like single chart, but with "blue / red" values
        tickvals = categories
        ticktext = [
            f"{cat}<br>"
            f"<span style='color:{color_a};font-weight:600'>{val_a:.0f}</span>"
            f"<span style='color:#6b7280'> / </span>"
            f"<span style='color:{color_b};font-weight:600'>{val_b:.0f}</span>"
            for cat, val_a, val_b in zip(categories, values_a, values_b)
        ]

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickvals=[25, 50, 75, 100],
                ticktext=['25', '50', '75', '100'],
                tickfont=dict(size=10, color='#888'),
                gridcolor='#d1d5db',
                linecolor='#d1d5db',
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color='#333'),
                tickmode="array" if ticktext else "auto",
                tickvals=tickvals,
                ticktext=ticktext,
                gridcolor='#e5e7eb',
                linecolor='#d1d5db',
            ),
            bgcolor='rgba(0,0,0,0)',
        ),
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.05,
            xanchor='center',
            x=0.5,
            font=dict(size=11),
        ),
        height=height,
        margin=dict(l=60, r=60, t=50, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def render_radar_to_base64(
    team_metrics: pd.DataFrame,
    width: int = 400,
    height: int = 400,
    color: str = '#3b82f6'
) -> str:
    """
    Generate radar chart and return as base64 PNG for PDF export.

    Args:
        team_metrics: DataFrame with team metrics (filtered for specific team+manager)
        width: Image width in pixels
        height: Image height in pixels
        color: Color for the radar fill

    Returns:
        Base64 data URL string (data:image/png;base64,...)
    """
    import io
    import base64
    import matplotlib.pyplot as plt
    import numpy as np

    # Calculate radar values
    radar_values = calculate_radar_values(team_metrics)

    # Prepare data
    categories = RADAR_LABELS
    values = [radar_values.get(cat, 50.0) for cat in categories]

    # Number of variables
    N = len(categories)

    # Compute angle for each category
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # Complete the loop

    values_plot = values + values[:1]  # Complete the loop

    # Force a square canvas to avoid elliptical distortion in PDF scaling
    size = min(width, height)
    fig, ax = plt.subplots(figsize=(size/100, size/100), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    # Draw the radar
    ax.plot(angles, values_plot, 'o-', linewidth=2.5, color=color)
    ax.fill(angles, values_plot, alpha=0.35, color=color)

    # Set the labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=9, fontweight='bold')

    # Set radial limits
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(['25', '50', '75', '100'], fontsize=8, color='#666')

    # Add value labels on the radar points
    for angle, value, cat in zip(angles[:-1], values, categories):
        ax.annotate(
            f'{value:.0f}',
            xy=(angle, value),
            xytext=(angle, value + 8),
            ha='center',
            va='bottom',
            fontsize=8,
            fontweight='bold',
            color=color
        )

    # Style the grid
    ax.grid(True, color='#d1d5db', linestyle='-', linewidth=0.5)
    ax.spines['polar'].set_color('#d1d5db')

    # Keep margins inside a square canvas to prevent cropping and distortion
    # Extra padding to avoid label clipping on the sides
    fig.subplots_adjust(left=0.18, right=0.82, top=0.88, bottom=0.12)

    # Export to base64 (avoid tight bbox that can change aspect ratio)
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=150,
                facecolor='white', edgecolor='none')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close(fig)

    return f"data:image/png;base64,{img_base64}"


def render_team_radar_with_comparison(
    team_metrics: pd.DataFrame,
    cluster_avg_values: Dict[str, float] = None,
    team_name: str = "",
    cluster_name: str = "",
    height: int = 350
):
    """
    Render a radar chart comparing team to cluster average.

    Args:
        team_metrics: DataFrame with team metrics
        cluster_avg_values: Dict of category -> percentile for cluster average
        team_name: Name of the team
        cluster_name: Name of the cluster
        height: Chart height in pixels
    """
    # Calculate radar values for the team
    radar_values = calculate_radar_values(team_metrics)

    categories = RADAR_LABELS
    values = [radar_values.get(cat, 50.0) for cat in categories]
    values_closed = values + [values[0]]
    categories_closed = categories + [categories[0]]

    fig = go.Figure()

    # Add team trace
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        name=team_name or "Squadra",
        fill='toself',
        opacity=0.7,
        line=dict(color='#3b82f6', width=2),
    ))

    # Add cluster average if provided
    if cluster_avg_values:
        cluster_values = [cluster_avg_values.get(cat, 50.0) for cat in categories]
        cluster_values_closed = cluster_values + [cluster_values[0]]

        fig.add_trace(go.Scatterpolar(
            r=cluster_values_closed,
            theta=categories_closed,
            name=f"Media {cluster_name}" if cluster_name else "Media Cluster",
            fill='toself',
            opacity=0.3,
            line=dict(color='#94a3b8', width=1, dash='dot'),
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickvals=[25, 50, 75, 100],
                tickfont=dict(size=9, color='#666'),
            ),
            angularaxis=dict(
                tickfont=dict(size=10, color='#333'),
            ),
        ),
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.15,
            xanchor='center',
            x=0.5,
            font=dict(size=10)
        ),
        height=height,
        margin=dict(l=50, r=50, t=20, b=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
