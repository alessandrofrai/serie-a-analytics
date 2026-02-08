"""
Serie A 2015-2016 Team Analytics Dashboard

Main Streamlit application entry point.
Shows team selection grid, then redirects to dashboard page.
"""

import streamlit as st

# Page config - MUST be first Streamlit command
st.set_page_config(
    page_title="Serie A 2015-2016 Data Analytics",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Import shared modules AFTER page config
from utils.styles import apply_custom_css
from utils.data_helpers import load_data
from components.team_grid import render_team_grid

# Apply shared CSS
apply_custom_css()


def main():
    """Main application entry point."""
    st.markdown('<div class="main-header">Serie A 2015-2016 Data Analytics</div>', unsafe_allow_html=True)

    data = load_data()

    if data is None:
        st.warning("Dati non trovati. Esegui prima gli script di elaborazione.")
        return

    # Initialize session state
    if 'selected_team' not in st.session_state:
        st.session_state.selected_team = None
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

    # ============ TEAM SELECTION ============
    if st.session_state.selected_team is None:
        st.subheader("Seleziona una Squadra")
        render_team_grid(data['teams'], data['combinations'])

        # Link to clustering analysis page
        st.markdown("---")
        if st.button("Approfondisci Clustering Stile di Gioco", use_container_width=True):
            st.switch_page("pages/_stili_di_gioco.py")
        return

    # ============ REDIRECT TO DASHBOARD ============
    # When a team is selected, redirect to dashboard page
    # This prevents ghosting by using separate pages
    st.switch_page("pages/_dashboard.py")


if __name__ == "__main__":
    main()
