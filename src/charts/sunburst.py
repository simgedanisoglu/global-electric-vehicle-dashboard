import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


PARAMETER_GROUPS = {
    "EV Market": [
        "EV sales",
        "EV stock",
        "EV sales share",
        "EV stock share",
    ],
    "Charging": [
        "EV charging points",
        "Electric LDVs per charging point",
        "Average capacity per EV",
        "Average capacity per EVSE",
    ],
    "Energy & Impact": [
        "Battery deployment",
        "Electricity demand",
        "Oil displacement Mlge",
        "Oil displacement, Mbd",
    ],
    "Price": [
        "price_mean_2025USD",
        "price_p0_2025USD",
        "price_p25_2025USD",
        "price_p50_2025USD",
        "price_p75_2025USD",
        "price_p95_2025USD",
        "price_p100_2025USD",
    ],
}


def prepare_sunburst_data(
    df: pd.DataFrame,
    parameter_group: str
) -> pd.DataFrame:

    # Check the selected group
    if parameter_group not in PARAMETER_GROUPS:
        raise ValueError("Invalid parameter group")

    # Select historical records
    filtered = df[
        (df["category"] == "Historical")
        & (df["parameter"].isin(
            PARAMETER_GROUPS[parameter_group]
        ))
    ]

    # Keep unique combinations
    result = filtered[
        ["parameter", "mode", "powertrain"]
    ].drop_duplicates()

    return result


def build_sunburst(
    df: pd.DataFrame,
    parameter_group: str = "EV Market"
) -> go.Figure | None:

    # Prepare unique combinations
    data = prepare_sunburst_data(df, parameter_group)

    if data.empty:
        return None

    # Each combination has equal weight
    data = data.copy()
    data["count"] = 1

    # Create the hierarchical chart
    fig = px.sunburst(
        data,
        path=["parameter", "mode", "powertrain"],
        values="count",
        color="parameter",
        title=f"Dataset Structure — {parameter_group}",
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{label}</b>"
            "<br>Unique combinations: %{value}"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        template="plotly_white",
        height=650,
        margin=dict(t=65, l=20, r=20, b=20),
    )

    return fig

