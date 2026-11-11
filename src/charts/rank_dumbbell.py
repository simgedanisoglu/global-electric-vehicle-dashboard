import pandas as pd
import plotly.graph_objects as go



def prepare_rank_dumbbell_data(
    df: pd.DataFrame,
    year: int = 2025,
    top_n: int = 12
) -> pd.DataFrame:

    # Select historical electric car data
    filtered = df[
        (df["category"] == "Historical")
        & (df["year"] == year)
        & (df["mode"] == "Cars")
        & (df["powertrain"] == "EV")
        & (df["Aggregate group"].isin([
            "Other", "Projection_country"
        ]))
        & (df["parameter"].isin([
            "EV sales", "EV sales share"
        ]))
    ].copy()

    # Check unique country and metric records
    keys = ["region_country", "year", "parameter"]

    if filtered.duplicated(keys).any():
        raise ValueError(
            "Duplicate country-year-parameter records"
        )

    # Convert metrics to separate columns
    pivot = filtered.pivot(
        index="region_country",
        columns="parameter",
        values="value"
    ).reset_index()

    # Keep countries with both metrics
    pivot = pivot.dropna(
        subset=["EV sales", "EV sales share"]
    ).copy()

    if pivot.empty:
        return pivot

    # Check valid measurements
    pivot = pivot[
        (pivot["EV sales"] >= 0)
        & (pivot["EV sales share"].between(0, 100))
    ].copy()

    # Rank all matched countries
    pivot["sales_rank"] = pivot["EV sales"].rank(
        ascending=False,
        method="min"
    )

    pivot["share_rank"] = pivot["EV sales share"].rank(
        ascending=False,
        method="min"
    )

    pivot["rank_gap"] = (
        pivot["share_rank"] - pivot["sales_rank"]
    )

    # Show the union of top countries from both metrics
    selected = pivot[
        (pivot["sales_rank"] <= top_n)
        | (pivot["share_rank"] <= top_n)
    ].copy()

    return selected.sort_values(
        "sales_rank",
        ascending=False
    ).reset_index(drop=True)


def build_rank_dumbbell(
    df: pd.DataFrame,
    year: int = 2025,
    top_n: int = 20
) -> go.Figure | None:
    """
    Build dumbbell chart comparing EV sales rank vs EV sales share rank.
    """

    data = prepare_rank_dumbbell_data(df, year, top_n)

    if data.empty:
        return None

    fig = go.Figure()

    # Connecting lines
    for _, row in data.iterrows():
        fig.add_trace(
            go.Scatter(
                x=[row["sales_rank"], row["share_rank"]],
                y=[row["region_country"], row["region_country"]],
                mode="lines",
                line=dict(width=2, color="lightgray"),
                hoverinfo="skip",
                showlegend=False
            )
        )

    # EV sales rank points
    fig.add_trace(
        go.Scatter(
            x=data["sales_rank"],
            y=data["region_country"],
            mode="markers",
            name="EV Sales Rank",
            marker=dict(size=10, symbol="circle"),
            customdata=data[["EV sales", "EV sales share"]],
            hovertemplate=(
                "<b>%{y}</b>"
                "<br>EV Sales Rank: %{x}"
                "<br>EV Sales: %{customdata[0]:,.0f}"
                "<br>EV Sales Share: %{customdata[1]:.2f}"
                "<extra></extra>"
            )
        )
    )

    # EV sales share rank points
    fig.add_trace(
        go.Scatter(
            x=data["share_rank"],
            y=data["region_country"],
            mode="markers",
            name="EV Sales Share Rank",
            marker=dict(size=10, symbol="diamond"),
            customdata=data[["EV sales", "EV sales share"]],
            hovertemplate=(
                "<b>%{y}</b>"
                "<br>EV Sales Share Rank: %{x}"
                "<br>EV Sales: %{customdata[0]:,.0f}"
                "<br>EV Sales Share: %{customdata[1]:.2f}"
                "<extra></extra>"
            )
        )
    )

    fig.update_layout(
        title=f"Rank Comparison: EV Sales vs EV Sales Share ({year})",
        template="plotly_white",
        height=700,
        margin=dict(t=60, l=20, r=20, b=20),
        xaxis=dict(
            title="Rank (1 = highest)",
            autorange="reversed"
        ),
        yaxis=dict(title="Country"),
        legend=dict(orientation="h", y=1.05, x=0)
    )

    return fig