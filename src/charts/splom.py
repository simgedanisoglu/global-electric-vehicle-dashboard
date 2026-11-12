"""National EV stock and public-charging relationships in one SPLOM."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go


COUNTRY_GROUPS = ("Other", "Projection_country")
PUBLIC_CHARGER_TYPES = (
    "Publicly available slow",
    "Publicly available fast",
    "Publicly available ultra-fast",
)
SPLOM_DIMENSIONS = (
    "log_EV_stock",
    "log_Public_chargers",
    "Cars_per_point",
    "EV_sales_share",
)
DIMENSION_LABELS = {
    "log_EV_stock": "log10(EV stock)",
    "log_Public_chargers": "log10(Public charging points)",
    "Cars_per_point": "EV cars per public point",
    "EV_sales_share": "EV sales share (%)",
}


def prepare_charging_splom_data(
    df: pd.DataFrame,
    year: int = 2025,
) -> pd.DataFrame:
    """Prepare one complete country-year observation for each SPLOM point."""
    required = {
        "region_country", "category", "parameter", "mode", "powertrain",
        "year", "unit", "value", "Aggregate group",
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required SPLOM columns: {', '.join(sorted(missing))}")
    if isinstance(year, bool) or not isinstance(year, (int, np.integer)):
        raise ValueError("year must be an integer year.")

    profile_columns = [
        "region_country", "year", "EV_stock", "Public_chargers",
        "Cars_per_point", "log_EV_stock", "log_Public_chargers",
        "EV_sales_share",
    ]
    empty = pd.DataFrame(columns=profile_columns)
    empty.attrs["incomplete_charger_countries"] = []
    empty.attrs["no_charger_record_countries"] = []

    data = df.loc[
        df["category"].eq("Historical")
        & df["Aggregate group"].isin(COUNTRY_GROUPS)
    ].copy()
    relevant = data.loc[
        (
            data["parameter"].eq("EV stock")
            & data["mode"].eq("Cars")
            & data["powertrain"].eq("EV")
        )
        | (
            data["parameter"].eq("EV sales share")
            & data["mode"].eq("Cars")
            & data["powertrain"].eq("EV")
        )
        | (
            data["parameter"].eq("EV charging points")
            & data["mode"].eq("EVSE")
            & data["powertrain"].isin(PUBLIC_CHARGER_TYPES)
        )
    ].copy()
    if relevant.empty:
        return empty

    relevant["year"] = pd.to_numeric(relevant["year"], errors="raise")
    if not np.isfinite(relevant["year"]).all() or relevant["year"].mod(1).ne(0).any():
        raise ValueError("SPLOM years must be finite integers.")
    relevant["year"] = relevant["year"].astype(int)
    relevant = relevant.loc[relevant["year"].eq(year)].copy()
    if relevant.empty:
        return empty

    stock = relevant.loc[
        relevant["parameter"].eq("EV stock")
        & relevant["mode"].eq("Cars")
        & relevant["powertrain"].eq("EV")
    ].copy()
    sales_share = relevant.loc[
        relevant["parameter"].eq("EV sales share")
        & relevant["mode"].eq("Cars")
        & relevant["powertrain"].eq("EV")
    ].copy()
    charger_parts = relevant.loc[
        relevant["parameter"].eq("EV charging points")
        & relevant["mode"].eq("EVSE")
        & relevant["powertrain"].isin(PUBLIC_CHARGER_TYPES)
    ].copy()

    checks = [
        (stock, "EV stock", "Vehicles", ["region_country", "year"]),
        (sales_share, "EV sales share", "percent", ["region_country", "year"]),
        (
            charger_parts,
            "EV charging-point type",
            "charging points",
            ["region_country", "year", "powertrain"],
        ),
    ]
    for frame, label, unit, keys in checks:
        if frame.duplicated(keys).any():
            raise ValueError(f"Duplicate {label} records found.")
        if not frame["unit"].eq(unit).all():
            raise ValueError(f"{label} must use the '{unit}' unit.")
        frame["value"] = pd.to_numeric(frame["value"], errors="raise")
        if not np.isfinite(frame["value"].dropna()).all():
            raise ValueError(f"{label} values must be finite when present.")

    if not sales_share["value"].dropna().between(0, 100).all():
        raise ValueError("EV sales share values must be between 0 and 100.")
    if charger_parts["value"].dropna().lt(0).any():
        raise ValueError("EV charging-point values must be nonnegative.")

    stock_countries = set(stock["region_country"].dropna())
    share_countries = set(sales_share["region_country"].dropna())
    charger_countries = set(charger_parts["region_country"].dropna())
    no_charger_records = sorted(
        (stock_countries & share_countries) - charger_countries
    )

    charger_wide = charger_parts.pivot(
        index=["region_country", "year"],
        columns="powertrain",
        values="value",
    ).reindex(columns=PUBLIC_CHARGER_TYPES)
    incomplete = sorted(
        charger_wide.loc[charger_wide.isna().any(axis=1)]
        .index.get_level_values("region_country")
        .unique()
        .tolist()
    )
    public_chargers = (
        charger_wide.dropna()
        .sum(axis=1)
        .rename("Public_chargers")
        .reset_index()
    )

    profile = (
        stock[["region_country", "year", "value"]]
        .rename(columns={"value": "EV_stock"})
        .merge(public_chargers, on=["region_country", "year"], validate="one_to_one")
        .merge(
            sales_share[["region_country", "year", "value"]].rename(
                columns={"value": "EV_sales_share"}
            ),
            on=["region_country", "year"],
            validate="one_to_one",
        )
        .dropna()
    )
    profile = profile.loc[
        profile["EV_stock"].gt(0) & profile["Public_chargers"].gt(0)
    ].copy()
    profile["Cars_per_point"] = profile["EV_stock"] / profile["Public_chargers"]
    profile["log_EV_stock"] = np.log10(profile["EV_stock"])
    profile["log_Public_chargers"] = np.log10(profile["Public_chargers"])
    profile = profile[profile_columns].sort_values("region_country").reset_index(drop=True)
    profile.attrs["incomplete_charger_countries"] = incomplete
    profile.attrs["no_charger_record_countries"] = no_charger_records
    return profile


def build_charging_splom(
    df: pd.DataFrame,
    year: int = 2025,
) -> go.Figure | None:
    """Build a four-dimension SPLOM with linked country selections."""
    profile = prepare_charging_splom_data(df, year)
    if len(profile) < 4:
        return None

    countries = profile["region_country"].tolist()
    customdata = profile[
        ["region_country", "EV_stock", "Public_chargers", "EV_sales_share"]
    ].to_numpy()
    fig = go.Figure(
        go.Splom(
            dimensions=[
                dict(label=DIMENSION_LABELS[column], values=profile[column])
                for column in SPLOM_DIMENSIONS
            ],
            ids=countries,
            customdata=customdata,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "EV stock: %{customdata[1]:,.0f} vehicles<br>"
                "Public charging points: %{customdata[2]:,.0f}<br>"
                "EV sales share: %{customdata[3]:.1f}%"
                "<extra></extra>"
            ),
            marker=dict(
                color=profile["EV_sales_share"],
                colorscale="Viridis",
                cmin=0,
                cmax=100,
                showscale=True,
                size=7,
                opacity=0.75,
                colorbar=dict(title="EV sales share (%)"),
            ),
            selected=dict(marker=dict(opacity=1, size=10)),
            unselected=dict(marker=dict(opacity=0.18)),
            diagonal_visible=False,
            showupperhalf=False,
        )
    )

    spearman = float(
        profile["EV_stock"].rank().corr(profile["Public_chargers"].rank())
    )
    fig.update_layout(
        title=f"03 · EV stock and public charging relationships, {year}",
        template="plotly_white",
        height=800,
        font=dict(family="Arial", size=12),
        margin=dict(l=70, r=125, t=85, b=70),
        dragmode="select",
        hovermode="closest",
        clickmode="event+select",
        meta=dict(
            year=year,
            observation_count=len(profile),
            incomplete_charger_countries=profile.attrs[
                "incomplete_charger_countries"
            ],
            no_charger_record_countries=profile.attrs[
                "no_charger_record_countries"
            ],
            spearman_ev_stock_public_chargers=spearman,
            selection_status="manual browser verification required",
        ),
    )
    return fig
