
from pathlib import Path

import pandas as pd
import streamlit as st

from src.charts.sunburst import (
    PARAMETER_GROUPS,
    build_sunburst,
)
from src.ui.theme import apply_dashboard_theme


DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "analysisdataset"
    / "global_ev_cleaned.csv"
)


@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)


apply_dashboard_theme()

st.title("Dataset Explorer")
st.write(
    "Explore the structure of the IEA Global EV dataset "
    "through an interactive hierarchical visualization."
)
st.caption("Source: IEA Global EV Outlook 2026")


st.subheader("01 · Sunburst — Dataset Structure")

st.markdown(
    "**Research question:** How are EV indicators organized "
    "across parameters, vehicle modes, and powertrain types?"
)

parameter_group = st.selectbox(
    "Parameter group",
    options=list(PARAMETER_GROUPS.keys()),
    key="sunburst_parameter_group",
)

df = load_data()

fig = build_sunburst(
    df,
    parameter_group=parameter_group,
)

if fig is not None:
    st.plotly_chart(
        fig,
        width="stretch",
        key="dataset_sunburst",
    )
else:
    st.info(
        "No data is available for the selected parameter group."
    )

st.markdown("**How to read:**")
st.write(
    "The chart shows a three-level hierarchy: "
    "parameter → vehicle mode → powertrain. "
    "Click a segment to explore its subcategories."
)

st.markdown("**Coverage and limitations:**")
st.write(
    "The visualization uses historical records and counts "
    "unique combinations of parameters, vehicle modes, "
    "and powertrains. Segment sizes do not represent "
    "EV sales volumes or market shares."
)
