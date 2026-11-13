"""Paired 2035 scenario differences, normalized to each indicator's CPS value."""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


SCENARIO_METRICS = (
    ("EV sales", "Cars", "EV", "EV sales · Cars", "Vehicles"),
    ("EV sales share", "Cars", "EV", "EV sales share · Cars", "percent"),
    ("EV stock", "Cars", "EV", "EV stock · Cars", "Vehicles"),
    ("EV charging points", "EVSE", "Publicly available slow", "Public chargers · Slow", "charging points"),
    ("EV charging points", "EVSE", "Publicly available fast", "Public chargers · Fast", "charging points"),
    ("EV charging points", "EVSE", "Publicly available ultra-fast", "Public chargers · Ultra-fast", "charging points"),
    ("Electricity demand", "Cars", "EV", "Electricity demand · Cars", "GWh"),
    ("Battery deployment", "Cars", "EV", "Battery deployment · Cars", "GWh"),
    ("Oil displacement Mlge", "Cars", "EV", "Oil displacement · Cars", "Million litres gasoline equivalent"),
)
GEOGRAPHIES = (
    "China", "Europe", "India", "Japan", "Korea", "Latin America",
    "Southeast Asia", "USA", "World",
)


def _signed_log(values):
    """Map percentages to color coordinates only; preserve zero and NaN."""
    values = np.asarray(values, dtype=float)
    return np.sign(values) * np.log1p(np.abs(values) / 5.0)


