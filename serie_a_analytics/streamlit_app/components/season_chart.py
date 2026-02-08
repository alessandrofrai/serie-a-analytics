"""
Season Chart Component for Player Profile.

Renders a 38-round season visualization with:
- Rating bars: fixed height container with fill based on 0-10 scale
- Minutes bars: fixed height container with fill based on 0-90 scale
- Event icons (goals, assists, cards)
"""

import streamlit as st
from typing import List


def interpolate_color(color1: str, color2: str, t: float) -> str:
    """Interpolate between two hex colors."""
    r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
    r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def get_rating_color(rating: float) -> str:
    """Get color for rating value with smooth interpolation."""
    if rating is None:
        return "#d1d5db"
    rating = max(3.0, min(10.0, rating))
    color_stops = [
        (3.0, "#ef4444"), (5.0, "#f97316"), (6.0, "#eab308"),
        (7.0, "#84cc16"), (8.0, "#22c55e"), (9.0, "#3b82f6"), (10.0, "#3b82f6"),
    ]
    for i in range(len(color_stops) - 1):
        low_val, low_color = color_stops[i]
        high_val, high_color = color_stops[i + 1]
        if low_val <= rating <= high_val:
            t = (rating - low_val) / (high_val - low_val) if high_val != low_val else 0
            return interpolate_color(low_color, high_color, t)
    return "#3b82f6"


def get_minutes_color(minutes: int) -> str:
    """Get color for minutes value."""
    if minutes <= 0:
        return "#d1d5db"
    if minutes <= 15:
        return "#fbbf24"
    elif minutes <= 45:
        return "#a3e635"
    elif minutes <= 75:
        return "#22c55e"
    return "#16a34a"


def render_events(goals: int, assists: int, yellow_cards: int, red_cards: int) -> str:
    """Render event icons for a round with stacking effect when > 2 icons."""
    icons = []
    for _ in range(min(goals, 3)):
        icons.append("⚽")
    for _ in range(min(assists, 3)):
        icons.append("👟")
    for _ in range(min(yellow_cards, 2)):
        icons.append("🟨")
    for _ in range(min(red_cards, 1)):
        icons.append("🟥")

    if not icons:
        return "&nbsp;"

    # Wrap each emoji in a span for stacking effect
    # First emoji has no negative margin, others overlap progressively
    spans = []
    for i, icon in enumerate(icons):
        if i == 0:
            spans.append(f'<span style="position:relative;z-index:{10-i};">{icon}</span>')
        else:
            # Negative margin to overlap (-4px per icon after the first)
            spans.append(f'<span style="position:relative;z-index:{10-i};margin-left:-4px;">{icon}</span>')

    return "".join(spans)


RATING_BAR_HEIGHT = 70
MINUTES_BAR_HEIGHT = 45
BAR_WIDTH = 18
GRAY_COLOR = "#e5e7eb"
COLUMN_MIN_WIDTH = 28
COLUMN_GAP = 6

# Total height calculation for iframe:
# Rating label: 14px + Rating bar: 70px + gap: 3px + Minutes bar: 45px +
# Minutes label: 12px + Events: 16px + Round number: 14px + padding: 20px + margin: 10px
CHART_HEIGHT = 210


