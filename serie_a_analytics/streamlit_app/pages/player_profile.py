"""
Player Profile Page.

Shows detailed statistics and season visualization for a single player.
Identified by (player_id, team_id) pair - same player with different teams = different profiles.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import base64
from io import BytesIO

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="Profilo Giocatore - Serie A 2015-2016",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Import shared modules AFTER page config
from utils.styles import apply_custom_css
from utils.data_helpers import (
    load_data,
    load_sofascore_player_ratings,
    load_player_external_ids,
    load_player_events_for_player,
    load_matches_for_events,
    get_player_data_for_team,
    get_player_basic_info,
    get_player_season_data,
    get_player_summary_stats,
    calculate_usage_score,
    get_player_face_image,
    get_team_logo_html,
    get_team_logo_base64,
)
from components.season_chart import render_season_chart_streamlit, render_chart_legend
from components.pitch_viz import render_pitch_visualizations, render_match_filter, generate_pitch_images_base64
from components.season_chart import (
    get_rating_color, get_minutes_color, render_events,
    RATING_BAR_HEIGHT, MINUTES_BAR_HEIGHT, BAR_WIDTH, GRAY_COLOR, COLUMN_MIN_WIDTH, COLUMN_GAP
)

# Apply custom CSS
apply_custom_css()


def get_player_image_base64(player_id: int) -> str:
    """Get player face image as base64 string for PDF embedding."""
    try:
        # Import internally to avoid circular imports
        from utils.data_helpers import _get_local_player_image_path

        local_path = _get_local_player_image_path(player_id)
        if local_path and local_path.exists():
            with open(local_path, 'rb') as f:
                img_data = f.read()
            return base64.b64encode(img_data).decode('utf-8')
    except Exception:
        pass
    return None


def generate_pdf_html(
    player_name: str,
    team_name: str,
    position: str,
    stats: dict,
    usage: dict,
    season_data: list,
    player_img_b64: str,
    team_logo_b64: str,
    pitch_images: dict = None,
    pitch_matches_count: int = None
) -> str:
    """Generate HTML for landscape A4 PDF export.

    Args:
        pitch_images: Optional dict with 'pass', 'carry', 'duel' base64 images
        pitch_matches_count: Number of matches shown in pitch visualizations
    """

    score = usage['score']
    label, color = get_usage_label(score)

    # Extract usage metrics
    minutes_played = usage.get('minutes_played', 0)
    minutes_possible = usage.get('minutes_possible', 0)
    matches_played = usage.get('matches_played', 0)
    matches_available = usage.get('matches_available', 0)
    starts = usage.get('starts', 0)
    minutes_rate = usage.get('minutes_rate', 0)
    match_rate = usage.get('match_rate', 0)
    starter_rate = usage.get('starter_rate', 0)
    consistency_score = usage.get('consistency_score', 0)
    avg_minutes = usage.get('avg_minutes_per_match', 0)

    components_data = usage.get('component_scores', {})
    comp_minutes = components_data.get('minutes', 0)
    comp_participation = components_data.get('participation', 0)
    comp_starter = components_data.get('starter', 0)
    comp_consistency = components_data.get('consistency', 0)

    # Player image HTML
    if player_img_b64:
        player_img_html = f'<img src="data:image/png;base64,{player_img_b64}" class="player-img">'
    else:
        player_img_html = '<div class="player-img-placeholder">👤</div>'

    # Team logo HTML
    if team_logo_b64:
        team_logo_html = f'<img src="data:image/png;base64,{team_logo_b64}" class="team-logo">'
    else:
        team_logo_html = '⚽'

    # Stats formatting
    avg_rating_str = f"{stats['avg_rating']:.2f}" if stats['avg_rating'] else "N/A"
    minutes_str = f"{stats['minutes_total']:,}".replace(",", ".")

    # Generate season chart columns
    chart_columns = []
    for rd in season_data:
        round_num = rd.get('round', 0)
        played = rd.get('played', False)
        rating = rd.get('rating')
        minutes = rd.get('minutes', 0)
        goals = rd.get('goals', 0)
        assists = rd.get('assists', 0)
        yellow_cards = rd.get('yellow_cards', 0)
        red_cards = rd.get('red_cards', 0)

        if played and rating is not None and rating > 0:
            rating_fill_pct = (rating / 10) * 100
            rating_fill_pct = min(100, max(0, rating_fill_pct))
            rating_color = get_rating_color(rating)
            rating_label = f"{rating:.1f}"
        else:
            rating_fill_pct = 0
            rating_color = GRAY_COLOR
            rating_label = ""

        if played and minutes > 0:
            minutes_fill_pct = (minutes / 90) * 100
            minutes_fill_pct = min(100, max(0, minutes_fill_pct))
            minutes_color = get_minutes_color(minutes)
            minutes_label = f"{minutes}'"
        else:
            minutes_fill_pct = 0
            minutes_color = GRAY_COLOR
            minutes_label = ""

        events = render_events(goals, assists, yellow_cards, red_cards)

        rating_fill_radius = "5px" if rating_fill_pct >= 95 else "0 0 5px 5px"
        minutes_fill_radius = "5px" if minutes_fill_pct >= 95 else "0 0 5px 5px"

        col_html = f'''
        <div class="round-col">
          <div class="rating-label">{rating_label}</div>
          <div class="bar-container rating-bar">
            <div class="bar-fill" style="height:{rating_fill_pct:.0f}%;background:{rating_color};border-radius:{rating_fill_radius};"></div>
          </div>
          <div class="bar-container minutes-bar">
            <div class="bar-fill" style="height:{minutes_fill_pct:.0f}%;background:{minutes_color};border-radius:{minutes_fill_radius};"></div>
          </div>
          <div class="minutes-label">{minutes_label}</div>
          <div class="events">{events}</div>
          <div class="round-num">{round_num}</div>
        </div>'''
        chart_columns.append(col_html)

    chart_html = '\n'.join(chart_columns)

    # Generate pitch section HTML if images are provided
    pitch_section_html = ''
    if pitch_images:
        pass_img = pitch_images.get('pass')
        carry_img = pitch_images.get('carry')
        duel_img = pitch_images.get('duel')

        # Only show section if at least one image exists
        if pass_img or carry_img or duel_img:
            pass_html = f'<img src="data:image/png;base64,{pass_img}" class="pitch-img">' if pass_img else '<div class="pitch-img" style="background:#f1f5f9;height:150px;display:flex;align-items:center;justify-content:center;color:#9ca3af;">Nessun passaggio</div>'
            carry_html = f'<img src="data:image/png;base64,{carry_img}" class="pitch-img">' if carry_img else '<div class="pitch-img" style="background:#f1f5f9;height:150px;display:flex;align-items:center;justify-content:center;color:#9ca3af;">Nessuna conduzione</div>'
            duel_html = f'<img src="data:image/png;base64,{duel_img}" class="pitch-img">' if duel_img else '<div class="pitch-img" style="background:#f1f5f9;height:150px;display:flex;align-items:center;justify-content:center;color:#9ca3af;">Nessun duello</div>'

            # Build title with match count if available
            pitch_title = "Mappa Azioni"
            if pitch_matches_count:
                pitch_title = f"Mappa Azioni (Ultime {pitch_matches_count} partite)"

            pitch_section_html = f'''
    <div class="pitch-section">
      <div class="pitch-title">{pitch_title}</div>
      <div class="pitch-container">
        <div class="pitch-item">
          <div class="pitch-label">Passaggi Open Play</div>
          {pass_html}
        </div>
        <div class="pitch-item">
          <div class="pitch-label">Conduzioni</div>
          {carry_html}
        </div>
        <div class="pitch-item">
          <div class="pitch-label">Azioni Difensive</div>
          {duel_html}
        </div>
      </div>
    </div>'''

    # Full PDF HTML - Landscape A4
    html = f'''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    @page {{
      size: A4 landscape;
      margin: 9mm 0mm 0mm 15mm;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      font-size: 11px;
      color: #1f2937;
      background: white;
      width: 267mm;
      height: 180mm;
    }}
    .container {{
      padding: 10px;
    }}
    /* HEADER SECTION */
    .header {{
      display: flex;
      gap: 20px;
      margin-bottom: 15px;
    }}
    .player-section {{
      display: flex;
      gap: 15px;
      flex: 0 0 auto;
    }}
    .player-img {{
      width: 120px;
      height: 120px;
      border-radius: 10px;
      object-fit: cover;
      border: 3px solid white;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }}
    .player-img-placeholder {{
      width: 120px;
      height: 120px;
      border-radius: 10px;
      background: linear-gradient(135deg, #d1d5db 0%, #9ca3af 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 3rem;
    }}
    .player-info {{
      display: flex;
      flex-direction: column;
      justify-content: center;
    }}
    .player-name {{
      font-size: 1.8rem;
      font-weight: 800;
      color: #0c1929;
      margin-bottom: 4px;
    }}
    .player-team {{
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 1rem;
      color: #374151;
      margin-bottom: 2px;
    }}
    .team-logo {{
      width: 20px;
      height: 20px;
    }}
    .player-position {{
      font-size: 0.9rem;
      color: #6b7280;
      margin-bottom: 8px;
    }}
    .stats-compact {{
      display: flex;
      flex-direction: column;
      gap: 4px;
      padding: 8px 12px;
      background: #f1f5f9;
      border-radius: 8px;
      font-size: 0.85rem;
    }}
    .stats-row {{
      display: flex;
      gap: 12px;
    }}
    .stat-compact strong {{
      color: #0c1929;
      font-weight: 700;
    }}
    /* USAGE SCORE CARD */
    .score-card {{
      flex: 1;
      display: flex;
      gap: 20px;
      padding: 15px;
      background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
      border-radius: 14px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }}
    .gauge-section {{
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }}
    .gauge-wrapper {{
      position: relative;
      width: 100px;
      height: 100px;
    }}
    .gauge-svg {{
      transform: rotate(-90deg);
    }}
    .gauge-bg {{
      fill: none;
      stroke: #e5e7eb;
      stroke-width: 10;
    }}
    .gauge-fg {{
      fill: none;
      stroke: {color};
      stroke-width: 10;
      stroke-linecap: round;
    }}
    .gauge-center {{
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      text-align: center;
    }}
    .gauge-value {{
      font-size: 2rem;
      font-weight: 800;
      color: #0c1929;
    }}
    .gauge-label-text {{
      font-size: 0.65rem;
      color: #6b7280;
      text-transform: uppercase;
    }}
    .status-badge {{
      margin-top: 6px;
      padding: 4px 12px;
      background: {color};
      color: white;
      font-size: 0.7rem;
      font-weight: 700;
      border-radius: 12px;
      text-transform: uppercase;
    }}
    .details-section {{
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}
    .section-title {{
      font-size: 0.7rem;
      font-weight: 700;
      color: #4b5563;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 4px;
    }}
    .breakdown {{
      display: flex;
      flex-direction: column;
      gap: 5px;
    }}
    .breakdown-row {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.75rem;
    }}
    .breakdown-label {{
      width: 70px;
    }}
    .breakdown-bar {{
      flex: 1;
      height: 8px;
      background: #e5e7eb;
      border-radius: 4px;
      overflow: hidden;
    }}
    .breakdown-fill {{
      height: 100%;
      border-radius: 4px;
    }}
    .breakdown-value {{
      font-weight: 700;
      min-width: 30px;
      text-align: right;
    }}
    .metrics-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 6px;
    }}
    .metric-box {{
      padding: 6px;
      background: rgba(255,255,255,0.8);
      border-radius: 6px;
      text-align: center;
    }}
    .metric-value {{
      font-size: 0.9rem;
      font-weight: 700;
      color: #0c1929;
    }}
    .metric-label {{
      font-size: 0.6rem;
      color: #6b7280;
      text-transform: uppercase;
    }}
    /* SEASON CHART */
    .chart-section {{
      margin-top: 10px;
    }}
    .chart-title {{
      font-size: 1rem;
      font-weight: 700;
      color: #0c1929;
      margin-bottom: 8px;
    }}
    .chart-container {{
      display: flex;
      gap: 3px;
      padding: 10px;
      background: #f8fafc;
      border-radius: 10px;
      overflow-x: visible;
    }}
    .round-col {{
      display: flex;
      flex-direction: column;
      align-items: center;
      min-width: 18px;
      flex: 1;
    }}
    .rating-label {{
      font-size: 7px;
      color: #374151;
      font-weight: 600;
      height: 10px;
      line-height: 10px;
    }}
    .bar-container {{
      width: 12px;
      border-radius: 6px;
      position: relative;
      overflow: hidden;
      background: {GRAY_COLOR};
    }}
    .rating-bar {{
      height: 50px;
    }}
    .minutes-bar {{
      height: 32px;
      margin-top: 2px;
    }}
    .bar-fill {{
      position: absolute;
      bottom: 0;
      left: 0;
      width: 100%;
    }}
    .minutes-label {{
      font-size: 6px;
      color: #6b7280;
      height: 8px;
      line-height: 8px;
    }}
    .events {{
      font-size: 8px;
      height: 12px;
      line-height: 12px;
    }}
    .round-num {{
      font-size: 7px;
      color: #9ca3af;
    }}
    /* LEGEND */
    .legend {{
      display: flex;
      gap: 15px;
      font-size: 0.65rem;
      color: #6b7280;
      margin-top: 8px;
      padding: 6px 10px;
      background: #f8fafc;
      border-radius: 6px;
      flex-wrap: wrap;
    }}
    .legend-item {{
      display: flex;
      align-items: center;
      gap: 4px;
    }}
    .legend-bar {{
      width: 10px;
      height: 14px;
      border-radius: 3px;
    }}
    /* PITCH VISUALIZATIONS */
    .pitch-section {{
      margin-top: 15px;
    }}
    .pitch-title {{
      font-size: 1.15rem;
      font-weight: 700;
      color: #0c1929;
      margin-bottom: 10px;
    }}
    .pitch-container {{
      display: flex;
      gap: 20px;
      justify-content: center;
    }}
    .pitch-item {{
      flex: 1;
      text-align: center;
    }}
    .pitch-label {{
      font-size: 1rem;
      font-weight: 600;
      color: #374151;
      margin-bottom: 6px;
    }}
    .pitch-img {{
      width: 100%;
      max-width: 340px;
      height: auto;
    }}
    .pitch-legend {{
      display: flex;
      gap: 20px;
      justify-content: center;
      font-size: 0.65rem;
      color: #6b7280;
      margin-top: 8px;
      padding: 6px 10px;
      background: #f8fafc;
      border-radius: 6px;
      flex-wrap: wrap;
    }}
    .pitch-legend-item {{
      display: flex;
      align-items: center;
      gap: 4px;
    }}
    .pitch-legend-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }}
    /* FOOTER */
    .footer {{
      margin-top: 10px;
      text-align: right;
      font-size: 0.6rem;
      color: #9ca3af;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="player-section">
        {player_img_html}
        <div class="player-info">
          <div class="player-name">{player_name}</div>
          <div class="player-team">{team_logo_html} {team_name}</div>
          <div class="player-position">{position}</div>
          <div class="stats-compact">
            <div class="stats-row">
              <span><strong>{stats['matches']}</strong> partite</span>
              <span><strong>{minutes_str}</strong> min</span>
              <span><strong>{avg_rating_str}</strong> media</span>
            </div>
            <div class="stats-row">
              <span><strong>{stats['goals']}</strong> ⚽</span>
              <span><strong>{stats['assists']}</strong> 👟</span>
              <span><strong>{stats['yellow_cards']}</strong> 🟨</span>
              <span><strong>{stats['red_cards']}</strong> 🟥</span>
            </div>
          </div>
        </div>
      </div>

      <div class="score-card">
        <div class="gauge-section">
          <div class="gauge-wrapper">
            <svg class="gauge-svg" width="100" height="100" viewBox="0 0 100 100">
              <circle class="gauge-bg" cx="50" cy="50" r="40"></circle>
              <circle class="gauge-fg" cx="50" cy="50" r="40" stroke-dasharray="{score * 2.51} {251 - score * 2.51}"></circle>
            </svg>
            <div class="gauge-center">
              <div class="gauge-value">{score:.0f}</div>
              <div class="gauge-label-text">Score</div>
            </div>
          </div>
          <div class="status-badge">{label}</div>
        </div>

        <div class="details-section">
          <div>
            <div class="section-title">Composizione Score</div>
            <div class="breakdown">
              <div class="breakdown-row">
                <span class="breakdown-label">Minuti</span>
                <div class="breakdown-bar">
                  <div class="breakdown-fill" style="width:{min(100, minutes_rate)}%;background:#3b82f6;"></div>
                </div>
                <span class="breakdown-value">+{comp_minutes:.0f}</span>
              </div>
              <div class="breakdown-row">
                <span class="breakdown-label">Presenze</span>
                <div class="breakdown-bar">
                  <div class="breakdown-fill" style="width:{min(100, match_rate)}%;background:#8b5cf6;"></div>
                </div>
                <span class="breakdown-value">+{comp_participation:.0f}</span>
              </div>
              <div class="breakdown-row">
                <span class="breakdown-label">Titolarità</span>
                <div class="breakdown-bar">
                  <div class="breakdown-fill" style="width:{min(100, starter_rate)}%;background:#f59e0b;"></div>
                </div>
                <span class="breakdown-value">+{comp_starter:.0f}</span>
              </div>
              <div class="breakdown-row">
                <span class="breakdown-label">Regolarità</span>
                <div class="breakdown-bar">
                  <div class="breakdown-fill" style="width:{min(100, consistency_score)}%;background:#10b981;"></div>
                </div>
                <span class="breakdown-value">+{comp_consistency:.0f}</span>
              </div>
            </div>
          </div>
          <div>
            <div class="section-title">Statistiche</div>
            <div class="metrics-grid">
              <div class="metric-box">
                <div class="metric-value">{minutes_played:,}</div>
                <div class="metric-label">Minuti</div>
              </div>
              <div class="metric-box">
                <div class="metric-value">{matches_played}/{matches_available}</div>
                <div class="metric-label">Partite</div>
              </div>
              <div class="metric-box">
                <div class="metric-value">{starts}</div>
                <div class="metric-label">Titolare</div>
              </div>
              <div class="metric-box">
                <div class="metric-value">{avg_minutes:.0f}'</div>
                <div class="metric-label">Media Min</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="chart-section">
      <div class="chart-title">Andamento Stagionale</div>
      <div class="chart-container">
        {chart_html}
      </div>
      <div class="legend">
        <div class="legend-item">
          <div class="legend-bar" style="background:linear-gradient(to top,#ef4444,#22c55e,#3b82f6);"></div>
          <span>Rating (0-10)</span>
        </div>
        <div class="legend-item">
          <div class="legend-bar" style="background:linear-gradient(to top,#fbbf24,#16a34a);"></div>
          <span>Minuti (0-90)</span>
        </div>
        <div class="legend-item">
          <div class="legend-bar" style="background:{GRAY_COLOR};"></div>
          <span>Non giocato</span>
        </div>
        <div>⚽ Goal</div>
        <div>👟 Assist</div>
        <div>🟨 Giallo</div>
        <div>🟥 Rosso</div>
      </div>
    </div>

    {pitch_section_html}
  </div>
</body>
</html>'''

    return html


def get_position_label(position: str) -> str:
    """Convert position code to Italian label."""
    labels = {
        'G': 'Portiere',
        'D': 'Difensore',
        'M': 'Centrocampista',
        'F': 'Attaccante'
    }
    return labels.get(position, position or 'N/A')


def get_usage_score_class(score: float) -> str:
    """Get CSS class based on usage score value."""
    if score <= 30:
        return "score-low"
    elif score <= 60:
        return "score-medium"
    else:
        return "score-high"


def render_player_image(player_id: int):
    """Render player image or placeholder."""
    try:
        image = get_player_face_image(player_id)
        if image is not None:
            st.image(image, width=170)
        else:
            st.markdown(
                '<div class="player-image-placeholder">👤</div>',
                unsafe_allow_html=True
            )
    except Exception:
        st.markdown(
            '<div class="player-image-placeholder">👤</div>',
            unsafe_allow_html=True
        )


def get_usage_label(score: float) -> tuple[str, str]:
    """Get descriptive label and color based on usage score."""
    if score >= 85:
        return "Titolare Fisso", "#16a34a"
    elif score >= 70:
        return "Titolare", "#22c55e"
    elif score >= 50:
        return "Rotazione", "#eab308"
    elif score >= 30:
        return "Riserva", "#f97316"
    else:
        return "Poco Utilizzato", "#ef4444"


def render_usage_gauge(usage: dict):
    """
    Render a horizontal usage score card with circular gauge and detailed breakdown.

    The score is calculated from 4 weighted components:
    - Minuti (40%): minutes_played / minutes_possible
    - Partecipazione (25%): matches_played / matches_available
    - Titolarità (20%): starter rate + quality of starts
    - Consistenza (15%): regularity of playing time
    """
    import streamlit.components.v1 as components

    score = usage['score']
    label, color = get_usage_label(score)

    # Extract all metrics
    minutes_played = usage.get('minutes_played', 0)
    minutes_possible = usage.get('minutes_possible', 0)
    matches_played = usage.get('matches_played', 0)
    matches_available = usage.get('matches_available', 0)
    starts = usage.get('starts', 0)
    minutes_rate = usage.get('minutes_rate', 0)
    match_rate = usage.get('match_rate', 0)
    starter_rate = usage.get('starter_rate', 0)
    consistency_score = usage.get('consistency_score', 0)
    avg_minutes = usage.get('avg_minutes_per_match', 0)

    # Component scores (already weighted)
    components_data = usage.get('component_scores', {})
    comp_minutes = components_data.get('minutes', 0)
    comp_participation = components_data.get('participation', 0)
    comp_starter = components_data.get('starter', 0)
    comp_consistency = components_data.get('consistency', 0)

    # Horizontal layout - gauge on left, breakdown + metrics on right
    gauge_html = f'''<!DOCTYPE html>
<html>
<head>
  <style>
    body {{
      margin: 0;
      padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }}
    .card-container {{
      display: flex;
      flex-direction: row;
      align-items: stretch;
      padding: 20px;
      background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
      border-radius: 20px;
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
      gap: 24px;
      position: relative;
      width: 100%;
      box-sizing: border-box;
    }}
    /* Left side - Gauge */
    .gauge-section {{
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-width: 160px;
    }}
    .gauge-wrapper {{
      position: relative;
      width: 140px;
      height: 140px;
    }}
    .gauge-svg {{
      transform: rotate(-90deg);
    }}
    .gauge-bg {{
      fill: none;
      stroke: #e5e7eb;
      stroke-width: 12;
    }}
    .gauge-fg {{
      fill: none;
      stroke: {color};
      stroke-width: 12;
      stroke-linecap: round;
      stroke-dasharray: {score * 3.77} {377 - score * 3.77};
    }}
    .gauge-center {{
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      text-align: center;
    }}
    .gauge-value {{
      font-size: 2.8rem;
      font-weight: 800;
      color: #0c1929;
      line-height: 1;
    }}
    .gauge-percent {{
      font-size: 0.85rem;
      font-weight: 700;
      color: #6b7280;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .gauge-label {{
      margin-top: 10px;
      padding: 6px 16px;
      background: {color};
      color: white;
      font-size: 0.85rem;
      font-weight: 700;
      border-radius: 20px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    /* Right side - Breakdown + Metrics */
    .details-section {{
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}
    .section-title {{
      font-size: 0.8rem;
      font-weight: 700;
      color: #4b5563;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      margin-bottom: 6px;
    }}
    .breakdown {{
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}
    .breakdown-row {{
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 0.9rem;
      color: #374151;
    }}
    .breakdown-label {{
      width: 90px;
      font-weight: 500;
    }}
    .breakdown-bar {{
      flex: 1;
      height: 10px;
      background: #e5e7eb;
      border-radius: 5px;
      overflow: hidden;
      min-width: 100px;
    }}
    .breakdown-fill {{
      height: 100%;
      border-radius: 5px;
    }}
    .breakdown-value {{
      font-weight: 700;
      color: #0c1929;
      min-width: 40px;
      text-align: right;
      font-size: 0.95rem;
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
    }}
    .metric {{
      padding: 10px 8px;
      background: rgba(255,255,255,0.85);
      border-radius: 10px;
      text-align: center;
      box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }}
    .metric-value {{
      font-size: 1.1rem;
      font-weight: 700;
      color: #0c1929;
      line-height: 1.2;
    }}
    .metric-label {{
      font-size: 0.7rem;
      color: #6b7280;
      text-transform: uppercase;
      margin-top: 4px;
      letter-spacing: 0.03em;
    }}
    .info-icon {{
      position: absolute;
      top: 12px;
      right: 12px;
      width: 20px;
      height: 20px;
      border-radius: 50%;
      background: #9ca3af;
      color: white;
      font-size: 12px;
      font-weight: 700;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: help;
      font-style: italic;
    }}
    .info-icon:hover {{
      background: #6b7280;
    }}
    .tooltip {{
      display: none;
      position: absolute;
      top: 38px;
      right: 8px;
      width: 260px;
      padding: 14px;
      background: #1f2937;
      color: white;
      font-size: 0.78rem;
      line-height: 1.5;
      border-radius: 10px;
      z-index: 100;
      box-shadow: 0 6px 20px rgba(0,0,0,0.35);
    }}
    .info-icon:hover + .tooltip,
    .tooltip:hover {{
      display: block;
    }}
    .tooltip-title {{
      font-weight: 700;
      margin-bottom: 8px;
      font-size: 0.85rem;
    }}
    .tooltip-item {{
      display: flex;
      justify-content: space-between;
      margin-bottom: 4px;
    }}
    .tooltip-weight {{
      color: #9ca3af;
    }}
  </style>
</head>
<body>
  <div class="card-container">
    <div class="info-icon">i</div>
    <div class="tooltip">
      <div class="tooltip-title">Come è calcolato lo Score</div>
      <p style="margin:0 0 10px 0;color:#d1d5db;">Score composito per valutare l'utilizzo di giocatori in prestito:</p>
      <div class="tooltip-item">
        <span>📊 Minuti giocati</span>
        <span class="tooltip-weight">40%</span>
      </div>
      <div class="tooltip-item">
        <span>📋 Presenze in partita</span>
        <span class="tooltip-weight">25%</span>
      </div>
      <div class="tooltip-item">
        <span>⭐ Titolarità</span>
        <span class="tooltip-weight">20%</span>
      </div>
      <div class="tooltip-item">
        <span>📈 Regolarità d'impiego</span>
        <span class="tooltip-weight">15%</span>
      </div>
      <p style="margin:10px 0 0 0;color:#9ca3af;font-size:0.7rem;">Ogni componente è normalizzato 0-100 e poi pesato.</p>
    </div>

    <div class="gauge-section">
      <div class="gauge-wrapper">
        <svg class="gauge-svg" width="140" height="140" viewBox="0 0 140 140">
          <circle class="gauge-bg" cx="70" cy="70" r="60"></circle>
          <circle class="gauge-fg" cx="70" cy="70" r="60"></circle>
        </svg>
        <div class="gauge-center">
          <div class="gauge-value">{score:.0f}</div>
          <div class="gauge-percent">Score</div>
        </div>
      </div>
      <div class="gauge-label">{label}</div>
    </div>

    <div class="details-section">
      <div>
        <div class="section-title">Composizione Score</div>
        <div class="breakdown">
          <div class="breakdown-row">
            <span class="breakdown-label">Minuti</span>
            <div class="breakdown-bar">
              <div class="breakdown-fill" style="width:{min(100, minutes_rate)}%;background:#3b82f6;"></div>
            </div>
            <span class="breakdown-value">+{comp_minutes:.0f}</span>
          </div>
          <div class="breakdown-row">
            <span class="breakdown-label">Presenze</span>
            <div class="breakdown-bar">
              <div class="breakdown-fill" style="width:{min(100, match_rate)}%;background:#8b5cf6;"></div>
            </div>
            <span class="breakdown-value">+{comp_participation:.0f}</span>
          </div>
          <div class="breakdown-row">
            <span class="breakdown-label">Titolarità</span>
            <div class="breakdown-bar">
              <div class="breakdown-fill" style="width:{min(100, starter_rate)}%;background:#f59e0b;"></div>
            </div>
            <span class="breakdown-value">+{comp_starter:.0f}</span>
          </div>
          <div class="breakdown-row">
            <span class="breakdown-label">Regolarità</span>
            <div class="breakdown-bar">
              <div class="breakdown-fill" style="width:{min(100, consistency_score)}%;background:#10b981;"></div>
            </div>
            <span class="breakdown-value">+{comp_consistency:.0f}</span>
          </div>
        </div>
      </div>

      <div>
        <div class="section-title">Statistiche</div>
        <div class="metrics">
          <div class="metric">
            <div class="metric-value">{minutes_played:,}</div>
            <div class="metric-label">Minuti</div>
          </div>
          <div class="metric">
            <div class="metric-value">{matches_played}/{matches_available}</div>
            <div class="metric-label">Partite</div>
          </div>
          <div class="metric">
            <div class="metric-value">{starts}</div>
            <div class="metric-label">Titolare</div>
          </div>
          <div class="metric">
            <div class="metric-value">{avg_minutes:.0f}'</div>
            <div class="metric-label">Media Min</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</body>
</html>'''

    components.html(gauge_html, height=260)


def render_header_section(player_id: int, team_id: int, df_player: pd.DataFrame, df_all: pd.DataFrame):
    """Render the header section with player info, stats, and usage score."""
    # Get basic info
    info = get_player_basic_info(player_id, team_id)
    if not info:
        st.error("Informazioni giocatore non disponibili")
        return

    # Calculate comprehensive usage score (includes all metrics)
    usage = calculate_usage_score(df_player, df_all)

    # Get stats for compact display
    stats = get_player_summary_stats(df_player)

    # Format player name with shirt number
    if info["shirt_number"]:
        player_display_name = f'{info["shirt_number"]}. {info["player_name"]}'
    else:
        player_display_name = info["player_name"]

    # Layout: Image + Info (left) | Usage Score Card (right - wider for horizontal layout)
    col_left, col_right = st.columns([4, 6])

    with col_left:
        col_img, col_info = st.columns([1, 2])

        with col_img:
            render_player_image(player_id)

        with col_info:
            st.markdown(f'<div class="player-name">{player_display_name}</div>', unsafe_allow_html=True)

            team_logo = get_team_logo_html(team_id, size=24)
            st.markdown(
                f'<div class="player-team">{team_logo} {info["team_name"]}</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                f'<div class="player-position">{get_position_label(info["position"])}</div>',
                unsafe_allow_html=True
            )

            # Compact stats - Two rows
            avg_rating_str = f"{stats['avg_rating']:.2f}" if stats['avg_rating'] else "N/A"
            minutes_str = f"{stats['minutes_total']:,}".replace(",", ".")

            st.markdown(f'''
                <div class="player-stats-compact">
                    <div class="stats-row">
                        <span class="stat-compact"><strong>{stats['matches']}</strong> partite</span>
                        <span class="stat-compact"><strong>{minutes_str}</strong> min</span>
                        <span class="stat-compact"><strong>{avg_rating_str}</strong> media</span>
                    </div>
                    <div class="stats-row">
                        <span class="stat-compact"><strong>{stats['goals']}</strong> ⚽</span>
                        <span class="stat-compact"><strong>{stats['assists']}</strong> 👟</span>
                        <span class="stat-compact"><strong>{stats['yellow_cards']}</strong> 🟨</span>
                        <span class="stat-compact"><strong>{stats['red_cards']}</strong> 🟥</span>
                    </div>
                </div>
            ''', unsafe_allow_html=True)

    with col_right:
        render_usage_gauge(usage)


def render_stats_summary(df_player: pd.DataFrame):
    """Render summary statistics box."""
    stats = get_player_summary_stats(df_player)

    st.markdown("### Statistiche Stagione")

    # Create columns for stats
    cols = st.columns(8)

    stat_items = [
        ("Partite", stats['matches']),
        ("Minuti", f"{stats['minutes_total']:,}".replace(",", ".")),
        ("Media Voto", f"{stats['avg_rating']:.2f}" if stats['avg_rating'] else "N/A"),
        ("Titolare", f"{stats['starter_count']} ({stats['starter_pct']:.0f}%)"),
        ("Goal", stats['goals']),
        ("Assist", stats['assists']),
        ("Gialli", stats['yellow_cards']),
        ("Rossi", stats['red_cards']),
    ]

    for i, (label, value) in enumerate(stat_items):
        with cols[i]:
            st.markdown(f'''
                <div class="stat-item">
                    <div class="stat-value">{value}</div>
                    <div class="stat-label">{label}</div>
                </div>
            ''', unsafe_allow_html=True)


def render_pitch_events(sofascore_player_id: int, sofascore_team_id: int):
    """
    Render pitch visualizations (passes, carries, duels) for a player.

    Shows three horizontal pitch maps with:
    - Passes: green arrows (success) / red arrows (fail)
    - Carries: blue dashed lines (positive) / orange dashed lines (negative)
    - Duels: colored points by type (aerial, ground, tackle)

    Includes a slider to filter by last N matches.
    """
    # Load external IDs mapping
    external_ids = load_player_external_ids()
    if external_ids.empty:
        return  # No mapping table

    # Find StatsBomb player ID for this SofaScore player
    mapping = external_ids[
        (external_ids['external_id'].astype(str) == str(sofascore_player_id)) &
        (external_ids['provider'] == 'sofascore')
    ]

    if mapping.empty:
        return  # No mapping found

    statsbomb_id = int(mapping.iloc[0]['player_id'])

    # Load player events - filtered server-side for this player only
    df_events = load_player_events_for_player(statsbomb_id)
    if df_events.empty:
        return  # No events for this player

    # Load match dates for filtering
    match_dates = load_matches_for_events()

    st.markdown("### Mappa Azioni")

    # Get number of matches this player has played
    num_matches = df_events['match_id'].nunique()

    # Render filter slider (dynamically adapts to player's matches)
    last_n = render_match_filter(num_matches)

    # Render the three pitch visualizations
    render_pitch_visualizations(
        player_id=statsbomb_id,
        df_events=df_events,
        last_n_matches=last_n,
        match_dates=match_dates
    )


def render_statsbomb_metrics(sofascore_player_id: int, sofascore_team_id: int):
    """
    Render StatsBomb metrics if available.

    Shows metrics classified into positive/neutral/negative based on percentile
    compared to all players with 800+ minutes.

    The player_metrics table is UNPIVOTED:
    - Each row = one metric for one player
    - metric_name column contains the metric identifier
    - metric_value_p90 contains the normalized value per 90 minutes
    - total_minutes contains minutes played
    """
    # Load external IDs mapping
    external_ids = load_player_external_ids()
    if external_ids.empty:
        return  # No mapping table

    # Find StatsBomb player ID for this SofaScore player
    mapping = external_ids[
        (external_ids['external_id'].astype(str) == str(sofascore_player_id)) &
        (external_ids['provider'] == 'sofascore')
    ]

    if mapping.empty:
        return  # No mapping found

    statsbomb_id = int(mapping.iloc[0]['player_id'])

    # Load player metrics
    data = load_data()
    if data is None or 'player_metrics' not in data:
        return

    player_metrics = data['player_metrics']
    if player_metrics.empty:
        return

    # Get this player's metrics (all rows for this player)
    player_data = player_metrics[player_metrics['player_id'] == statsbomb_id]
    if player_data.empty:
        return

    # Get player's total minutes (should be same across all rows)
    player_minutes = player_data['total_minutes'].iloc[0] if 'total_minutes' in player_data.columns else 0

    # Only show metrics for players with significant playing time
    if player_minutes < 200:
        return

    # Get all players with 800+ minutes for comparison
    # First get unique player-minutes combinations
    if 'total_minutes' in player_metrics.columns:
        players_800 = player_metrics[player_metrics['total_minutes'] >= 800]
    else:
        # If no total_minutes column, can't filter - use all
        players_800 = player_metrics

    if players_800.empty:
        return

    # Metrics where lower is better
    lower_is_better = {
        'fouls_committed', 'yellow_cards', 'red_cards', 'turnovers', 'dispossessed',
        'xg_conceded', 'shots_conceded', 'ppda', 'turnovers_per_touch',
        'dispossessed_per_touch', 'aerial_duels_lost', 'ground_duels_lost'
    }

    # Classify metrics
    positive_metrics = []
    neutral_metrics = []
    negative_metrics = []

    # Get unique metrics for this player
    unique_metrics = player_data['metric_name'].unique()

    for metric_name in unique_metrics:
        try:
            # Get this player's value for this metric
            player_metric_row = player_data[player_data['metric_name'] == metric_name]
            if player_metric_row.empty:
                continue

            # Use metric_value_p90 for normalized comparison
            value_col = 'metric_value_p90' if 'metric_value_p90' in player_metric_row.columns else 'metric_value'
            player_value = player_metric_row[value_col].iloc[0]

            if pd.isna(player_value):
                continue

            # Get all values for this metric from players with 800+ minutes
            all_metric_data = players_800[players_800['metric_name'] == metric_name]
            if len(all_metric_data) < 5:
                continue  # Not enough data for meaningful percentile

            all_values = all_metric_data[value_col].dropna()
            if len(all_values) < 5:
                continue

            # Calculate percentile
            percentile = (all_values < player_value).mean() * 100

            # Adjust for "lower is better" metrics
            if metric_name in lower_is_better:
                percentile = 100 - percentile

            # Get category if available
            category = player_metric_row['metric_category'].iloc[0] if 'metric_category' in player_metric_row.columns else ''

            # Format metric name for display
            display_name = metric_name.replace('_', ' ').title()

            # Classify
            metric_info = {
                'name': display_name,
                'value': float(player_value),
                'percentile': percentile,
                'category': category
            }

            if percentile >= 70:
                positive_metrics.append(metric_info)
            elif percentile >= 30:
                neutral_metrics.append(metric_info)
            else:
                negative_metrics.append(metric_info)

        except Exception:
            continue

    if not (positive_metrics or neutral_metrics or negative_metrics):
        return

    # Group metrics by category
    def group_by_category(metrics_list):
        """Group metrics by their category."""
        grouped = {}
        for m in metrics_list:
            cat = m['category'] if m['category'] else 'Altro'
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(m)
        # Sort metrics within each category by percentile
        for cat in grouped:
            grouped[cat].sort(key=lambda x: x['percentile'], reverse=True)
        return grouped

    positive_grouped = group_by_category(positive_metrics)
    neutral_grouped = group_by_category(neutral_metrics)
    negative_grouped = group_by_category(negative_metrics)

    st.markdown("### Metriche Avanzate (StatsBomb)")

    col1, col2, col3 = st.columns(3)

    def render_metrics_column(grouped_metrics, column_class, header_class, header_text):
        """Render a column of metrics grouped by category."""
        st.markdown(f'''
            <div class="metrics-column {column_class}">
                <div class="column-header {header_class}">{header_text}</div>
        ''', unsafe_allow_html=True)

        if not grouped_metrics:
            st.markdown('<div class="metric-row"><em>Nessuna metrica</em></div>', unsafe_allow_html=True)
        else:
            # Sort categories alphabetically
            for category in sorted(grouped_metrics.keys()):
                metrics = grouped_metrics[category]
                st.markdown(f'<div class="metric-category-header">{category}</div>', unsafe_allow_html=True)
                for m in metrics:
                    st.markdown(f'''
                        <div class="metric-row">
                            <div class="metric-name">{m['name']}</div>
                            <div class="metric-value-percentile">{m['value']:.2f} ({m['percentile']:.0f}°)</div>
                        </div>
                    ''', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with col1:
        render_metrics_column(positive_grouped, "metrics-column-positive", "column-header-positive", "✅ Punti di Forza")

    with col2:
        render_metrics_column(neutral_grouped, "metrics-column-neutral", "column-header-neutral", "➖ Nella Media")

    with col3:
        render_metrics_column(negative_grouped, "metrics-column-negative", "column-header-negative", "❌ Da Migliorare")


def main():
    """Main page function."""
    # Get player and team IDs from session state
    player_id = st.session_state.get('player_profile_id')
    team_id = st.session_state.get('player_profile_team')

    # Top bar: Back button (left) + PDF export (far right)
    col_back, col_spacer, col_pdf = st.columns([1, 8, 1])
    with col_back:
        if st.button("← Indietro", key="back_to_dashboard"):
            # Clear profile state and go back
            st.session_state.player_profile_id = None
            st.session_state.player_profile_team = None
            st.switch_page("pages/_dashboard.py")

    # Validate parameters
    if not player_id or not team_id:
        st.error("Giocatore non trovato. Parametri mancanti.")
        st.info("Seleziona un giocatore dalla rosa nella dashboard.")
        if st.button("Torna alla Home"):
            st.switch_page("app.py")
        return

    # Load data
    df_all = load_sofascore_player_ratings()
    if df_all is None or df_all.empty:
        st.error("Dati non disponibili")
        return

    df_player = get_player_data_for_team(player_id, team_id)
    if df_player.empty:
        st.warning(f"Nessun dato trovato per il giocatore (ID: {player_id}) con questa squadra (ID: {team_id}).")
        if st.button("Torna alla Home"):
            st.switch_page("app.py")
        return

    # Get data for PDF export
    info = get_player_basic_info(player_id, team_id)
    stats = get_player_summary_stats(df_player)
    usage = calculate_usage_score(df_player, df_all)
    season_data = get_player_season_data(player_id, team_id)

    # Export button - HTML download with print instructions
    with col_pdf:
        # Format player name
        if info and info.get("shirt_number"):
            pdf_player_name = f'{info["shirt_number"]}. {info["player_name"]}'
        else:
            pdf_player_name = info["player_name"] if info else "Giocatore"

        player_img_b64 = get_player_image_base64(player_id)
        team_logo_b64 = get_team_logo_base64(team_id)
        safe_name = pdf_player_name.replace(" ", "_").replace(".", "")

        # Generate pitch images for PDF export
        pitch_images = None
        pitch_matches_used = None
        external_ids = load_player_external_ids()
        if not external_ids.empty:
            mapping = external_ids[
                (external_ids['external_id'].astype(str) == str(player_id)) &
                (external_ids['provider'] == 'sofascore')
            ]
            if not mapping.empty:
                statsbomb_id = int(mapping.iloc[0]['player_id'])
                df_events = load_player_events_for_player(statsbomb_id)
                if not df_events.empty:
                    match_dates = load_matches_for_events()
                    # Use default of 4 matches for PDF (consistent with UI default)
                    num_matches = df_events['match_id'].nunique()
                    pitch_matches_used = min(4, num_matches) if num_matches > 0 else None
                    pitch_images = generate_pitch_images_base64(
                        player_id=statsbomb_id,
                        df_events=df_events,
                        last_n_matches=pitch_matches_used,
                        match_dates=match_dates
                    )

        pdf_html = generate_pdf_html(
            player_name=pdf_player_name,
            team_name=info["team_name"] if info else "",
            position=get_position_label(info["position"]) if info else "",
            stats=stats,
            usage=usage,
            season_data=season_data,
            player_img_b64=player_img_b64,
            team_logo_b64=team_logo_b64,
            pitch_images=pitch_images,
            pitch_matches_count=pitch_matches_used
        )

        # HTML download with instructions dialog
        @st.dialog("Scarica profilo")
        def show_download_dialog():
            st.markdown("""
            ### Come salvare in PDF

            1. Clicca **Scarica** qui sotto
            2. Apri il file HTML nel browser (doppio click)
            3. Stampa: `⌘+P` (Mac) o `Ctrl+P` (Windows)
            4. Seleziona **"Salva come PDF"**
            5. Imposta **Margini: Nessuno**
            6. Imposta **orientamento orizzontale**
            """)
            st.download_button(
                label="Scarica HTML",
                data=pdf_html.encode('utf-8'),
                file_name=f"profilo_{safe_name}.html",
                mime="text/html",
                key="html_export_dialog_btn",
                use_container_width=True
            )

        @st.dialog("Come salvare in PDF")
        def show_info_dialog():
            st.markdown("""
            ### Istruzioni

            1. Clicca il bottone **Scarica**
            2. Apri il file HTML nel browser (doppio click)
            3. Stampa: `⌘+P` (Mac) o `Ctrl+P` (Windows)
            4. Seleziona **"Salva come PDF"**
            5. Imposta **Margini: Nessuno**
            6. Imposta **orientamento orizzontale**
            """)

        btn_col1, btn_col2 = st.columns([2, 1], gap="small")
        with btn_col1:
            if st.button("Scarica", key="open_download_dialog", use_container_width=True):
                show_download_dialog()
        with btn_col2:
            if st.button("?", key="open_help_dialog", use_container_width=True):
                show_info_dialog()

    # SECTION 1: Header with player info and usage score
    render_header_section(player_id, team_id, df_player, df_all)

    st.markdown("---")

    # SECTION 2: Season Chart
    season_data = get_player_season_data(player_id, team_id)
    render_season_chart_streamlit(season_data)
    render_chart_legend()

    st.markdown("---")

    # SECTION 2.5: Pitch Visualizations (passes, carries, duels)
    render_pitch_events(player_id, team_id)

    st.markdown("---")

    # SECTION 3: StatsBomb Metrics (optional - only if mapping exists)
    render_statsbomb_metrics(player_id, team_id)


if __name__ == "__main__":
    main()
