import streamlit as st

from pathlib import Path

import pandas as pd

from src.charts.rank_dumbbell import build_rank_dumbbell
from src.charts.sankey import build_energy_transition_sankey
from src.charts.connected_scatter import build_market_connected_scatter
from src.charts.parallel_coordinates import build_ev_mode_pcp
from src.charts.splom import (
    build_charging_splom,
    prepare_charging_splom_data,
)
from src.charts.violin import (
    PRICE_SEGMENTS,
    build_price_violin,
    prepare_price_violin_data,
)
from src.charts.treemap import build_energy_treemap, METRICS
from src.charts.diverging_heatmap import build_scenario_heatmap

DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "analysisdataset"
    / "global_ev_cleaned.csv"
)


@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)

SCENARIO_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "analysisdataset"
    / "ev_2035_scenario_comparison.csv"
)


@st.cache_data
def load_scenario_data():
    return pd.read_csv(SCENARIO_PATH)


st.title("Research & Insights")

st.write(
    "Explore global EV adoption, charging infrastructure, "
    "vehicle prices, energy impacts, and future scenarios."
)

st.caption("Source: IEA Global EV Outlook 2026")


tabs = st.tabs([
    "Market & Adoption",
    "Charging",
    "Prices",
    "Energy & Impact",
    "Future 2035",
])



with tabs[0]:
    st.subheader("Market & Adoption")

   
    st.subheader("01 · Connected Scatterplot — EV Market Evolution")

    st.markdown(
        "**Research question:** How have global EV sales volumes "
        "and the BEV share of BEV/PHEV sales evolved together "
        "from 2010 to 2025?"
    )

    df = load_data()

    fig = build_market_connected_scatter(df)

    if fig is not None:
        st.plotly_chart(
            fig,
            width="stretch",
            key="market_connected_scatter",
        )
    else:
        st.info(
            "No valid historical global EV sales data "
            "is available for this visualization."
        )

    st.markdown("**How to read:**")
    st.write(
        "Each point represents a year. The horizontal axis "
        "shows global electric car sales, while the vertical "
        "axis shows the BEV percentage of combined BEV and PHEV "
        "sales. Connecting lines follow chronological order."
    )

    st.markdown("**Key observation:**")
    st.write(
        "The trajectory allows us to compare growth in global "
        "EV sales with changes in the composition of electric "
        "vehicle technologies over time."
    )

    st.markdown("**Coverage and limitations:**")
    st.write(
        "Uses historical worldwide electric passenger car "
        "sales data from 2010–2025, including only years "
        "with comparable EV, BEV, and PHEV observations. "
        "The figure illustrates association over time, "
        "not a causal relationship."
    )


    st.divider()

    st.subheader("02 · Rank Dumbbell — EV Market Rankings")

    st.markdown(
        "**Research question:** Do countries leading in "
        "EV sales volume also lead in EV sales share?"
    )

    # Select a historical year
    year = st.selectbox(
        "Historical year",
        options=list(range(2025, 2009, -1)),
        index=0,
        key="dumbbell_year",
    )

    df = load_data()

    fig = build_rank_dumbbell(
        df,
        year=year,
        top_n=12,
    )

    if fig is not None:
        st.plotly_chart(
            fig,
            width="stretch",
            key="rank_dumbbell_chart",
        )
    else:
        st.info(
            "No comparable country data is available "
            "for the selected year."
        )

    st.markdown("**How to read:**")
    st.write(
        "Each country has two markers: one for its "
        "EV sales volume ranking and another for its "
        "EV sales share ranking. The connecting line "
        "shows the difference between these rankings. "
        "Rank 1 represents the highest position."
    )

    st.markdown("**Key observation:**")
    st.write(
        "Countries with high EV sales volumes do not "
        "necessarily have the highest EV sales shares. "
        "The distance between markers highlights "
        "differences between market size and adoption."
    )

    st.markdown("**Coverage and limitations:**")
    st.write(
        "Historical electric passenger car data are used. "
        "Countries are included only when both metrics "
        "are available. Rankings are calculated across "
        "all matched countries, while the chart displays "
        "the top 12 countries from either ranking."
    )

    st.divider()

   
    st.subheader("07 · Parallel Coordinates — EV Adoption by Vehicle Type")

    st.markdown(
        "**Research question:** Did different vehicle types "
        "electrify at the same pace between 2020 and 2025?"
    )

    fig = build_ev_mode_pcp(
        df,
        start_year=2020,
        end_year=2025,
    )

    if fig is not None:
        st.plotly_chart(
            fig,
            width="stretch",
            key="ev_mode_pcp_chart",
        )
    else:
        st.info(
            "Insufficient comparable vehicle-type data "
            "is available for the selected period."
        )

    st.markdown("**How to read:**")
    st.write(
        "Each colored line represents a vehicle type. "
        "The vertical axes show EV sales shares for each year "
        "from 2020 to 2025. Follow a line across the axes "
        "to observe changes in its electrification rate."
    )

    st.markdown("**Interaction:**")
    st.write(
        "Try dragging along a vertical axis to select a "
        "percentage range and highlight matching vehicle types. "
        "Hover over the chart to explore its values."
    )

    st.markdown("**Key observation:**")
    st.write(
        "The chart allows us to compare the pace of "
        "electrification across different vehicle types. "
        "Changes in EV sales share are measured in "
        "percentage points, not percentage growth."
    )

    st.markdown("**Coverage and limitations:**")
    st.write(
        "The chart uses historical worldwide EV sales-share "
        "data for 2020–2025. Only vehicle types with complete "
        "observations across the period are included. "
        "The visualization describes new vehicle sales "
        "rather than the entire vehicle fleet."
    )


    st.write(
        "01 · Connected Scatterplot"
    )

    st.write(
        "02 · Rank Dumbbell"
    )

    st.write(
        "07 · Parallel Coordinates"
    )


