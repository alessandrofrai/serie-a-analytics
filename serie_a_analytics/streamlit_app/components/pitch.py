"""
Pitch Visualization Component

Beautiful football pitch with player positions and color-coded contributions.
Shows player names clearly and visualizes contribution with both color and size.
"""

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle
from typing import Dict, Optional
import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config import FORMATION_COORDINATES


def render_formation(
    formation: str,
    player_values: Optional[Dict[int, float]] = None,
    player_names: Optional[Dict[int, str]] = None,
    selected_metric: Optional[str] = None,
    player_faces: Optional[Dict[int, np.ndarray]] = None,
    player_ratings: Optional[Dict[int, float]] = None,
    show_ratings: bool = False
):
    """
    Render a beautiful football pitch with formation and player markers.

    Args:
        formation: Formation string (e.g., "4-3-3")
        player_values: Dict mapping slot (1-11) to contribution percentage
        player_names: Dict mapping slot (1-11) to player surname
        selected_metric: Name of the selected metric (for title)
        player_faces: Dict mapping slot (1-11) to face image (numpy array)
        player_ratings: Dict mapping slot (1-11) to average SofaScore rating
        show_ratings: Whether to show rating badges under faces
    """
    coords = FORMATION_COORDINATES.get(formation, FORMATION_COORDINATES.get("4-3-3"))

    if coords is None:
        st.warning(f"Formazione '{formation}' non supportata")
        return

    # Create figure with dark theme
    fig, ax = plt.subplots(figsize=(10, 8), facecolor='#1a1a2e')
    ax.set_xlim(-8, 108)
    ax.set_ylim(-12, 112)
    ax.set_facecolor('#1a1a2e')

    # Draw pitch
    _draw_modern_pitch(ax)

    # Calculate max/min contribution for scaling (supports negative values)
    max_contribution = 1
    min_contribution = 0
    if player_values:
        values = list(player_values.values())
        if values:
            max_contribution = max(values) if values else 1
            min_contribution = min(values) if values else 0

    # Draw players
    for slot, pos_info in coords.items():
        x = pos_info['x']
        y = pos_info['y']
        position = pos_info['position']

        # Get player name
        name = player_names.get(slot, position) if player_names else position

        # Get contribution if available
        contribution = player_values.get(slot, 0) if player_values else None

        # Get face image and rating if available
        face_image = player_faces.get(slot) if player_faces else None
        rating = player_ratings.get(slot) if player_ratings else None

        # Draw player
        _draw_player_marker(
            ax, x, y, name, position,
            contribution=contribution,
            max_contribution=max_contribution,
            min_contribution=min_contribution,
            show_contribution=player_values is not None,
            face_image=face_image,
            rating=rating,
            show_rating=show_ratings
        )

    ax.set_aspect('equal')
    ax.axis('off')

    # Add title if metric selected
    if selected_metric and player_values:
        metric_display = selected_metric.replace('_', ' ').title()
        ax.text(
            50, 108,
            f"Contributo: {metric_display}",
            ha='center', va='bottom',
            fontsize=12, fontweight='bold',
            color='white'
        )

    # Add legend if values are shown
    if player_values:
        _add_modern_legend(fig, ax, has_negative=min_contribution < 0)

    # Use full canvas to avoid distortion from tight bounding boxes
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    st.pyplot(fig)
    plt.close()