def _prepare_scenario_data(sc: pd.DataFrame) -> pd.DataFrame:
    """Validate selected pairs without aggregating or changing the input."""
    required = {
        "region_country", "parameter", "mode", "powertrain", "year", "unit",
        "Projection-CPS", "Projection-STEPS",
    }
    missing = required.difference(sc.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
    segments = []
    for parameter, mode, powertrain, indicator, unit in SCENARIO_METRICS:
        rows = sc.loc[
            sc["parameter"].eq(parameter) & sc["mode"].eq(mode)
            & sc["powertrain"].eq(powertrain)
            & sc["region_country"].isin(GEOGRAPHIES),
            list(sorted(required)),
        ].copy()
        try:
            rows["year"] = pd.to_numeric(rows["year"], errors="raise")
        except (TypeError, ValueError) as exc:
            raise ValueError("Scenario years must be numeric integers") from exc
        years = rows["year"].to_numpy(dtype=float)
        if not np.isfinite(years).all() or (years != np.floor(years)).any():
            raise ValueError("Scenario years must be finite integers")
        rows = rows.loc[rows["year"].eq(2035)].copy()
        if rows["region_country"].duplicated().any():
            raise ValueError(f"Duplicate geography/indicator/year records: {indicator}")
        if not rows["unit"].eq(unit).all():
            raise ValueError(f"Expected unit {unit!r} for {indicator}")
        for column in ("Projection-CPS", "Projection-STEPS"):
            try:
                rows[column] = pd.to_numeric(rows[column], errors="raise")
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{column} values must be numeric") from exc
            if not np.isfinite(rows[column].dropna().to_numpy(dtype=float)).all():
                raise ValueError(f"{column} values must be finite or missing")
        rows["Indicator"] = indicator
        rows["Diff_percent"] = np.nan
        valid = (rows["Projection-CPS"].notna()
                 & rows["Projection-STEPS"].notna()
                 & rows["Projection-CPS"].ne(0))
        rows.loc[valid, "Diff_percent"] = (
            100 * (rows.loc[valid, "Projection-STEPS"] - rows.loc[valid, "Projection-CPS"])
            / rows.loc[valid, "Projection-CPS"].abs()
        )
        if not np.isfinite(rows.loc[valid, "Diff_percent"].to_numpy(dtype=float)).all():
            raise ValueError("Relative scenario differences must be finite")
        segments.append(rows)
    return pd.concat(segments, ignore_index=True)


def build_scenario_heatmap(sc: pd.DataFrame) -> go.Figure | None:
    """Build the reference multi-metric 2035 CPS/STEPS heatmap.

    Return None for no selected records or no computable differences. Missing
    pairs and CPS=0 remain NaN; equal nonzero scenarios are real zero. Invalid
    schema, units, duplicate keys or nonfinite values raise ValueError.
    Rows retain all nine indicators, even if one has no valid pairs. Columns
    retain selected geographies with records, including entirely missing
    scenario values. Country, region and World profiles are never summed.
    Only color coordinates use signed-log scaling (transition parameter 5%).
    Hover and colorbar labels retain original relative percentages.
    The caller owns loading, rendering and empty-data messages.
    """
    selected = _prepare_scenario_data(sc)
    if selected.empty:
        return None
    indicators = [metric[3] for metric in SCENARIO_METRICS]
    geographies = sorted(selected["region_country"].unique())
    mat = selected.pivot(
        index="Indicator", columns="region_country", values="Diff_percent",
    ).reindex(index=indicators, columns=geographies)
    values = mat.to_numpy(dtype=float)
    finite = np.isfinite(values)
    if not finite.any():
        return None
    extent = max(5.0, float(np.abs(values[finite]).max()))
    color_extent = float(_signed_log(extent))
    # Keep a compact, symmetric legend, including nonstandard data endpoints.
    ticks = sorted({0.0, -extent, extent, *(
        sign * value for value in (5, 20, 100)
        if value < extent for sign in (-1, 1)
    )})

    # Keep raw scenarios, undefined-cell reasons and untransformed percentages.
    records = selected.set_index(["Indicator", "region_country"])
    customdata = np.empty((*values.shape, 8), dtype=object)
    for i, (parameter, mode, powertrain, indicator, unit) in enumerate(SCENARIO_METRICS):
        for j, geography in enumerate(geographies):
            key = (indicator, geography)
            cps = steps = "Missing"
            status = "No matching scenario record"
            if key in records.index:
                row = records.loc[key]
                cps_value, steps_value = row["Projection-CPS"], row["Projection-STEPS"]
                cps = "Missing" if pd.isna(cps_value) else float(cps_value)
                steps = "Missing" if pd.isna(steps_value) else float(steps_value)
                reasons = []
                if pd.isna(cps_value) or pd.isna(steps_value):
                    reasons.append("Missing scenario value")
                if pd.notna(cps_value) and cps_value == 0:
                    reasons.append("CPS=0; relative difference is undefined")
                status = "; ".join(reasons) if reasons else "Valid paired scenarios"
            customdata[i, j] = [parameter, mode, powertrain, unit, cps, steps, status, values[i, j]]

    fig = px.imshow(
        mat.apply(_signed_log), aspect="auto", zmin=-color_extent, zmax=color_extent,
        color_continuous_scale="RdBu_r", color_continuous_midpoint=0,
        labels={"x": "Geography", "y": "Indicator / vehicle", "color": "STEPS − CPS (%)"},
        title="08 · 2035 | STEPS–CPS relative differences by indicator (%)",
    )
    details = (
        "Geography: %{x}<br>Year: 2035<br>Parameter: %{customdata[0]}"
        "<br>Mode: %{customdata[1]}<br>Powertrain: %{customdata[2]}"
        "<br>CPS: %{customdata[4]} %{customdata[3]}"
        "<br>STEPS: %{customdata[5]} %{customdata[3]}"
    )
    fig.update_traces(
        customdata=customdata, hoverongaps=False,
        hovertemplate=details + "<br>Relative difference: %{customdata[7]:.2f}%<extra></extra>",
    )
    fig.update_coloraxes(colorbar=dict(
        title="STEPS − CPS (%)",
        tickmode="array", tickvals=_signed_log(ticks),
        ticktext=[f"{value:g}%" for value in ticks],
    ))
    if (~finite).any():
        # An identical gray overlay enables tooltips on otherwise unhoverable
        # NaN cells without replacing missing differences with a real zero.
        fig.add_trace(go.Heatmap(
            x=geographies, y=indicators, z=np.where(finite, np.nan, 0.0),
            colorscale=[[0, "#e2e8f0"], [1, "#e2e8f0"]],
            showscale=False, showlegend=False, hoverongaps=False,
            customdata=customdata,
            hovertemplate=details + "<br>Relative difference: Not defined"
            "<br>Reason: %{customdata[6]}<extra></extra>",
        ))
    fig.update_xaxes(tickangle=-30)
    fig.update_layout(
        plot_bgcolor="#e2e8f0", template="plotly_white", height=660,
        font=dict(family="Arial", size=12),
        margin=dict(l=50, r=40, t=85, b=60), hovermode="closest",
        legend=dict(orientation="h", y=-0.12),
    )
    return fig