def render_season_chart_streamlit(season_data: List[dict]):
    """Render the 38-round season chart using components.html for reliable rendering."""
    import streamlit.components.v1 as components

    st.markdown("### Andamento Stagionale")

    # Build the full chart as a single HTML block
    columns_html = []

    for rd in season_data:
        round_num = rd.get('round', 0)
        played = rd.get('played', False)
        rating = rd.get('rating')
        minutes = rd.get('minutes', 0)
        goals = rd.get('goals', 0)
        assists = rd.get('assists', 0)
        yellow_cards = rd.get('yellow_cards', 0)
        red_cards = rd.get('red_cards', 0)

        # Calculate fill percentages
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

        # Border radius for fill
        rating_fill_radius = "7px" if rating_fill_pct >= 95 else "0 0 7px 7px"
        minutes_fill_radius = "7px" if minutes_fill_pct >= 95 else "0 0 7px 7px"

        column_html = f'''
        <div style="display:flex;flex-direction:column;align-items:center;min-width:{COLUMN_MIN_WIDTH}px;flex:1;">
          <div style="font-size:10px;color:#374151;font-weight:600;height:14px;line-height:14px;">{rating_label}</div>
          <div style="width:{BAR_WIDTH}px;height:{RATING_BAR_HEIGHT}px;background:{GRAY_COLOR};border-radius:8px;position:relative;overflow:hidden;">
            <div style="position:absolute;bottom:0;left:0;width:100%;height:{rating_fill_pct:.0f}%;background:{rating_color};border-radius:{rating_fill_radius};"></div>
          </div>
          <div style="width:{BAR_WIDTH}px;height:{MINUTES_BAR_HEIGHT}px;background:{GRAY_COLOR};border-radius:8px;position:relative;overflow:hidden;margin-top:3px;">
            <div style="position:absolute;bottom:0;left:0;width:100%;height:{minutes_fill_pct:.0f}%;background:{minutes_color};border-radius:{minutes_fill_radius};"></div>
          </div>
          <div style="font-size:9px;color:#6b7280;height:12px;line-height:12px;">{minutes_label}</div>
          <div style="display:flex;justify-content:center;align-items:center;font-size:10px;height:16px;line-height:16px;">{events}</div>
          <div style="font-size:10px;color:#9ca3af;line-height:14px;">{round_num}</div>
        </div>'''
        columns_html.append(column_html)

    # Complete HTML document with DOCTYPE and proper styling
    full_html = f'''<!DOCTYPE html>
<html>
<head>
  <style>
    body {{
      margin: 0;
      padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }}
    .chart-container {{
      display: flex;
      gap: {COLUMN_GAP}px;
      padding: 12px 16px;
      background: #f8fafc;
      border-radius: 12px;
      overflow-x: auto;
      width: 100%;
      box-sizing: border-box;
    }}
  </style>
</head>
<body>
  <div class="chart-container">
    {"".join(columns_html)}
  </div>
</body>
</html>'''

    # Use components.html with explicit height for reliable rendering
    components.html(full_html, height=CHART_HEIGHT, scrolling=True)


def render_chart_legend():
    """Render a legend for the season chart."""
    import streamlit.components.v1 as components

    legend_html = f'''<!DOCTYPE html>
<html>
<head>
  <style>
    body {{
      margin: 0;
      padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }}
    .legend {{
      display: flex;
      gap: 1.5rem;
      font-size: 0.8rem;
      color: #6b7280;
      margin-top: 10px;
      flex-wrap: wrap;
      padding: 10px;
      background: #f8fafc;
      border-radius: 8px;
      align-items: center;
    }}
    .legend-item {{
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .bar-sample {{
      position: relative;
      overflow: hidden;
      border-radius: 3px;
    }}
    .bar-fill {{
      position: absolute;
      bottom: 0;
      width: 100%;
      border-radius: 0 0 3px 3px;
    }}
  </style>
</head>
<body>
  <div class="legend">
    <div class="legend-item">
      <div class="bar-sample" style="width:14px;height:20px;background:{GRAY_COLOR};">
        <div class="bar-fill" style="height:70%;background:linear-gradient(to top,#ef4444,#22c55e,#3b82f6);"></div>
      </div>
      <span>Rating (0-10)</span>
    </div>
    <div class="legend-item">
      <div class="bar-sample" style="width:14px;height:16px;background:{GRAY_COLOR};">
        <div class="bar-fill" style="height:80%;background:linear-gradient(to top,#fbbf24,#16a34a);"></div>
      </div>
      <span>Minuti (0-90)</span>
    </div>
    <div class="legend-item">
      <div style="width:14px;height:16px;background:{GRAY_COLOR};border-radius:3px;"></div>
      <span>Non giocato</span>
    </div>
    <div>⚽ Goal</div>
    <div>👟 Assist</div>
    <div>🟨 Giallo</div>
    <div>🟥 Rosso</div>
  </div>
</body>
</html>'''

    components.html(legend_html, height=60)


def render_season_chart(season_data: List[dict]) -> str:
    """DEPRECATED: Use render_season_chart_streamlit() instead."""
    return ""
