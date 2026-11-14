"""Shared presentation for both dashboard pages."""

from copy import deepcopy
import re

import streamlit as st


OLIVE_NIGHT = {
    "page": "#1D2018", "navigation": "#465237", "card": "#30362A",
    "plot": "#252B21", "heading": "#D1E6AB", "text": "#F2F5EC",
    "secondary": "#C1CBB6", "accent": "#A7CD74", "border": "#566346",
}


def is_dark_mode():
    return st.session_state.get("ev_theme_mode", "Light") == "Dark"


def _store_theme_choice():
    st.session_state["ev_theme_mode"] = (
        "Light" if st.session_state["_ev_light_switch"] else "Dark"
    )



def render_theme_selector():
    """Render the theme switch."""

    st.session_state.setdefault("ev_theme_mode", "Light")
    st.session_state["_ev_light_switch"] = (
        st.session_state["ev_theme_mode"] == "Light"
    )

    with st.container(
        horizontal=True,
        vertical_alignment="center",
        width="content",
        key="theme_controls",
    ):
        st.toggle(
            "Theme",
            label_visibility="collapsed",
            key="_ev_light_switch",
            on_change=_store_theme_choice,
        )

def apply_theme():
    """Style the application shell without changing chart color semantics."""
    
    st.markdown(
        """<style>

                /* Align labels directly beside the switch */
        .st-key-theme_controls {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 190px !important;
            min-width: 190px;
        }

        .st-key-theme_controls label:has(input[role="switch"]) {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            white-space: nowrap;
        }

        .st-key-theme_controls label:has(input[role="switch"])::before {
            content: "Dark";
            font-size: 14px;
            font-weight: 500;
        }

        .st-key-theme_controls label:has(input[role="switch"])::after {
            content: "Light";
            font-size: 14px;
            font-weight: 500;
        }
        .stApp { background: #DCEBDD; color: #243b35; }
        [data-testid="stHeader"], [data-testid="stTopNav"] {
            background: #9FC9AC;
        }
        /* Only our keyed control is positioned; native navigation stays intact. */
        .st-key-theme_controls {
            position: fixed;
            width: 190px !important;
            min-width: 190px;
            height: 40px;
            top: 10px;
            right: 12rem;
            z-index: 1000001;
            padding: 0.25rem 0.5rem;
            border-radius: 999px;
            background: #9FC9AC;
            color: #155E3C;
            display: flex !important;
            flex-direction: row !important;
            justify-content: center !important;
            align-items: center !important;
            gap: 8px !important;
            flex-wrap: nowrap !important;
        }
        /* Prevent Streamlit from stretching the two text blocks. */
        .st-key-theme_controls > div {
            flex: 0 0 auto !important;
            width: auto !important;
            min-width: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        .st-key-theme_controls p {
            margin: 0 !important;
            font-size: 0.875rem;
            line-height: 1 !important;
            white-space: nowrap;
        }
        .st-key-theme_controls [data-testid="stToggle"] {
            display: flex;
            align-items: center;
            margin: 0 !important;
            padding: 0 !important;
        }
        .st-key-theme_controls label {
            margin: 0 !important;
            padding: 0 !important;
            display: flex;
            align-items: center;
        }

        .st-key-theme_controls label:has(input[role="switch"]) > div:not([data-testid]) {
            background: #465237;
        }
        .st-key-theme_controls label[data-selected]:has(input[role="switch"]) > div:not([data-testid]) {
            background: #237A52;
        }
        [data-testid="stTopNav"] { max-width: calc(100% - 23rem); }
        .stMainBlockContainer { padding-top: 5rem; }
        @media (max-width: 1099px) {
            /* A second header row keeps both navigation and switch usable. */
            [data-testid="stHeader"] { height: 112px; align-items: flex-start; }
            [data-testid="stToolbar"] { height: 60px; }
            [data-testid="stTopNav"] { max-width: 100%; align-self: flex-start; }
            .st-key-theme_controls { top: 64px; right: 1rem; }
            .stMainBlockContainer { padding-top: 7.5rem; }
        }
        [data-testid="stTopNavLink"], [data-testid="stTopNavDropdownLink"] {
            text-transform: uppercase;
            border-radius: 999px;
            border: 1px solid transparent;
            background: rgba(255, 255, 255, 0.25);
            color: #315B40;
            padding: 0.45rem 0.9rem;
            margin: 0.25rem;
        }
        [data-testid="stTopNavLink"][aria-current="page"],
        [data-testid="stTopNavDropdownLink"][aria-current="page"] {
            background: #EAF5ED;
            border-color: #155E3C;
            color: #155E3C;
            box-shadow: 0 0 0 2px rgba(21, 94, 60, 0.10),
                        0 2px 10px rgba(21, 94, 60, 0.18);
            font-weight: 700;
        }
        [data-testid="stTopNavLink"] *,
        [data-testid="stTopNavDropdownLink"] * {
            color: inherit;
            font-weight: inherit;
        }
        [data-testid="stTopNavLink"]:focus-visible,
        [data-testid="stTopNavDropdownLink"]:focus-visible {
            outline: 2px solid #155E3C;
            outline-offset: 2px;
        }
        /* Preserve Streamlit's responsive top clearance for its fixed header. */
        .stMainBlockContainer { padding-bottom: 3rem; }
        h1, h2, h3 { color: #145e51; }
        [class*="st-key-card_"] {
            background: #FFFFFF; border-color: #c0d3c4;
            border-radius: 12px;
        }
        [class*="st-key-card_header_"] {
            border: 1px solid #D2DFD5;
            border-left: 4px solid #237A52;
        }
        [class*="st-key-card_header_"] strong { color: #155E3C; }
        [class*="st-key-card_plot_"] [data-testid="stElementToolbar"] {
            opacity: 1;
            visibility: visible;
            pointer-events: auto;
        }
        [data-testid="stCaptionContainer"] { color: #526b62; }
        [data-baseweb="tab-highlight"] { background-color: #168574; }
        [aria-selected="true"][role="tab"] { color: #146d5c; }
        [data-baseweb="tag"] { background-color: #e0f2eb; color: #145e51; }
        a { color: #147b69; }
        </style>""",
        unsafe_allow_html=True,
    )
    if is_dark_mode():
        apply_dark_theme()


