"""K-Means EV adoption clusters shown as a strip plot of EV sales share."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


CLUSTER_ORDER = (
    "Early EV Adoption",
    "Intermediate EV Adoption",
    "Advanced EV Adoption",
)
CLUSTER_COLORS = {
    "Early EV Adoption": "#F59E0B",
    "Intermediate EV Adoption": "#3B82F6",
    "Advanced EV Adoption": "#10B981",
}
REQUIRED_COLUMNS = (
    "region_country", "year", "ev_sales_share", "ev_stock_share", "cluster_name",
)


def prepare_cluster_data(
    df: pd.DataFrame,
    year: int | None = 2025,
    countries: list[str] | None = None,
    clusters: list[str] | None = None,
) -> pd.DataFrame:
    """Filter clustering results; empty country/cluster lists mean no restriction
    for countries and no selection for clusters (callers pass all clusters)."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing clustering columns: {missing}")
    data = df.dropna(subset=list(REQUIRED_COLUMNS)).copy()
    if year is not None:
        data = data.loc[data["year"].eq(year)]
    if countries:
        data = data.loc[data["region_country"].isin(countries)]
    if clusters is not None:
        data = data.loc[data["cluster_name"].isin(clusters)]
    return data.reset_index(drop=True)


def summarize_clusters(data: pd.DataFrame) -> pd.DataFrame:
    """Country count and median EV sales share of the filtered rows, per cluster."""
    summary = (
        data.groupby("cluster_name")
        .agg(Countries=("region_country", "nunique"),
             **{"Median EV sales share (%)": ("ev_sales_share", "median")})
        .round(2)
        .reindex(list(CLUSTER_ORDER))
        .dropna(how="all")
    )
    summary["Countries"] = summary["Countries"].astype(int)
    summary.index.name = "Cluster"
    return summary


def build_cluster_strip(data: pd.DataFrame) -> go.Figure | None:
    """Strip plot: one point per country-year, coloured by K-Means cluster.
    `data` must already be filtered with prepare_cluster_data."""
    if data is None or data.empty:
        return None
    years = sorted(data["year"].unique())
    year_text = str(int(years[0])) if len(years) == 1 else f"{int(years[0])}–{int(years[-1])}"
    fig = px.strip(
        data,
        x="cluster_name",
        y="ev_sales_share",
        color="cluster_name",
        hover_name="region_country",
        hover_data={
            "year": True,
            "ev_sales_share": ":.2f",
            "ev_stock_share": ":.2f",
            "cluster_name": True,
        },
        category_orders={"cluster_name": list(CLUSTER_ORDER)},
        color_discrete_map=CLUSTER_COLORS,
        labels={
            "cluster_name": "EV Adoption Cluster",
            "ev_sales_share": "EV Sales Share (%)",
            "ev_stock_share": "EV Stock Share (%)",
            "year": "Year",
        },
        title=f"EV Adoption Clustering Results ({year_text})",
    )
    fig.update_traces(jitter=0.45, marker=dict(size=11, opacity=0.85))
    fig.update_xaxes(categoryorder="array", categoryarray=list(CLUSTER_ORDER))
    fig.update_yaxes(range=[0, 100])
    fig.update_layout(template="plotly_white", height=520, showlegend=False)
    return fig
