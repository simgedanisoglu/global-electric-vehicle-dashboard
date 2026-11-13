"""Absolute 2025 prediction errors of the next-year EV sales share models."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


MODELS = ("Persistence Baseline", "Linear Regression", "Random Forest", "XGBoost")
MODEL_COLORS = {
    "Persistence Baseline": "#94A3B8",
    "Linear Regression": "#3B82F6",
    "Random Forest": "#10B981",
    "XGBoost": "#F59E0B",
}
ACTUAL_COLUMN = "2025 Gerçek"  # column name as stored in the source CSV


def prepare_regression_errors(
    results: pd.DataFrame,
    models: list[str] | None = None,
    countries: list[str] | None = None,
) -> pd.DataFrame:
    """Long table: region_country, model, actual, prediction, abs_error.
    The error is recomputed as |actual - prediction| in percentage points."""
    required = ["region_country", ACTUAL_COLUMN, *MODELS]
    missing = [c for c in required if c not in results.columns]
    if missing:
        raise ValueError(f"Missing regression columns: {missing}")
    selected = [m for m in MODELS if models is None or m in models]
    frames = []
    for model in selected:
        part = results[["region_country", ACTUAL_COLUMN, model]].dropna()
        part = part.rename(columns={ACTUAL_COLUMN: "actual", model: "prediction"})
        part["model"] = model
        frames.append(part)
    if not frames:
        return pd.DataFrame(
            columns=["region_country", "model", "actual", "prediction", "abs_error"])
    data = pd.concat(frames, ignore_index=True)
    if countries:
        data = data.loc[data["region_country"].isin(countries)]
    data["abs_error"] = (data["actual"] - data["prediction"]).abs()
    return data[["region_country", "model", "actual", "prediction", "abs_error"]] \
        .reset_index(drop=True)


def summarize_errors(data: pd.DataFrame) -> pd.DataFrame:
    """Per-model country count, MAE, median and maximum error of the filtered rows."""
    summary = (
        data.groupby("model")["abs_error"]
        .agg(Countries="count", MAE="mean", Median="median", Maximum="max")
        .reindex([m for m in MODELS if m in set(data["model"])])
    )
    summary["Countries"] = summary["Countries"].astype(int)
    summary = summary.rename(columns={
        "MAE": "MAE (pp)", "Median": "Median error (pp)", "Maximum": "Max error (pp)"})
    summary.index.name = "Model"
    return summary.round(3)


def build_error_boxplot(data: pd.DataFrame) -> go.Figure | None:
    """Box plot with the individual country errors beside each box."""
    if data is None or data.empty:
        return None
    fig = go.Figure()
    for model in [m for m in MODELS if m in set(data["model"])]:
        part = data.loc[data["model"].eq(model)]
        fig.add_trace(go.Box(
            x=part["model"],
            y=part["abs_error"],
            name=model,
            marker_color=MODEL_COLORS[model],
            boxpoints="all",
            jitter=0.5,
            pointpos=-1.6,
            marker=dict(size=7, opacity=0.8, color=MODEL_COLORS[model]),
            customdata=part[["region_country", "actual", "prediction"]],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>Model: " + model +
                "<br>Actual 2025: %{customdata[1]:.2f}%"
                "<br>Prediction: %{customdata[2]:.2f}%"
                "<br>Absolute error: %{y:.2f} pp<extra></extra>"
            ),
        ))
    fig.update_xaxes(
        title="Regression Model", categoryorder="array",
        categoryarray=[m for m in MODELS if m in set(data["model"])])
    fig.update_yaxes(title="Absolute Prediction Error (percentage points)", rangemode="tozero")
    fig.update_layout(
        title="Regression Model Error Distribution (2025)",
        template="plotly_white", height=520, showlegend=False,
    )
    return fig
