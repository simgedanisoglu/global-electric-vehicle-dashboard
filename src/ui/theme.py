
"""Shared dashboard styles."""

import streamlit as st


def apply_dashboard_theme():
    """Apply common styling to dashboard pages."""

    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1450px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        h1 {
            color: #243247;
            font-weight: 750;
            letter-spacing: -0.5px;
        }

        h2, h3 {
            color: #243247;
            font-weight: 650;
        }

        p {
            line-height: 1.65;
        }

        hr {
            border-color: #E2E8F0;
        }

        .stPlotlyChart {
            margin-top: 0.75rem;
            margin-bottom: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
