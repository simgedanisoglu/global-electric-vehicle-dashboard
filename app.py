
import streamlit as st

from src.ui.theme import apply_theme, render_theme_selector

st.set_page_config(
    page_title="Global EV Transition",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

pages = [
    st.Page(
        "pages/1_Dataset_Explorer.py",
        title="Dataset Explorer",
        default=True,
    ),
    st.Page(
        "pages/2_Research_Insights.py",
        title="Research & Insights",
    ),
]

# Add the ML page when it is ready.

navigation = st.navigation(
    pages,
    position="top",
)

apply_theme()
render_theme_selector()

navigation.run()
