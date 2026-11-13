from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from src.charts.connected_scatter import build_market_connected_scatter
from src.charts.diverging_heatmap import build_scenario_heatmap
from src.charts.parallel_coordinates import build_ev_mode_pcp
from src.charts.rank_dumbbell import build_rank_dumbbell, prepare_rank_dumbbell_data
from src.charts.sankey import build_energy_transition_sankey, prepare_energy_transition_data
from src.charts.splom import build_charging_splom, prepare_charging_splom_data
from src.charts.treemap import METRICS, build_energy_treemap
from src.charts.violin import PRICE_SEGMENTS, build_price_violin, prepare_price_violin_data
from src.ui.theme import card_header, card_result, card_plot


DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "analysisdataset"


@st.cache_data
def load_data():
    return pd.read_csv(DATA_DIR / "global_ev_cleaned.csv")


@st.cache_data
def load_scenario_data():
    return pd.read_csv(DATA_DIR / "ev_2035_scenario_comparison.csv")


st.title("Research & Insights")
st.caption("EV adoption, charging, prices, energy and scenarios · Source: IEA Global EV Outlook 2026")
tabs = st.tabs([
    "Market & Adoption", "Charging", "Prices", "Energy & Impact", "Future 2035",
])
df = load_data()

with tabs[0]:
    with st.container(border=False, key="chart_group_connected_scatter", gap="small"):
        card_header(
            "01 · Connected Scatterplot — EV Market Evolution",
            "How did global EV sales and the BEV share of BEV/PHEV sales evolve together?",
        )
        with st.container(border=True, key="card_plot_market_connected_scatter"):
            fig = build_market_connected_scatter(df)
            insight = ""
            scope = "Historical · World · Cars · EV sales (vehicles); BEV/(BEV+PHEV) (%)"
            if fig is not None:
                trace = fig.data[0]
                insight = (
                    f"World electric car sales were {trace.x[0]:,.0f} in {trace.text[0]} "
                    f"and {trace.x[-1]:,.0f} in {trace.text[-1]}; the BEV share of "
                    f"BEV/PHEV sales was {trace.y[0]:.1f}% and {trace.y[-1]:.1f}%, respectively."
                )
                scope += f" · {trace.text[0]}–{trace.text[-1]} · {len(trace.x)} matched years"
            card_plot(fig, key="market_connected_scatter")
        card_result(
            fig, key="market_connected_scatter", insight=insight, scope=scope,
            methodology=(
                "Points connect chronologically; hover for year and technology values, "
                "or use zoom/pan. Only years with valid EV, BEV and PHEV sales are included. "
                "The BEV share is 100 × BEV/(BEV+PHEV), not a share of all car sales. "
                "Published EV totals remain separate; temporal association is not causation."
            ),
        )

    with st.container(border=False, key="chart_group_rank_dumbbell", gap="small"):
        card_header(
            "02 · Rank Dumbbell — EV Market Rankings",
            "Do countries leading in EV sales volume also lead in EV sales share?",
        )
        with st.container(border=True, key="card_plot_rank_dumbbell_chart"):
            year = st.selectbox(
                "Historical year", options=list(range(2025, 2009, -1)),
                index=0, key="dumbbell_year",
            )
            prepared = prepare_rank_dumbbell_data(df, year=year, top_n=12)
            fig = build_rank_dumbbell(df, year=year, top_n=12)
            insight = ""
            if fig is not None:
                leader = prepared.loc[prepared["sales_rank"].eq(1)].iloc[0]
                insight = (
                    f"In {year}, {leader['region_country']} ranked first in EV car sales volume "
                    f"and had a sales-share rank of {leader['share_rank']:.0f} "
                    f"({leader['EV sales share']:.1f}%)."
                )
            card_plot(fig, key="rank_dumbbell_chart")
        card_result(
            fig, key="rank_dumbbell_chart", insight=insight,
            scope=f"Historical · {year} · Countries · Cars/EV · {len(prepared)} displayed countries · Rank (1 = highest)",
            methodology=(
                "Ranks are calculated across all countries with valid paired sales volume "
                "and sales share. The display is the union of the top 12 in either ranking; "
                "ties share a rank. Hover over either marker for country values. "
                "World and regional aggregates are excluded."
            ),
        )

    with st.container(border=False, key="chart_group_pcp", gap="small"):
        card_header(
            "07 · Parallel Coordinates — EV Adoption by Vehicle Type",
            "Did different vehicle types electrify at the same pace between 2020 and 2025?",
        )
        with st.container(border=True, key="card_plot_ev_mode_pcp_chart"):
            fig = build_ev_mode_pcp(df, start_year=2020, end_year=2025)
            insight = ""
            scope = "Historical · 2020–2025 · World · EV sales share (%)"
            if fig is not None:
                changes = fig.layout.meta["change_pp"]
                maximum = max(changes.values())
                leaders = ", ".join(mode for mode, change in changes.items() if change == maximum)
                insight = f"{leaders} recorded the largest EV sales-share change from 2020 to 2025 ({maximum:+.1f} percentage points)."
                scope += f" · {len(changes)} complete vehicle types"
            card_plot(fig, key="ev_mode_pcp_chart")
        card_result(
            fig, key="ev_mode_pcp_chart", insight=insight, scope=scope,
            methodology=(
                "Each line is a vehicle type with complete annual observations. "
                "Drag a range on an axis to brush matching profiles; clear the range to reset. "
                "Share changes are percentage points, not percentage growth. "
                "These shares describe new sales, not the entire fleet. "
                "Incomplete vehicle types are excluded."
            ),
        )

