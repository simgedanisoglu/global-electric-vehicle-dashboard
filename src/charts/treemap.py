"""World energy impacts by vehicle mode; the caller owns metric selection."""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


MODES = ("Cars", "Buses", "Trucks", "Vans", "2 and 3 wheelers")
METRICS = {
    "Oil displacement Mlge": (
        "Petrol ikamesi", "Million litres gasoline equivalent"
    ),
    "Battery deployment": ("Batarya kullanımı", "GWh"),
    "Electricity demand": ("EV elektrik talebi", "GWh"),
}
MODE_COLORS = dict(zip(MODES, px.colors.qualitative.Set2))


def build_energy_treemap(
    df: pd.DataFrame,
    metric: str = "Oil displacement Mlge",
    year: int = 2025,
) -> go.Figure | None:
    """Build a single-metric World → mode treemap without modifying ``df``.

    Return None for absent/incomplete values or an all-zero total. Invalid
    schema, units, duplicate keys, or negative/nonfinite values raise
    ValueError. Zero modes retain their labels in the source trace and are
    listed below the chart because they have no visible area. The year
    argument supports explicit historical reuse; the dashboard uses 2025.
    """
    required = {
        "category", "region_country", "year", "powertrain", "mode",
        "parameter", "unit", "value",
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
    if metric not in METRICS:
        raise ValueError(f"Unsupported energy metric: {metric!r}")
    if isinstance(year, bool) or not isinstance(year, (int, np.integer)):
        raise ValueError("year must be an integer historical year (2010–2025)")
    if not 2010 <= year <= 2025:
        raise ValueError("year must be historical (2010–2025)")

    data = df.loc[
        df["category"].eq("Historical")
        & df["region_country"].eq("World")
        & df["year"].eq(year)
        & df["powertrain"].eq("EV")
        & df["mode"].isin(MODES)
        & df["parameter"].eq(metric),
        ["mode", "value", "unit"],
    ].copy()
    if data.empty:
        return None
    if data["mode"].duplicated().any():
        raise ValueError("Duplicate World/year/parameter/mode/EV records")
    label, unit = METRICS[metric]
    if not data["unit"].eq(unit).all():
        raise ValueError(f"Expected unit {unit!r} for {metric}")
    try:
        data["value"] = pd.to_numeric(data["value"], errors="raise")
    except (ValueError, TypeError) as exc:
        raise ValueError("Energy values must be numeric") from exc
    observed = data["value"].dropna().to_numpy(dtype=float)
    if not np.isfinite(observed).all() or (observed < 0).any():
        raise ValueError("Energy values must be finite and nonnegative")
    if set(data["mode"]) != set(MODES) or data["value"].isna().any():
        return None
    data = data.set_index("mode").reindex(MODES).reset_index()
    total = float(data["value"].sum())
    if not np.isfinite(total):
        raise ValueError("Energy total must be finite")
    if total == 0:
        return None

    data["root"] = "World"
    fig = px.treemap(
        data, path=["root", "mode"], values="value", color="mode",
        color_discrete_map=MODE_COLORS,
    )
    trace = fig.data[0]
    trace.marker.colors = [
        "#FFD700" if node_id == "World" else color
        for node_id, color in zip(trace.ids, trace.marker.colors)
    ]
    # Explicit customdata also defines the root tooltip unambiguously.
    trace.customdata = [
        [name, year, metric, unit, 100 * float(value) / total]
        for name, value in zip(trace.labels, trace.values)
    ]
    trace.textinfo = "label+percent parent"
    trace.hovertemplate = (
        "Araç türü / kapsam: %{customdata[0]}<br>Yıl: %{customdata[1]}"
        "<br>Metrik: %{customdata[2]}<br>Değer: %{value:,.2f} %{customdata[3]}"
        "<br>World beş-mod toplamındaki pay: %{customdata[4]:.2f}%"
        "<extra></extra>"
    )
    fig.update_layout(
        title=f"05 · {year} Dünya | {label} ({unit})",
        template="plotly_white", height=635,
        font=dict(family="Arial", size=12),
        margin=dict(l=40, r=40, t=100, b=65),
    )
    zero_modes = data.loc[data["value"].eq(0), "mode"].tolist()
    if zero_modes:
        fig.add_annotation(
            text="Sıfır değer (alan yok): " + ", ".join(zero_modes),
            x=0, y=-0.07, xref="paper", yref="paper",
            showarrow=False, xanchor="left",
        )
    return fig