def apply_dark_theme():
    """Scoped overrides; no generated Emotion classes or positional selectors."""
    p = OLIVE_NIGHT
    css = """
        .stApp { background: PAGE; color: TEXT; color-scheme: dark; }
        [data-testid="stHeader"], [data-testid="stTopNav"] { background: NAV; }
        .st-key-theme_controls { background: NAV; color: TEXT; }
        .st-key-theme_controls label:has(input[role="switch"]) > div:not([data-testid]) {
            background: BORDER;
        }
        .st-key-theme_controls label[data-selected]:has(input[role="switch"]) > div:not([data-testid]) {
            background: ACCENT;
        }
        h1, h2, h3, [class*="st-key-card_header_"] strong { color: HEADING; }
        [class*="st-key-card_"] { background: CARD; border-color: BORDER; }
        [class*="st-key-card_header_"] { border-left-color: ACCENT; }
        [data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"],
        .st-key-theme_controls label { color: TEXT; }
        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] [data-testid="stMarkdownContainer"] {
            color: SECONDARY;
        }
        [data-testid="stTopNavLink"], [data-testid="stTopNavDropdownLink"] {
            background: CARD; color: SECONDARY;
        }
        [data-testid="stTopNavLink"][aria-current="page"],
        [data-testid="stTopNavDropdownLink"][aria-current="page"] {
            background: CARD; color: ACCENT; border-color: ACCENT;
            box-shadow: 0 0 0 2px rgba(167,205,116,.12),
                        0 2px 10px rgba(167,205,116,.2);
        }
        [data-testid="stTopNavLink"] [data-testid="stMarkdownContainer"],
        [data-testid="stTopNavDropdownLink"] [data-testid="stMarkdownContainer"] {
            color: inherit;
        }
        a, [aria-selected="true"][role="tab"] { color: ACCENT; }
        [role="tab"] { color: SECONDARY; }
        [data-baseweb="tab-highlight"] { background: ACCENT; }
        [data-testid="stSelectbox"] [data-baseweb="select"] > div,
        [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
            background: PLOT; color: TEXT; border-color: BORDER;
        }
        [data-baseweb="select"] input { color: TEXT; caret-color: ACCENT; }
        [data-baseweb="select"] svg { fill: SECONDARY; }
        [data-baseweb="tag"] { background: NAV; color: TEXT; }
        [data-baseweb="popover"], [role="listbox"], [role="option"] {
            background: CARD; color: TEXT;
        }
        [role="option"]:hover, [role="option"][aria-selected="true"] {
            background: NAV;
        }
        [data-testid="stExpander"] details {
            background: CARD; color: TEXT; border-color: BORDER;
        }
        [data-testid="stExpander"] summary,
        [data-testid="stExpander"] summary:hover { color: TEXT; background: CARD; }
        [data-testid="stAlert"] { background: PLOT; color: TEXT; }
        [data-testid="stAlert"] svg { fill: ACCENT; }
        [class*="st-key-card_plot_"] [data-testid="stFullScreenFrame"] {
            background: PLOT;
        }
        [class*="st-key-card_plot_"] [data-testid="stElementToolbar"] button {
            background: CARD; color: TEXT;
        }
        [class*="st-key-card_plot_"] .modebar { background: transparent !important; }
        [class*="st-key-card_plot_"] .modebar-btn path { fill: SECONDARY; }
        [class*="st-key-card_plot_"] .modebar-btn.active path,
        [class*="st-key-card_plot_"] .modebar-btn:hover path { fill: ACCENT; }
    """
    for token, value in {
        "PAGE": p["page"], "NAV": p["navigation"], "CARD": p["card"],
        "PLOT": p["plot"], "HEADING": p["heading"], "TEXT": p["text"],
        "SECONDARY": p["secondary"], "ACCENT": p["accent"], "BORDER": p["border"],
    }.items():
        css = css.replace(token, value)
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def display_title(title):
    """Remove the chart number only at the presentation layer."""
    return re.sub(r"^\s*\d+\s*[·.—–|:-]\s*", "", title).upper()


