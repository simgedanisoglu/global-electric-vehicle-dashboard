
import pandas as pd
import plotly.graph_objects as go


LEVELS = ["Low", "Medium", "High"]

COLORS = {
    "Low": "#16A085",
    "Medium": "#E5A33D",
    "High": "#DC6A56",
}


def prepare_energy_transition_data(
    df: pd.DataFrame,
    start_year: int = 2020,
    end_year: int = 2025,
):
    # Select historical country records
    data = df[
        (df["category"] == "Historical")
        & (df["Aggregate group"].isin(
            ["Other", "Projection_country"]
        ))
        & (df["mode"] == "Cars")
        & (df["powertrain"] == "EV")
        & (df["year"].isin([start_year, end_year]))
        & (df["parameter"].isin([
            "Electricity demand", "EV stock"
        ]))
    ].copy()

    if data.empty:
        return pd.DataFrame(), None

    # Check measurement units
    expected_units = {
        "Electricity demand": "GWh",
        "EV stock": "vehicles",
    }

    for parameter, expected in expected_units.items():
        actual = data.loc[
            data["parameter"] == parameter, "unit"
        ].dropna().astype(str).str.strip().str.lower()

        if not actual.eq(expected.lower()).all():
            raise ValueError(
                f"Unexpected unit for {parameter}"
            )

    # Do not combine duplicate measurements
    keys = ["region_country", "year", "parameter"]

    if data.duplicated(keys).any():
        raise ValueError(
            "Duplicate country-year-parameter records"
        )

    # Match electricity demand with EV stock
    pivot = data.pivot(
        index=["region_country", "year"],
        columns="parameter",
        values="value",
    ).reset_index()

    pivot = pivot.dropna(
        subset=["Electricity demand", "EV stock"]
    )

    # Keep valid stock and demand values
    pivot = pivot[
        (pivot["EV stock"] > 0)
        & (pivot["Electricity demand"] >= 0)
    ].copy()

    # Calculate approximate annual energy demand
    pivot["kWh_per_yearend_EV"] = (
        pivot["Electricity demand"]
        * 1_000_000
        / pivot["EV stock"]
    )

    # Keep countries with both years
    paired = pivot.pivot(
        index="region_country",
        columns="year",
        values="kWh_per_yearend_EV",
    ).dropna(subset=[start_year, end_year])

    if paired.empty:
        return pd.DataFrame(), None

    # Use the same thresholds for both years
    combined = pd.concat([
        paired[start_year],
        paired[end_year],
    ])

    q1 = combined.quantile(1 / 3)
    q2 = combined.quantile(2 / 3)

    thresholds = (q1, q2)

    def classify(value):
        if value <= q1:
            return "Low"
        if value <= q2:
            return "Medium"
        return "High"

    paired = paired.copy()
    paired["start_level"] = paired[start_year].apply(
        classify
    )
    paired["end_level"] = paired[end_year].apply(
        classify
    )

    return paired.reset_index(), thresholds


def build_energy_transition_sankey(
    df: pd.DataFrame,
    start_year: int = 2020,
    end_year: int = 2025,
) -> go.Figure | None:

    paired, thresholds = prepare_energy_transition_data(
        df, start_year, end_year
    )

    if paired.empty:
        return None

    # Create transition groups
    transitions = (
        paired.groupby(
            ["start_level", "end_level"],
            observed=True,
        )["region_country"]
        .agg(list)
        .reset_index(name="countries")
    )

    transitions["count"] = transitions[
        "countries"
    ].apply(len)

    # Build six nodes: three for each year
    labels = (
        [f"{start_year} — {x}" for x in LEVELS]
        + [f"{end_year} — {x}" for x in LEVELS]
    )

    node_colors = [
        COLORS[level] for level in LEVELS
    ] * 2

    sources = []
    targets = []
    values = []
    link_colors = []
    customdata = []

    for _, row in transitions.iterrows():
        start_level = row["start_level"]
        end_level = row["end_level"]

        sources.append(LEVELS.index(start_level))
        targets.append(3 + LEVELS.index(end_level))
        values.append(row["count"])

        link_colors.append(
            COLORS[start_level] + "70"
        )

        names = ", ".join(sorted(row["countries"]))

        customdata.append(
            f"{start_level} → {end_level}"
            f"<br>Countries: {names}"
        )

    fig = go.Figure(
        go.Sankey(
            arrangement="snap",
            node=dict(
                label=labels,
                color=node_colors,
                pad=22,
                thickness=22,
                line=dict(color="white", width=1),
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color=link_colors,
                customdata=customdata,
                hovertemplate=(
                    "%{customdata}"
                    "<br>Country count: %{value}"
                    "<extra></extra>"
                ),
            ),
        )
    )

    q1, q2 = thresholds

    fig.update_layout(
        title=(
            f"EV Energy Demand Level Transitions "
            f"({start_year}–{end_year})"
        ),
        template="plotly_white",
        height=550,
        font=dict(size=13),
        margin=dict(t=75, l=30, r=30, b=55),
        annotations=[
            dict(
                x=0.5, y=-0.12,
                xref="paper", yref="paper",
                showarrow=False,
                text=(
                    f"Matched countries: {len(paired)}"
                    f" | Low ≤ {q1:.1f}"
                    f" | Medium ≤ {q2:.1f} kWh"
                ),
            )
        ],
    )

    return fig
