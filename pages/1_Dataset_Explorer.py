from pathlib import Path

import pandas as pd
import streamlit as st

from src.charts.sunburst import (
    PARAMETER_GROUPS, build_sunburst, prepare_sunburst_data,
)
from src.ui.theme import card_header, card_result, card_plot


DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "data" / "analysisdataset" / "global_ev_cleaned.csv"
)


@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)


st.title("Dataset Explorer")
st.caption("Explore the dataset hierarchy · Source: IEA Global EV Outlook 2026")

with st.container(border=False, key="chart_group_sunburst", gap="small"):
    card_header(
        "01 · Sunburst — Dataset Structure",
        "How are EV indicators organized across parameters, vehicle modes, and powertrains?",
    )
    with st.container(border=True, key="card_plot_dataset_sunburst"):
        parameter_group = st.selectbox(
            "Parameter group", options=list(PARAMETER_GROUPS),
            key="sunburst_parameter_group",
        )
        df = load_data()
        prepared = prepare_sunburst_data(df, parameter_group)
        fig = build_sunburst(df, parameter_group=parameter_group)
        insight = ""
        if fig is not None:
            counts = prepared.groupby("parameter").size()
            leader = counts.idxmax()
            tied = int(counts.eq(counts.max()).sum())
            tie_note = f" (tied across {tied} indicators)" if tied > 1 else ""
            insight = (
                f"{leader} has the most unique mode-powertrain combinations "
                f"({counts.max():,}) in {parameter_group}{tie_note}."
            )
        historical = df.loc[
            df["category"].eq("Historical")
            & df["parameter"].isin(PARAMETER_GROUPS[parameter_group])
        ]
        years = historical["year"]
        period = f"{years.min():.0f}–{years.max():.0f}" if not years.empty else "No years"
        card_plot(fig, key="dataset_sunburst")
    card_result(
        fig, key="dataset_sunburst", insight=insight,
        scope=(f"Historical · {period} · {parameter_group} · "
               f"{len(prepared):,} unique combinations · All recorded geographies"),
        methodology=(
            "Each unique parameter → mode → powertrain combination counts once across "
            "historical records. Areas represent combination counts, not sales volumes "
            "or market shares; geography and year are not separate weights. Click a "
            "segment to drill down and the central parent to return; hover for counts."
        ),
    )