def card_header(title, question):
    with st.container(border=True, key=f"card_header_{title.split(' · ')[0]}"):
        st.markdown(f"**{display_title(title)}**")
        st.write(question)


def card_plot(fig, *, key, selectable=False):
    """Keep the original figure and tools inside the dedicated graph card.

    selectable=True opts a chart into Streamlit's selection tools (Box/Lasso Select).
    """
    if fig is None:
        st.info("No comparable data is available for this selection.")
    else:
        # A presentation copy leaves builder output, metadata and data untouched.
        presentation = themed_figure(fig)
        if presentation.layout.title.text:
            presentation.update_layout(title=dict(
                text=display_title(presentation.layout.title.text),
                font=dict(color=OLIVE_NIGHT["heading"] if is_dark_mode() else "#155E3C", weight=700),
            ))
        # Streamlit provides the native fullscreen toolbar, including Parcoords.
        # No Cartesian zoom buttons are injected into non-Cartesian charts.
        options = dict(
            width="stretch", key=key, theme=None,
            config={"displayModeBar": True, "responsive": True},
        )
        # Streamlit removes Box/Lasso Select unless selection events are enabled.
        # Only charts that opt in get them; the figure's own dragmode, click mode
        # and selected/unselected styling are left as the chart builder set them.
        if selectable:
            options.update(on_select="rerun", selection_mode=("points", "box", "lasso"))
        st.plotly_chart(presentation, **options)


def themed_figure(fig):
    """Copy before changing surface/font styles; keep trace colors and data."""
    presentation = deepcopy(fig)
    if not is_dark_mode():
        return presentation
    p = OLIVE_NIGHT
    presentation.update_layout(
        paper_bgcolor=p["plot"], font_color=p["text"],
        legend=dict(font_color=p["text"], bgcolor=p["plot"]),
        modebar=dict(bgcolor=p["plot"], color=p["secondary"], activecolor=p["accent"]),
    )
    # The heatmap's gray gap background encodes missing data, so preserve it.
    if not any(trace.type == "heatmap" for trace in presentation.data):
        presentation.update_layout(plot_bgcolor=p["plot"])
    for axis in list(presentation.select_xaxes()) + list(presentation.select_yaxes()):
        axis.update(color=p["secondary"], gridcolor=p["border"], zerolinecolor=p["border"])
    for annotation in presentation.layout.annotations:
        annotation.font.color = p["text"]
    # These trace-local fonts do not inherit layout.font; leave their colorscales alone.
    for trace in presentation.data:
        if trace.type == "parcoords":
            trace.update(labelfont_color=p["text"], tickfont_color=p["secondary"],
                         rangefont_color=p["text"])
        for parent in (trace, getattr(trace, "marker", None), getattr(trace, "line", None)):
            if parent is not None and "colorbar" in parent.to_plotly_json():
                colorbar = parent.colorbar
                colorbar.tickfont.color = p["secondary"]
                colorbar.title.font.color = p["text"]
    for coloraxis in presentation.select_coloraxes():
        coloraxis.colorbar.tickfont.color = p["secondary"]
        coloraxis.colorbar.title.font.color = p["text"]
    return presentation


def card_result(fig, *, key, insight, scope, methodology):
    """Render the separate explanation card below the graph."""
    with st.container(border=True, key=f"card_details_{key}"):
        if fig is not None:
            st.markdown(f"**Key Insight:** {insight}")
        st.caption(f"Coverage: {scope}")
        with st.expander("Methodology & Limitations", expanded=False):
            st.write(methodology)