def _draw_modern_pitch(ax):
    """Draw a modern, beautiful football pitch."""
    # Pitch colors
    pitch_color = '#16a34a'  # Vibrant green
    line_color = 'rgba(255,255,255,0.9)'
    line_width = 2

    # Add grass pattern effect (stripes)
    for i in range(10):
        stripe_color = '#15803d' if i % 2 == 0 else '#16a34a'
        stripe = patches.Rectangle(
            (i * 10, 0), 10, 100,
            facecolor=stripe_color,
            edgecolor='none',
            zorder=0
        )
        ax.add_patch(stripe)

    # Main pitch border
    pitch_border = FancyBboxPatch(
        (0, 0), 100, 100,
        boxstyle="round,pad=0,rounding_size=2",
        facecolor='none',
        edgecolor='white',
        linewidth=3,
        zorder=2
    )
    ax.add_patch(pitch_border)

    # Center line
    ax.plot([50, 50], [0, 100], color='white', linewidth=line_width, zorder=2)

    # Center circle
    center_circle = Circle(
        (50, 50), 9.15,
        fill=False,
        color='white',
        linewidth=line_width,
        zorder=2
    )
    ax.add_patch(center_circle)

    # Center spot
    center_spot = Circle((50, 50), 1, color='white', zorder=2)
    ax.add_patch(center_spot)

    # Penalty areas
    for x_start, direction in [(0, 1), (100, -1)]:
        # Large box
        large_box = patches.Rectangle(
            (x_start if direction == 1 else x_start - 16.5, 21),
            16.5, 58,
            fill=False,
            edgecolor='white',
            linewidth=line_width,
            zorder=2
        )
        ax.add_patch(large_box)

        # Small box
        small_box = patches.Rectangle(
            (x_start if direction == 1 else x_start - 5.5, 37),
            5.5, 26,
            fill=False,
            edgecolor='white',
            linewidth=line_width,
            zorder=2
        )
        ax.add_patch(small_box)

        # Penalty spot
        pen_spot = Circle(
            (x_start + 11 * direction, 50), 0.5,
            color='white', zorder=2
        )
        ax.add_patch(pen_spot)

        # Penalty arc
        theta = np.linspace(-0.6, 0.6, 30) if direction == 1 else np.linspace(np.pi - 0.6, np.pi + 0.6, 30)
        arc_x = x_start + 11 * direction + 9.15 * np.cos(theta)
        arc_y = 50 + 9.15 * np.sin(theta)
        ax.plot(arc_x, arc_y, color='white', linewidth=line_width, zorder=2)

    # Goals (3D effect)
    for x_pos in [-3, 100]:
        goal_color = '#ffffff' if x_pos < 0 else '#ffffff'
        goal = patches.Rectangle(
            (x_pos, 44), 3, 12,
            facecolor=goal_color,
            edgecolor='white',
            linewidth=2,
            alpha=0.8,
            zorder=3
        )
        ax.add_patch(goal)

    # Corner arcs
    for corner in [(0, 0), (0, 100), (100, 0), (100, 100)]:
        theta_start = {
            (0, 0): 0, (0, 100): 270, (100, 0): 90, (100, 100): 180
        }[corner]
        arc = patches.Arc(
            corner, 2, 2,
            angle=0, theta1=theta_start, theta2=theta_start + 90,
            color='white', linewidth=line_width, zorder=2
        )
        ax.add_patch(arc)