with tabs[1]:
    with st.container(border=False, key="chart_group_splom", gap="small"):
        card_header(
            "03 · Scatterplot Matrix — EV Stock and Charging",
            "Are larger electric car fleets associated with more public charging points?",
        )
        with st.container(border=True, key="card_plot_charging_splom_chart"):
            prepared = prepare_charging_splom_data(df, year=2025)
            fig = build_charging_splom(df, year=2025)
            insight = ""
            if fig is not None:
                rho = fig.layout.meta["spearman_ev_stock_public_chargers"]
                insight = (
                    f"Across {len(prepared)} matched countries, EV car stock and public charging "
                    f"points have a Spearman rank correlation of {rho:.2f}."
                    if np.isfinite(rho) else
                    "Rank correlation is undefined because one of the matched metrics is constant."
                )
            card_plot(fig, key="charging_splom_chart")
        card_result(
            fig, key="charging_splom_chart", insight=insight,
            scope=f"Historical · 2025 · {len(prepared)} complete countries · Cars/EV · Stock and public charging points",
            methodology=(
                "Countries must have EV stock, sales share and all three public charger "
                "types (slow, fast, ultra-fast). Missing records are not zero. Stock and "
                "charger counts use log10 scales; hover for original values and use box/lasso "
                "selection across panels. Cars per point is an approximate ratio. "
                "Correlation does not establish causation."
            ),
        )

with tabs[2]:
    with st.container(border=False, key="chart_group_violin", gap="small"):
        card_header(
            "04 · Violin Plot — BEV vs ICEV Price Gaps",
            "How does the BEV–ICEV median price gap vary across segments and countries?",
        )
        with st.container(border=True, key="card_plot_price_violin_chart"):
            selected_segments = st.multiselect(
                "Vehicle segments", options=list(PRICE_SEGMENTS),
                default=list(PRICE_SEGMENTS), key="violin_segments",
            )
            prepared = prepare_price_violin_data(df, segments=selected_segments, year=2025)
            fig = build_price_violin(df, segments=selected_segments, year=2025)
            insight = ""
            if fig is not None:
                below = prepared["price_gap_pct"].lt(0).sum()
                insight = (
                    f"BEV median prices are below ICEV medians in {below} of "
                    f"{len(prepared)} selected country–segment pairs; the median "
                    f"gap across these pairs is {prepared['price_gap_pct'].median():+.1f}%."
                )
            card_plot(fig, key="price_violin_chart")
        card_result(
            fig, key="price_violin_chart", insight=insight,
            scope=(f"Historical · 2025 · {prepared['region_country'].nunique()} countries · "
                   f"{len(prepared)} country–segment pairs · Gap (%) from 2025 USD medians"),
            methodology=(
                "Gap = 100 × (BEV median − ICEV median)/ICEV median, using paired positive "
                "country–segment prices in constant 2025 USD. Positive values indicate a BEV "
                "premium. These are country-level median gaps, not individual car prices; "
                "small samples may yield unstable densities. Select segments, hover over "
                "country points, or zoom to inspect distributions."
            ),
        )