with tabs[1]:
    st.subheader("Charging Infrastructure")

    st.subheader("03 · Scatterplot Matrix — EV Stock and Charging")

    st.markdown(
        "**Research question:** Are larger electric car fleets "
        "associated with more public charging points?"
    )

    df = load_data()
    year = 2025

    prepared = prepare_charging_splom_data(df, year=year)

    fig = build_charging_splom(df, year=year)

    if fig is not None:
        st.plotly_chart(
            fig,
            width="stretch",
            key="charging_splom_chart",
        )

        st.caption(
            f"Year: {year} | "
            f"Countries with complete observations: {len(prepared)}"
        )
    else:
        st.info(
            "No comparable charging infrastructure data "
            "is available for the selected year."
        )

    st.markdown("**How to read:**")
    st.write(
        "Each point represents a country. The matrix compares "
        "electric car stock, public charging points, "
        "electric cars per public charging point, "
        "and EV sales share. Stock and charging-point "
        "counts are displayed on logarithmic scales."
    )

    st.markdown("**Interaction:**")
    st.write(
        "Hover over points to inspect country values. "
        "Use box or lasso selection to explore "
        "groups of countries across the matrix."
    )

    st.markdown("**Key observation:**")
    st.write(
        "The matrix helps investigate whether countries "
        "with larger electric car fleets also have "
        "more public charging infrastructure. "
        "An observed relationship does not establish causation."
    )

    st.markdown("**Coverage and limitations:**")
    st.write(
        "Uses 2025 historical country-level observations. "
        "Only countries with the required EV stock, "
        "sales-share, and public charging categories "
        "are included. Missing charging records "
        "are not treated as zero."
    )




with tabs[2]:
    st.subheader("Vehicle Prices")

    st.subheader("04 · Violin Plot — BEV vs ICEV Price Gaps")

    st.markdown(
        "**Research question:** How does the BEV–ICEV "
        "median price gap vary across vehicle segments "
        "and countries?"
    )

    # Select vehicle segments
    selected_segments = st.multiselect(
        "Vehicle segments",
        options=list(PRICE_SEGMENTS),
        default=list(PRICE_SEGMENTS),
        key="violin_segments",
    )

    df = load_data()

    prepared = prepare_price_violin_data(
        df,
        segments=selected_segments,
        year=2025,
    )

    fig = build_price_violin(
        df,
        segments=selected_segments,
        year=2025,
    )

    if fig is not None:
        st.plotly_chart(
            fig,
            width="stretch",
            key="price_violin_chart",
        )

        st.caption(
            f"Year: 2025 | "
            f"Country–segment observations: {len(prepared)} | "
            f"Countries: {prepared['region_country'].nunique()}"
        )
    else:
        st.info(
            "No comparable BEV and ICEV median-price "
            "observations are available for the selected segments."
        )

    st.markdown("**How to read:**")
    st.write(
        "Each violin summarizes the distribution of country-level "
        "BEV–ICEV median price gaps for one vehicle segment. "
        "Individual points represent country–segment observations. "
        "Wider sections indicate a higher concentration of observations."
    )

    st.markdown("**Interaction:**")
    st.write(
        "Select one or more vehicle segments to update the chart. "
        "Hover over points to inspect country-level price gaps. "
        "Use Plotly zoom to examine the distribution."
    )

    st.markdown("**Key observation:**")
    st.write(
        "Compare the shape and spread of the distributions "
        "to identify how price gaps differ across vehicle segments. "
        "Positive values mean BEVs have a higher median price "
        "than comparable ICEVs; negative values mean BEVs "
        "have a lower median price."
    )

    st.markdown("**Coverage and limitations:**")
    st.write(
        "Uses 2025 historical country-level median prices "
        "expressed in constant 2025 USD. "
        "Only country–segment pairs with valid prices for "
        "both BEVs and ICEVs are included. "
        "These are distributions of country-level percentage "
        "gaps, not distributions of individual vehicle prices."
    )




