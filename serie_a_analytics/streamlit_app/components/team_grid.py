"""
Team Grid Component

Displays a grid of clickable team cards for selection.
"""

import streamlit as st
import pandas as pd

from utils.data_helpers import get_team_logo_html


def render_team_grid(teams_df: pd.DataFrame, combinations_df: pd.DataFrame):
    """
    Render a grid of team cards.

    Args:
        teams_df: DataFrame with team info
        combinations_df: DataFrame with team+manager combinations
    """
    # Sort teams by name
    teams_sorted = teams_df.sort_values('team_name')

    # Create columns for grid (5 columns)
    num_cols = 5
    rows = [teams_sorted.iloc[i:i+num_cols] for i in range(0, len(teams_sorted), num_cols)]

    for row in rows:
        cols = st.columns(num_cols)
        for idx, (_, team) in enumerate(row.iterrows()):
            with cols[idx]:
                team_id = team['team_id']
                team_name = team['team_name']

                # Get manager count for this team
                team_combos = combinations_df[combinations_df['team_id'] == team_id]
                num_managers = len(team_combos)

                # Get team logo
                logo_html = get_team_logo_html(team_id, size=50)

                # Create clickable card
                with st.container():
                    st.markdown(f"""
                    <div style="
                        padding: 1rem;
                        border: 2px solid #ddd;
                        border-radius: 10px;
                        text-align: center;
                        background: white;
                        min-height: 120px;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                    ">
                        <div style="margin-bottom: 0.5rem;">{logo_html}</div>
                        <div style="font-weight: bold; font-size: 0.9rem;">{team_name}</div>
                        <div style="color: #666; font-size: 0.75rem;">
                            {num_managers} allenator{'i' if num_managers > 1 else 'e'}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button(
                        "Seleziona",
                        key=f"team_{team_id}",
                        use_container_width=True
                    ):
                        st.session_state.selected_team = team_id
                        # Naviga a pagina separata per evitare ghosting
                        st.switch_page("pages/_dashboard.py")


def render_team_card(team_id: int, team_name: str, logo_url: str = None):
    """
    Render a single team card.

    Args:
        team_id: Team ID
        team_name: Team name
        logo_url: Optional logo URL
    """
    logo_display = "⚽"
    if logo_url:
        logo_display = f'<img src="{logo_url}" style="width: 50px; height: 50px;">'

    st.markdown(f"""
    <div class="team-card" onclick="selectTeam({team_id})">
        <div>{logo_display}</div>
        <div style="font-weight: bold; margin-top: 0.5rem;">{team_name}</div>
    </div>
    """, unsafe_allow_html=True)