with tabs[3]:
    with st.container(border=False, key="chart_group_treemap", gap="small"):
        card_header(
            "05 · Treemap — Global EV Energy Impacts",
            "Which vehicle types contribute most to oil displacement, battery deployment and electricity demand?",
        )
        with st.container(border=True, key="card_plot_energy_treemap_chart"):
            selected_metric = st.selectbox(
                "Energy impact metric", options=list(METRICS),
                format_func=lambda metric: METRICS[metric][0], key="treemap_metric",
            )
            fig = build_energy_treemap(df, metric=selected_metric, year=2025)
            insight = ""
            if fig is not None:
                trace = fig.data[0]
                leaves = [(label, float(value)) for label, parent, value in
                          zip(trace.labels, trace.parents, trace.values) if parent == "World"]
                maximum = max(value for _, value in leaves)
                leaders = ", ".join(label for label, value in leaves if value == maximum)
                share = 100 * maximum / sum(value for _, value in leaves)
                tie_note = " each" if sum(value == maximum for _, value in leaves) > 1 else ""
                insight = f"{leaders} lead in {METRICS[selected_metric][0].lower()}, contributing {share:.1f}%{tie_note} of the five-mode total."
            card_plot(fig, key="energy_treemap_chart")
        card_result(
            fig, key="energy_treemap_chart", insight=insight,
            scope=f"Historical · 2025 · World · EV · 5 vehicle types · {METRICS[selected_metric][0]} · {METRICS[selected_metric][1]}",
            methodology=(
                "Areas represent one selected metric across cars, buses, trucks, vans "
                "and two/three-wheelers. The denominator is the sum of these five World "
                "mode records, not World plus countries. Different metrics and units are "
                "never added together. Zero modes have no visible area. Change the metric, "
                "hover for values and shares, or click to drill down and return via the parent."
            ),
        )

    with st.container(border=False, key="chart_group_sankey", gap="small"):
        card_header(
            "06 · Sankey — Energy Demand Transition",
            "How did countries transition between electricity-demand-per-EV levels from 2020 to 2025?",
        )
        with st.container(border=True, key="card_plot_energy_sankey_chart"):
            prepared, thresholds = prepare_energy_transition_data(df, start_year=2020, end_year=2025)
            fig = build_energy_transition_sankey(df, start_year=2020, end_year=2025)
            insight = ""
            if fig is not None:
                unchanged = prepared["start_level"].eq(prepared["end_level"]).sum()
                insight = f"{unchanged} of {len(prepared)} matched countries remained in the same demand-per-EV category; {len(prepared) - unchanged} changed category between 2020 and 2025."
            card_plot(fig, key="energy_sankey_chart")
        card_result(
            fig, key="energy_sankey_chart", insight=insight,
            scope=f"Historical · 2020 → 2025 · {len(prepared)} matched countries · Cars/EV · Flows = country counts",
            methodology=(
                "Approximate annual demand per EV = electricity demand (GWh) × 1,000,000 "
                "/ year-end EV stock. Low/Medium/High use shared pooled tercile thresholds "
                "for both years, not official IEA categories. Only valid country pairs "
                "are included. Flow widths count countries, not energy volumes. Hover for "
                "transition details; drag nodes to rearrange."
            ),
        )

with tabs[4]:
    with st.container(border=False, key="chart_group_heatmap", gap="small"):
        card_header(
            "08 · Diverging Heatmap — 2035 Scenario Comparison",
            "Where are the largest relative STEPS–CPS differences across indicators and geographies in 2035?",
        )
        with st.container(border=True, key="card_plot_scenario_heatmap_chart"):
            fig = build_scenario_heatmap(load_scenario_data())
            insight = ""
            scope = "Projection · 2035 · STEPS vs CPS · Relative difference (%)"
            if fig is not None:
                trace = fig.data[0]
                values = np.asarray(trace.z, dtype=float)
                largest = np.nanmax(np.abs(values))
                positions = np.argwhere(np.abs(values) == largest)
                row, column = positions[0]
                tie_note = f" (tied across {len(positions)} cells)" if len(positions) > 1 else ""
                insight = (
                    f"{trace.x[column]} · {trace.y[row]} has the largest absolute relative "
                    f"scenario difference ({values[row, column]:+.1f}% versus CPS){tie_note}."
                )
                scope += f" · {len(trace.y)} indicators × {len(trace.x)} geographies · {np.isfinite(values).sum()} valid cells"
            card_plot(fig, key="scenario_heatmap_chart")
        card_result(
            fig, key="scenario_heatmap_chart", insight=insight, scope=scope,
            methodology=(
                "Relative difference = 100 × (STEPS − CPS)/abs(CPS), using paired 2035 "
                "projections. Colors diverge around zero; missing values and CPS=0 are "
                "undefined, not zero. Hover for scenario values and units. Even for sales "
                "shares, differences are relative percentages, not percentage points. "
                "Small CPS baselines can amplify percentages. Countries, regions and World "
                "are compared separately and never summed; these are not historical outcomes. "
                "Colors use a symmetric signed-log scale to improve the visibility of smaller differences. "
                "Hover values show the original percentages."
            ),
        )