def _hex_to_rgb(hex_color: str):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def _interpolate_color(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return _rgb_to_hex((r, g, b))


def _get_rating_color(rating: float) -> str:
    """
    Map rating to a red -> orange -> yellow -> light green -> dark green scale.
    6.9 is the light green midpoint (as requested).
    """
    stops = [
        (5.5, "#ef4444"),  # red
        (6.2, "#f59e0b"),  # orange
        (6.6, "#fbbf24"),  # yellow
        (6.9, "#86efac"),  # light green (avg ~ 6.9)
        (7.5, "#16a34a"),  # green
        (8.0, "#065f46"),  # dark green
    ]

    if rating <= stops[0][0]:
        return stops[0][1]
    if rating >= stops[-1][0]:
        return stops[-1][1]

    for i in range(len(stops) - 1):
        r0, c0 = stops[i]
        r1, c1 = stops[i + 1]
        if rating <= r1:
            t = (rating - r0) / (r1 - r0) if r1 != r0 else 0
            return _interpolate_color(c0, c1, t)
    return stops[-1][1]


def _get_contrast_text_color(bg_hex: str) -> str:
    r, g, b = _hex_to_rgb(bg_hex)
    # Perceived luminance
    luminance = (0.299 * r + 0.587 * g + 0.114 * b)
    return '#0f172a' if luminance > 160 else '#ffffff'


def _draw_player_marker(
    ax, x: float, y: float, name: str, position: str,
    contribution: Optional[float] = None,
    max_contribution: float = 1,
    min_contribution: float = 0,
    show_contribution: bool = False,
    face_image: Optional[np.ndarray] = None,
    rating: Optional[float] = None,
    show_rating: bool = False
):
    """Draw a beautiful player marker with name."""

    # Determine colors and size based on contribution
    if show_contribution and contribution is not None and contribution != 0:
        # Check if we have negative values (divergent scale)
        has_negative = min_contribution < 0

        if has_negative:
            # DIVERGENT SCALE: Red (negative) -> Grey (zero) -> Green (positive)
            if contribution < 0:
                # Negative values: grey -> red
                intensity = min(1.0, abs(contribution) / max(abs(min_contribution), 0.01))
                # Red color for underperforming
                r = int(128 + (239 - 128) * intensity)  # 128 -> 239
                g = int(128 + (68 - 128) * intensity)   # 128 -> 68
                b = int(128 + (68 - 128) * intensity)   # 128 -> 68
            else:
                # Positive values: grey -> green
                intensity = min(1.0, contribution / max(max_contribution, 0.01))
                # Green color for overperforming
                r = int(128 + (34 - 128) * intensity)   # 128 -> 34
                g = int(128 + (197 - 128) * intensity)  # 128 -> 197
                b = int(128 + (94 - 128) * intensity)   # 128 -> 94

            radius = 4 + 3 * intensity  # 4-7 range
        else:
            # STANDARD SCALE: Blue (low) -> Yellow (mid) -> Red (high)
            intensity = min(1.0, contribution / max(max_contribution, 1))

            if intensity < 0.5:
                # Blue to Yellow
                r = int(59 + (250 - 59) * (intensity * 2))
                g = int(130 + (204 - 130) * (intensity * 2))
                b = int(246 + (21 - 246) * (intensity * 2))
            else:
                # Yellow to Red
                r = int(250 + (239 - 250) * ((intensity - 0.5) * 2))
                g = int(204 + (68 - 204) * ((intensity - 0.5) * 2))
                b = int(21 + (68 - 21) * ((intensity - 0.5) * 2))

            radius = 4 + 3 * intensity  # 4-7 range

        marker_color = f'#{r:02x}{g:02x}{b:02x}'
        edge_color = 'white'
        edge_width = 2.5
    else:
        # Default: team color (blue-ish)
        marker_color = '#3b82f6'
        radius = 4.5
        edge_color = 'white'
        edge_width = 2

    # Player marker with shadow
    shadow = Circle(
        (x + 0.5, y - 0.5), radius,
        facecolor='#000000',
        alpha=0.3,
        zorder=4
    )
    ax.add_patch(shadow)

    if face_image is not None:
        # Border ring (use contribution color when available)
        border_color = marker_color if show_contribution else 'white'
        border = Circle(
            (x, y), radius,
            facecolor='none',
            edgecolor=border_color,
            linewidth=edge_width,
            zorder=6
        )
        ax.add_patch(border)

        # Face image clipped to the circle
        try:
            im = ax.imshow(
                face_image,
                extent=(x - radius, x + radius, y - radius, y + radius),
                zorder=5
            )
            im.set_clip_path(border)
        except Exception:
            # Fallback to colored circle if image rendering fails
            circle = Circle(
                (x, y), radius,
                facecolor=marker_color,
                edgecolor=edge_color,
                linewidth=edge_width,
                zorder=5
            )
            ax.add_patch(circle)
    else:
        # Main circle
        circle = Circle(
            (x, y), radius,
            facecolor=marker_color,
            edgecolor=edge_color,
            linewidth=edge_width,
            zorder=5
        )
        ax.add_patch(circle)

        # Position abbreviation inside circle
        ax.text(
            x, y,
            position,
            ha='center', va='center',
            fontsize=9, fontweight='bold',
            color='white',
            zorder=6
        )

    # Player name below (with background for readability)
    name_display = name  # Full name without truncation

    # Name background
    bbox_props = dict(
        boxstyle="round,pad=0.2",
        facecolor='#1a1a2e',
        edgecolor='none',
        alpha=0.8
    )

    # Optional badge below player (rating or contribution)
    badge_box_height = 2.4
    badge_box_width = 7.2
    badge_center_y = None

    if show_rating and rating is not None:
        badge_center_y = y - radius - 1.6
        badge_color = _get_rating_color(rating)
        text_color = _get_contrast_text_color(badge_color)

        badge_box = FancyBboxPatch(
            (x - badge_box_width / 2, badge_center_y - badge_box_height / 2),
            badge_box_width, badge_box_height,
            boxstyle="round,pad=0.2,rounding_size=0.6",
            facecolor=badge_color,
            edgecolor='white',
            linewidth=1,
            zorder=6
        )
        ax.add_patch(badge_box)

        ax.text(
            x, badge_center_y,
            f"{rating:.2f}",
            ha='center', va='center',
            fontsize=7.5, fontweight='bold',
            color=text_color,
            zorder=7
        )
    elif show_contribution and contribution is not None and contribution != 0:
        badge_center_y = y - radius - 1.6
        badge_border = marker_color
        badge_fill = _interpolate_color(marker_color, "#ffffff", 0.55)

        badge_box = FancyBboxPatch(
            (x - badge_box_width / 2, badge_center_y - badge_box_height / 2),
            badge_box_width, badge_box_height,
            boxstyle="round,pad=0.2,rounding_size=0.6",
            facecolor=badge_fill,
            edgecolor=badge_border,
            linewidth=1,
            zorder=6
        )
        ax.add_patch(badge_box)

        # Format with sign for divergent metrics
        if contribution > 0:
            contribution_text = f"+{contribution:.1f}"
        else:
            contribution_text = f"{contribution:.1f}"

        ax.text(
            x, badge_center_y,
            contribution_text,
            ha='center', va='center',
            fontsize=7.5, fontweight='bold',
            color='#0f172a',
            zorder=7
        )

    # Player name below (with background for readability)
    if badge_center_y is not None:
        name_y = badge_center_y - (badge_box_height / 2) - 1.0
    else:
        name_y = y - radius - 2

    ax.text(
        x, name_y,
        name_display,
        ha='center', va='top',
        fontsize=8, fontweight='bold',
        color='white',
        bbox=bbox_props,
        zorder=6
    )

    # (Removed: contribution label above player; now shown below as badge)


def _add_modern_legend(fig, ax, has_negative: bool = False):
    """Add a modern color legend."""
    # Create colorbar axes
    cbar_ax = fig.add_axes([0.15, 0.02, 0.7, 0.025])

    # Create gradient
    gradient = np.linspace(0, 1, 256).reshape(1, -1)

    from matplotlib.colors import LinearSegmentedColormap

    if has_negative:
        # DIVERGENT SCALE: Red (negative) -> Grey (zero) -> Green (positive)
        colors = ['#ef4444', '#808080', '#22c55e']
        cmap = LinearSegmentedColormap.from_list('divergent', colors)
        cbar_ax.imshow(gradient, aspect='auto', cmap=cmap)
        cbar_ax.set_xticks([0, 128, 256])
        cbar_ax.set_xticklabels(['Negativo', 'Zero', 'Positivo'], fontsize=9, color='white')
        cbar_ax.set_title('Differenza rispetto a xG', fontsize=10, color='white', pad=5)
    else:
        # STANDARD SCALE: Blue (low) -> Yellow (mid) -> Red (high)
        colors = ['#3b82f6', '#fbbf24', '#ef4444']
        cmap = LinearSegmentedColormap.from_list('contribution', colors)
        cbar_ax.imshow(gradient, aspect='auto', cmap=cmap)
        cbar_ax.set_xticks([0, 128, 256])
        cbar_ax.set_xticklabels(['Basso', 'Medio', 'Alto'], fontsize=9, color='white')
        cbar_ax.set_title('Contributo alla metrica', fontsize=10, color='white', pad=5)

    cbar_ax.set_yticks([])

    # Style the colorbar
    cbar_ax.spines['top'].set_visible(False)
    cbar_ax.spines['bottom'].set_visible(False)
    cbar_ax.spines['left'].set_visible(False)
    cbar_ax.spines['right'].set_visible(False)
    cbar_ax.tick_params(colors='white')


def render_formation_simple(formation: str, player_names: Optional[Dict[int, str]] = None):
    """
    Render a simple formation view without contribution data.
    Used when no metric is selected.
    """
    render_formation(formation, player_values=None, player_names=player_names)


def render_formation_to_base64(
    formation: str,
    player_names: Optional[Dict[int, str]] = None,
    player_values: Optional[Dict[int, float]] = None,
    player_faces: Optional[Dict[int, np.ndarray]] = None,
    player_ratings: Optional[Dict[int, float]] = None,
    show_ratings: bool = False,
    width: int = 600,
    height: int = 480
) -> str:
    """
    Generate formation pitch and return as base64 PNG for PDF export.

    Args:
        formation: Formation string (e.g., "4-3-3")
        player_names: Dict mapping slot (1-11) to player surname
        player_values: Dict mapping slot (1-11) to contribution percentage
        player_faces: Dict mapping slot (1-11) to face image (numpy array)
        player_ratings: Dict mapping slot (1-11) to average SofaScore rating
        show_ratings: Whether to show rating badges under faces
        width: Image width in pixels
        height: Image height in pixels

    Returns:
        Base64 data URL string (data:image/png;base64,...)
    """
    import io
    import base64

    coords = FORMATION_COORDINATES.get(formation, FORMATION_COORDINATES.get("4-3-3"))

    if coords is None:
        # Return empty placeholder if formation not supported
        return ""

    # Create figure with dark theme
    fig, ax = plt.subplots(figsize=(width/100, height/100), facecolor='#1a1a2e')
    ax.set_xlim(-8, 108)
    ax.set_ylim(-12, 112)
    ax.set_facecolor('#1a1a2e')

    # Draw pitch
    _draw_modern_pitch(ax)

    show_contributions = player_values is not None
    max_contribution = max(player_values.values()) if player_values else 1

    # Draw players (detailed version for PDF)
    for slot, pos_info in coords.items():
        x = pos_info['x']
        y = pos_info['y']
        position = pos_info['position']

        # Get player name
        name = player_names.get(slot, position) if player_names else position

        # Get contribution if available
        contribution = player_values.get(slot) if player_values else None

        # Get face image and rating if available
        face_image = player_faces.get(slot) if player_faces else None
        rating = player_ratings.get(slot) if player_ratings else None

        _draw_player_marker(
            ax, x, y, name, position,
            contribution=contribution,
            max_contribution=max_contribution,
            show_contribution=show_contributions,
            face_image=face_image,
            rating=rating,
            show_rating=show_ratings
        )

    ax.set_aspect('equal')
    ax.axis('off')

    plt.tight_layout(pad=0.5)

    # Export to base64
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=200,
                facecolor='#1a1a2e', edgecolor='none', pad_inches=0)
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close(fig)

    return f"data:image/png;base64,{img_base64}"