with tabs[3]:
    st.subheader("Energy & Environmental Impact")

    
    st.subheader("05 · Treemap — Global EV Energy Impacts")

    st.markdown(
        "**Research question:** Which vehicle types contribute "
        "most to global EV-related energy demand, battery "
        "deployment, and oil displacement?"
    )

    # Select one energy metric
    selected_metric = st.selectbox(
        "Energy impact metric",
        options=list(METRICS.keys()),
        format_func=lambda metric: METRICS[metric][0],
        key="treemap_metric",
    )

    fig = build_energy_treemap(
        df=load_data(),
        metric=selected_metric,
        year=2025,
    )

    if fig is not None:
        st.plotly_chart(
            fig,
            width="stretch",
            key="energy_treemap_chart",
        )

        st.caption(
            f"Year: 2025 | Scope: World | "
            f"Metric: {METRICS[selected_metric][0]} | "
            f"Unit: {METRICS[selected_metric][1]}"
        )
    else:
        st.info(
            "No complete energy impact data is available "
            "for the selected metric."
        )

    st.markdown("**How to read:**")
    st.write(
        "Each rectangle represents a vehicle type. "
        "Its area is proportional to that vehicle type's "
        "contribution to the selected global energy metric. "
        "Click a rectangle to explore the hierarchy."
    )

    st.markdown("**Interaction:**")
    st.write(
        "Select a metric to update the Treemap. "
        "Hover over rectangles to inspect their values "
        "and percentage contributions. "
        "Click a vehicle type to zoom into it."
    )

    st.markdown("**Key observation:**")
    st.write(
        "Compare rectangle sizes to identify which vehicle "
        "types contribute the largest shares of the selected "
        "global energy metric."
    )

    st.markdown("**Coverage and limitations:**")
    st.write(
        "Uses 2025 historical worldwide EV data for five "
        "vehicle types: cars, buses, trucks, vans, and "
        "two- and three-wheelers. "
        "Only one metric and its corresponding unit are "
        "displayed at a time. The chart does not combine "
        "oil displacement, battery deployment, and "
        "electricity demand into a single total."
    )

    st.divider()

    st.subheader("06 · Sankey — Energy Demand Transition")

    st.markdown(
        "**Research question:** How did countries transition "
        "between electricity-demand-per-EV levels "
        "from 2020 to 2025?"
    )

    df = load_data()

    fig = build_energy_transition_sankey(
        df,
        start_year=2020,
        end_year=2025,
    )

    if fig is not None:
        st.plotly_chart(
            fig,
            width="stretch",
            key="energy_sankey_chart",
        )
    else:
        st.info(
            "No comparable country data is available "
            "for the selected years."
        )

    st.markdown("**How to read:**")
    st.write(
        "Each flow connects a country's electricity-demand-"
        "per-EV category in 2020 to its category in 2025. "
        "The thickness of each flow represents the number "
        "of countries following that transition."
    )

    st.markdown("**Key observation:**")
    st.write(
        "Countries can remain within the same category "
        "or move between Low, Medium, and High levels. "
        "These relative categories help summarize "
        "changes in electricity demand per EV."
    )

    st.markdown("**Coverage and limitations:**")
    st.write(
        "Only countries with valid electric passenger car "
        "stock and electricity-demand data in both years "
        "are included. Categories are defined using "
        "quantile thresholds, not official IEA categories. "
        "The ratio is an approximation based on year-end "
        "EV stock, not measured electricity consumption "
        "per individual vehicle."
    )




with tabs[4]:
    st.subheader("Future Outlook 2035")

    st.subheader(
        "08 · Diverging Heatmap — 2035 Scenario Comparison"
    )

    st.markdown(
        "**Research question:** Where are the largest relative "
        "differences between the STEPS and CPS scenarios "
        "across EV indicators and geographies in 2035?"
    )

    # Load the 2035 scenario comparison dataset
    scenario_df = load_scenario_data()

    fig = build_scenario_heatmap(scenario_df)

    if fig is not None:
        st.plotly_chart(
            fig,
            width="stretch",
            key="scenario_heatmap_chart",
        )

        st.caption(
            "Year: 2035 | Scenarios: STEPS vs CPS | "
            "Measure: Relative difference (%)"
        )
    else:
        st.info(
            "No comparable 2035 CPS and STEPS scenario "
            "observations are available."
        )

    st.markdown("**How to read:**")
    st.write(
        "Each cell compares the STEPS and CPS projections "
        "for one EV indicator and geography. "
        "The diverging color scale is centered at zero: "
        "positive values indicate higher STEPS projections, "
        "while negative values indicate lower projections."
    )

    st.markdown("**Interaction:**")
    st.write(
        "Hover over cells to inspect the scenario values "
        "and relative percentage differences."
    )

    st.markdown("**Key observation:**")
    st.write(
        "The heatmap highlights where the STEPS and CPS "
        "projections differ most strongly relative to "
        "the CPS baseline. Compare color intensity "
        "across indicators and geographies to identify "
        "areas of larger scenario divergence."
    )

    st.markdown("**Coverage and limitations:**")
    st.write(
        "The visualization uses paired CPS and STEPS "
        "projections for 2035, not historical observations. "
        "Relative differences are calculated as "
        "100 × (STEPS − CPS) / |CPS|. "
        "Missing values and zero CPS baselines produce "
        "undefined differences rather than zero. "
        "Countries, regions, and World are compared "
        "individually and are not summed."
    )
