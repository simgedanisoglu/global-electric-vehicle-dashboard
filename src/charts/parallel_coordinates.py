"""World EV sales shares by vehicle type in parallel coordinates."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go


PCP_MODES = ("Cars", "Buses", "Trucks", "Vans", "2 and 3 wheelers")

MODE_COLORS = {
    "Cars": "#2563EB",
    "Buses": "#10B981",
    "Trucks": "#EF4444",
    "Vans": "#F59E0B",
    "2 and 3 wheelers": "#8B5CF6",
}


def build_ev_mode_pcp(
    df: pd.DataFrame,
    start_year: int = 2020,
    end_year: int = 2025,
) -> go.Figure | None:
    """Build the World EV-sales-share PCP for complete vehicle histories."""
    required = {
        "category", "region_country", "parameter", "mode",
        "powertrain", "year", "unit", "value",
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required PCP columns: {', '.join(sorted(missing))}")
    if (
        isinstance(start_year, bool)
        or isinstance(end_year, bool)
        or not isinstance(start_year, (int, np.integer))
        or not isinstance(end_year, (int, np.integer))
        or start_year >= end_year
    ):
        raise ValueError("start_year must be an integer earlier than end_year.")

    data = df.loc[
        df["category"].eq("Historical")
        & df["region_country"].eq("World")
        & df["parameter"].eq("EV sales share")
        & df["powertrain"].eq("EV")
        & df["mode"].isin(PCP_MODES),
        ["mode", "year", "unit", "value"],
    ].copy()
    if data.empty:
        return None

    data["year"] = pd.to_numeric(data["year"], errors="raise")
    if not np.isfinite(data["year"]).all() or data["year"].mod(1).ne(0).any():
        raise ValueError("PCP years must be finite integers.")
    data["year"] = data["year"].astype(int)
    data = data.loc[data["year"].between(start_year, end_year)].copy()
    if data.empty:
        return None
    if not data["unit"].eq("percent").all():
        raise ValueError("PCP values must use the 'percent' unit.")
    if data.duplicated(["mode", "year"]).any():
        raise ValueError("Duplicate PCP mode-year records found.")

    data["value"] = pd.to_numeric(data["value"], errors="raise")
    observed = data["value"].dropna().to_numpy(dtype=float)
    if not np.isfinite(observed).all():
        raise ValueError("PCP values must be finite when present.")
    if ((observed < 0) | (observed > 100)).any():
        raise ValueError("PCP percentage values must be between 0 and 100.")

    years = list(range(start_year, end_year + 1))
    wide = data.pivot(index="mode", columns="year", values="value").reindex(
        index=PCP_MODES,
        columns=years,
    )
    complete = wide.dropna()
    if len(complete) < 2:
        return None

    modes = complete.index.tolist()
    excluded_modes = [mode for mode in PCP_MODES if mode not in modes]
    change_pp = complete[end_year] - complete[start_year]
    annual_change = change_pp / (end_year - start_year)

    colorscale = []
    for index, mode in enumerate(modes):
        lower = index / len(modes)
        upper = (index + 1) / len(modes)
        colorscale.extend([[lower, MODE_COLORS[mode]], [upper, MODE_COLORS[mode]]])

    fig = go.Figure(
        go.Parcoords(
            dimensions=[
                dict(
                    label=str(year),
                    values=complete[year].tolist(),
                    range=[0, 100],
                )
                for year in years
            ],
            line=dict(
                color=list(range(len(modes))),
                colorscale=colorscale,
                cmin=-0.5,
                cmax=len(modes) - 0.5,
                showscale=True,
                colorbar=dict(
                    title="Vehicle type",
                    tickvals=list(range(len(modes))),
                    ticktext=modes,
                ),
            ),
        )
    )

    annotations = []
    if excluded_modes:
        annotations.append(dict(
            text="Excluded for incomplete coverage: " + ", ".join(excluded_modes),
            x=0, y=-0.14, xref="paper", yref="paper",
            showarrow=False, xanchor="left",
        ))

    fig.update_layout(
        title=f"07 · Global EV sales share by vehicle type, {start_year}–{end_year}",
        template="plotly_white",
        height=620,
        font=dict(family="Arial", size=12),
        margin=dict(l=70, r=170, t=85, b=100 if excluded_modes else 70),
        annotations=annotations,
        meta=dict(
            years=years,
            complete_modes=modes,
            excluded_modes=excluded_modes,
            change_pp={mode: float(change_pp[mode]) for mode in modes},
            average_pp_per_year={mode: float(annual_change[mode]) for mode in modes},
            brushing_status="manual browser verification required",
        ),
    )
    return fig
