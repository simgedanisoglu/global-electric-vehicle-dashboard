"""Country-level BEV–ICEV median-price gaps across car segments."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go


COUNTRY_GROUPS = ("Other", "Projection_country")
PRICE_SEGMENTS = (
    "City car",
    "Medium car",
    "Large car",
    "Small SUV/Pick-up",
    "Large SUV/Pick-up",
)
SEGMENT_COLORS = {
    "City car": "#2563EB",
    "Medium car": "#14B8A6",
    "Large car": "#F59E0B",
    "Small SUV/Pick-up": "#8B5CF6",
    "Large SUV/Pick-up": "#EF4444",
}


def prepare_price_violin_data(
    df: pd.DataFrame,
    segments: list[str] | None = None,
    year: int = 2025,
) -> pd.DataFrame:
    """Pair country-segment BEV/ICEV medians and calculate percentage gaps."""
    required = {
        "region_country", "category", "parameter", "mode", "powertrain",
        "year", "unit", "value", "Aggregate group",
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required Violin columns: {', '.join(sorted(missing))}")
    if isinstance(year, bool) or not isinstance(year, (int, np.integer)):
        raise ValueError("year must be an integer year.")
    if segments is not None and not isinstance(segments, list):
        raise TypeError("segments must be a list or None.")

    requested = list(PRICE_SEGMENTS) if segments is None else segments
    unknown = sorted(set(requested).difference(PRICE_SEGMENTS))
    if unknown:
        raise ValueError("Unsupported price segments: " + ", ".join(unknown))
    selected = [segment for segment in PRICE_SEGMENTS if segment in requested]
    result_columns = [
        "region_country", "year", "mode",
        "BEV_median", "ICEV_median", "price_gap_pct",
    ]
    if not selected:
        return pd.DataFrame(columns=result_columns)

    data = df.loc[
        df["category"].eq("Historical")
        & df["Aggregate group"].isin(COUNTRY_GROUPS)
        & df["parameter"].eq("price_p50_2025USD")
        & df["mode"].isin(selected)
        & df["powertrain"].isin(["BEV", "ICEV"]),
        ["region_country", "year", "mode", "powertrain", "unit", "value"],
    ].copy()
    if data.empty:
        return pd.DataFrame(columns=result_columns)

    data["year"] = pd.to_numeric(data["year"], errors="raise")
    if not np.isfinite(data["year"]).all() or data["year"].mod(1).ne(0).any():
        raise ValueError("Violin years must be finite integers.")
    data["year"] = data["year"].astype(int)
    data = data.loc[data["year"].eq(year)].copy()
    if data.empty:
        return pd.DataFrame(columns=result_columns)

    keys = ["region_country", "year", "mode", "powertrain"]
    if data.duplicated(keys).any():
        raise ValueError("Duplicate country-year-segment-powertrain price records.")
    if not data["unit"].eq("2025 USD").all():
        raise ValueError("Median prices must use the '2025 USD' unit.")
    data["value"] = pd.to_numeric(data["value"], errors="raise")
    if not np.isfinite(data["value"].dropna()).all():
        raise ValueError("Median prices must be finite when present.")

    paired = data.pivot(
        index=["region_country", "year", "mode"],
        columns="powertrain",
        values="value",
    ).reindex(columns=["BEV", "ICEV"])
    paired = paired.dropna().loc[lambda x: x["BEV"].gt(0) & x["ICEV"].gt(0)]
    paired = paired.reset_index().rename(
        columns={"BEV": "BEV_median", "ICEV": "ICEV_median"}
    )
    paired["price_gap_pct"] = 100 * (
        paired["BEV_median"] - paired["ICEV_median"]
    ) / paired["ICEV_median"]

    paired["mode"] = pd.Categorical(paired["mode"], selected, ordered=True)
    paired = paired.sort_values(["mode", "region_country"]).reset_index(drop=True)
    paired["mode"] = paired["mode"].astype(str)
    return paired[result_columns]


def build_price_violin(
    df: pd.DataFrame,
    segments: list[str] | None = None,
    year: int = 2025,
) -> go.Figure | None:
    """Build one violin per selected segment with country points and boxes."""
    data = prepare_price_violin_data(df, segments, year)
    if data.empty:
        return None

    present_segments = [
        segment for segment in PRICE_SEGMENTS if data["mode"].eq(segment).any()
    ]
    segment_counts = {
        segment: int(data.loc[data["mode"].eq(segment), "region_country"].nunique())
        for segment in present_segments
    }

    fig = go.Figure()
    for segment in present_segments:
        rows = data.loc[data["mode"].eq(segment)]
        fig.add_trace(
            go.Violin(
                x=rows["mode"],
                y=rows["price_gap_pct"],
                name=segment,
                customdata=rows[
                    ["region_country", "BEV_median", "ICEV_median"]
                ].to_numpy(),
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Segment: %{x}<br>"
                    "BEV median: %{customdata[1]:,.0f} 2025 USD<br>"
                    "ICEV median: %{customdata[2]:,.0f} 2025 USD<br>"
                    "BEV–ICEV median gap: %{y:.1f}%"
                    "<extra></extra>"
                ),
                box_visible=True,
                points="all",
                hoveron="points",
                jitter=0.13,
                pointpos=0,
                marker=dict(size=5, opacity=0.75, color=SEGMENT_COLORS[segment]),
                line=dict(color=SEGMENT_COLORS[segment]),
                fillcolor=SEGMENT_COLORS[segment],
                opacity=0.65,
                showlegend=False,
            )
        )

    fig.add_hline(
        y=0,
        line_width=1.5,
        line_dash="dash",
        line_color="#374151",
        annotation_text="Price parity (0%)",
    )
    fig.update_xaxes(
        title="Car segment",
        categoryorder="array",
        categoryarray=present_segments,
        tickvals=present_segments,
        ticktext=[f"{segment}<br>n={segment_counts[segment]}" for segment in present_segments],
        tickangle=-15,
    )
    fig.update_yaxes(title="BEV–ICEV median price gap (%)", zeroline=False)
    fig.update_layout(
        title=f"04 · Country-level BEV–ICEV median price gaps, {year}",
        template="plotly_white",
        height=610,
        font=dict(family="Arial", size=12),
        margin=dict(l=65, r=40, t=85, b=100),
        hovermode="closest",
        violingap=0.12,
        meta=dict(
            year=year,
            observation_count=len(data),
            country_count=data["region_country"].nunique(),
            segment_counts=segment_counts,
        ),
    )
    return fig