def _draw_player_marker_simple(ax, x: float, y: float, name: str, position: str):
    """Draw a simplified player marker for PDF export (no faces, no ratings)."""
    marker_color = '#3b82f6'
    radius = 4.5
    edge_color = 'white'
    edge_width = 2

    # Player marker with shadow
    shadow = Circle(
        (x + 0.5, y - 0.5), radius,
        facecolor='#000000',
        alpha=0.3,
        zorder=4
    )
    ax.add_patch(shadow)

    # Main circle
    circle = Circle(
        (x, y), radius,
        facecolor=marker_color,
        edgecolor=edge_color,
        linewidth=edge_width,
        zorder=5
    )
    ax.add_patch(circle)

    # Position abbreviation inside circle
    ax.text(
        x, y,
        position,
        ha='center', va='center',
        fontsize=9, fontweight='bold',
        color='white',
        zorder=6
    )

    # Player name below
    name_y = y - radius - 2

    bbox_props = dict(
        boxstyle="round,pad=0.2",
        facecolor='#1a1a2e',
        edgecolor='none',
        alpha=0.8
    )

    ax.text(
        x, name_y,
        name,
        ha='center', va='top',
        fontsize=8, fontweight='bold',
        color='white',
        bbox=bbox_props,
        zorder=6
    )
