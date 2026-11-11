"""Chronological World EV sales and BEV/(BEV+PHEV) market composition."""

import logging

import numpy as np
import pandas as pd
import plotly.graph_objects as go


logger = logging.getLogger(__name__)
TECHNOLOGIES = ("EV", "BEV", "PHEV")


def _prepare_market_data(df: pd.DataFrame) -> pd.DataFrame:
    """Validate the selected records and retain only valid common years."""
    required = {
        "region_country", "category", "parameter", "mode", "powertrain",
        "year", "unit", "value",
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
    data = df.loc[
        df["category"].eq("Historical")
        & df["region_country"].eq("World")
        & df["parameter"].eq("EV sales")
        & df["mode"].eq("Cars")
        & df["powertrain"].isin(TECHNOLOGIES),
        ["year", "powertrain", "unit", "value"],
    ].copy()
    try:
        data["year"] = pd.to_numeric(data["year"], errors="raise")
    except (ValueError, TypeError) as exc:
        raise ValueError("Market years must be numeric integers") from exc
    years = data["year"].to_numpy(dtype=float)
    if not np.isfinite(years).all() or (years != np.floor(years)).any():
        raise ValueError("Market years must be finite integers")
    data = data.loc[data["year"].between(2010, 2025)].copy()
    data["year"] = data["year"].astype(int)
    if data.duplicated(["year", "powertrain"]).any():
        raise ValueError("Duplicate World/Cars/EV sales year × powertrain records")
    if not data["unit"].eq("Vehicles").all():
        raise ValueError("World EV sales must use the Vehicles unit")
    try:
        data["value"] = pd.to_numeric(data["value"], errors="raise")
    except (ValueError, TypeError) as exc:
        raise ValueError("Market sales values must be numeric") from exc
    observed = data["value"].dropna().to_numpy(dtype=float)
    if not np.isfinite(observed).all() or (observed < 0).any():
        raise ValueError("Market sales values must be finite and nonnegative")

    wide = data.pivot(index="year", columns="powertrain", values="value")
    wide = wide.reindex(columns=list(TECHNOLOGIES)).sort_index()
    wide = wide.dropna(subset=list(TECHNOLOGIES)).copy()
    denominator = wide["BEV"] + wide["PHEV"]
    if not np.isfinite(denominator.to_numpy(dtype=float)).all():
        raise ValueError("BEV + PHEV sales must be finite")
    wide = wide.loc[wide["EV"].gt(0) & denominator.gt(0)].copy()
    denominator = denominator.loc[wide.index]
    wide["BEV_share_in_EV"] = 100 * (wide["BEV"] / denominator)
    wide["PHEV_share_in_EV"] = 100 * (wide["PHEV"] / denominator)
    shares = wide[["BEV_share_in_EV", "PHEV_share_in_EV"]]
    if ((shares < 0) | (shares > 100)).any().any():
        raise ValueError("Technology shares must be between 0 and 100 percent")
    gap = wide["EV"] - denominator
    if gap.ne(0).any():
        logger.info(
            "Published EV differs from BEV + PHEV; original totals retained. "
            "Year-to-difference (Vehicles): %s", gap.loc[gap.ne(0)].to_dict(),
        )
    return wide


def build_market_connected_scatter(df: pd.DataFrame) -> go.Figure | None:
    """Return the notebook's connected XY Figure without modifying ``df``.

    Only Historical World Cars EV sales in 2010–2025 are used. Missing
    technologies/values and nonpositive EV or BEV+PHEV totals exclude that
    year; no observations are interpolated or filled with zero. Return None
    when no valid common year remains. Invalid schema, duplicate keys,
    units, negative or nonfinite sales raise ValueError. Published EV totals
    remain independent of the BEV+PHEV denominator; differences are logged.
    The caller owns data loading, rendering, and empty-data messages.
    """
    market = _prepare_market_data(df)
    if market.empty:
        return None

    fig = go.Figure(go.Scatter(
        x=market["EV"], y=market["BEV_share_in_EV"],
        mode="lines+markers+text", text=market.index.astype(str),
        textposition="top center", textfont=dict(size=10),
        line=dict(color="#64748b", width=2.5),
        marker=dict(
            size=11, color=market.index, colorscale="Viridis",
            colorbar=dict(title="Year"), showscale=True,
        ),
        customdata=np.column_stack([
            market["PHEV_share_in_EV"].to_numpy(),
            market["BEV"].to_numpy(), market["PHEV"].to_numpy(),
        ]),
        hovertemplate=(
            "Year: %{text}<br>EV sales: %{x:,.0f} vehicles"
            "<br>BEV share: %{y:.1f}%<br>PHEV share: %{customdata[0]:.1f}%"
            "<br>BEV sales: %{customdata[1]:,.0f}"
            "<br>PHEV sales: %{customdata[2]:,.0f}<extra></extra>"
        ),
        showlegend=False,
    ))
    fig.update_layout(
        title="01 · World EV sales volume and BEV share over time",
        xaxis_title="Annual electric car sales (EV, vehicles)",
        yaxis_title="BEV share of BEV+PHEV sales (%)",
        annotations=[dict(
            x=market["EV"].iloc[-1], y=market["BEV_share_in_EV"].iloc[-1],
            text="Latest year", ax=40, ay=-35, showarrow=True,
        )],
        template="plotly_white", height=610,
        font=dict(family="Arial", size=12),
        margin=dict(l=50, r=40, t=85, b=60),
        hovermode="closest", legend=dict(orientation="h", y=-0.12),
        meta=dict(
            geography="World", vehicle_mode="Cars", category="Historical",
            years=market.index.tolist(), common_years=len(market),
        ),
    )
    return fig
