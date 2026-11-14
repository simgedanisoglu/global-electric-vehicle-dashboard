from pathlib import Path

import pandas as pd
import streamlit as st

from src.charts.ml_clustering import (
    CLUSTER_ORDER, build_cluster_strip, prepare_cluster_data, summarize_clusters,
)
from src.charts.ml_regression import (
    MODELS, bootstrap_mae_difference, build_error_boxplot,
    prepare_regression_errors, summarize_errors,
)
from src.ui.theme import card_header, card_result, card_plot


MODEL_DIR = Path(__file__).resolve().parents[1] / "data" / "modeldataset"


@st.cache_data
def load_clustering():
    return pd.read_csv(MODEL_DIR / "clustering" / "clustering_results.csv")


@st.cache_data
def load_regression():
    return pd.read_csv(
        MODEL_DIR / "regression" / "regression_results_2025.csv", encoding="utf-8-sig",
    )


def _count(number, singular, plural):
    return f"{number} {singular if number == 1 else plural}"


@st.cache_data
def bootstrap_intervals():
    results = load_regression()
    pairs = [
        ("Linear Regression", "XGBoost"), ("Linear Regression", "Random Forest"),
        ("Linear Regression", "Persistence Baseline"),
        ("Random Forest", "Persistence Baseline"), ("XGBoost", "Persistence Baseline"),
    ]
    return {pair: bootstrap_mae_difference(results, *pair) for pair in pairs}


def _interval(low, high):
    return f"[{low:+.2f}, {high:+.2f}] pp"


# Page-local tweak: tighter top clearance than the shared theme, ML Insights only.
st.markdown(
    """<style>
    .stMainBlockContainer { padding-top: 4.25rem; }
    @media (max-width: 1099px) { .stMainBlockContainer { padding-top: 7.25rem; } }
    /* The style holder itself must not add a flex gap above the title. */
    .stMainBlockContainer [data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] style) { display: none; }
    </style>""",
    unsafe_allow_html=True,
)

st.title("ML Insights")
st.caption("Clustering and next-year prediction of EV sales share · Source: IEA Global EV Outlook 2026")
tabs = st.tabs(["Clustering", "Regression"])


def _clustering_methodology(results):
    ranges = results.groupby("cluster_name")["ev_sales_share"].agg(["min", "max"])
    range_text = "; ".join(
        f"{name.replace(' EV Adoption', '')} {ranges.loc[name, 'min']:.1f}–{ranges.loc[name, 'max']:.1f}%"
        for name in CLUSTER_ORDER
    )
    per_year = results.groupby("year")["region_country"].nunique()
    changed = int((results.groupby("region_country")["cluster_name"].nunique() > 1).sum())
    total = results["region_country"].nunique()
    return (
        "Country-year observations were grouped with K-Means (k = 3, Feature Set B) on EV "
        "sales share, EV stock share, EV stock and slow, fast and ultra-fast public chargers "
        "per 1,000 EVs. EV stock and the charger densities were log1p-transformed, then all "
        "six features were standardized. The silhouette score of this solution is about "
        "0.290 (see clustering.ipynb), which indicates weak to moderate cluster structure; "
        "boundaries differed between feature sets and algorithms, so treat clusters as a "
        "descriptive grouping, not sharply separated classes. The Early, Intermediate and "
        "Advanced labels were assigned after clustering by ordering cluster EV sales shares. "
        "Because stock and charging density also shape the clusters, sales-share ranges "
        f"overlap across clusters (all years: {range_text}) and the labels describe relative "
        "position, not a country's development stage. "
        f"{changed} of {total} countries change cluster over the years. Only country-years "
        "with complete inputs are clustered, so coverage is smaller than the full dataset "
        f"and the country set changes across years ({per_year.min()}–{per_year.max()} "
        "countries per year); comparisons between years mix different country sets. "
        "Membership is fixed in the results file and is not recomputed when filters change; "
        "the summary uses only the filtered countries. Each point is one country, jittered "
        "horizontally for readability. Hover for values; zoom and pan with the toolbar."
    )


def _regression_methodology(results):
    outside = []
    for model in MODELS:
        values = results.set_index("region_country")[model]
        outside += [
            f"{model} for {country}, {value:.2f}%"
            for country, value in values[(values < 0) | (values > 100)].items()
        ]
    range_note = (
        "Predictions are not clipped and can fall outside the valid 0–100% range"
        + (f" (here: {'; '.join(outside)})" if outside else "")
        + "; predictions and metrics are shown as stored."
    )
    return (
        "Each model predicts a country's 2025 EV sales share from three 2024 inputs: EV sales "
        "share, EV sales and BEV sales. Absolute error = |actual − prediction| in percentage "
        "points, not percentage growth. The Persistence Baseline simply repeats the 2024 "
        "value. Models were trained on earlier years (targets up to 2024) and tested once on "
        "2025; on the 2023–2024 validation data the Persistence Baseline performed best "
        "(MAE 4.06 pp versus 4.39 Linear, 4.51 XGBoost and 5.16 Random Forest, see "
        "regression.ipynb), so the 2025 ranking is not stable across periods. Results are "
        "read from a stored results file; no model is retrained here. The test set is small "
        "(one year, one record per country), so differences between ML models are tentative. "
        "MAE and median error can rank models differently because a few large misses weigh "
        f"heavily on the mean. {range_note} The highlighted overall metrics cover all "
        "countries; the table and insight above follow the active filters."
    )

with tabs[0]:
    clusters_df = load_clustering()
    with st.container(border=False, key="chart_group_ml_clustering", gap="small"):
        card_header(
            "01 · Strip Plot — EV Adoption Clusters",
            "How do K-Means clusters separate countries by their EV sales share?",
        )
        with st.container(border=True, key="card_plot_ml_clustering_chart"):
            years = sorted(clusters_df["year"].unique(), reverse=True)
            col_year, col_country, col_cluster = st.columns(3)
            year = col_year.selectbox(
                "Year", options=years,
                index=years.index(2025) if 2025 in years else 0, key="ml_cluster_year",
            )
            countries = col_country.multiselect(
                "Country", options=sorted(clusters_df["region_country"].unique()),
                placeholder="All countries", key="ml_cluster_countries",
            )
            clusters = col_cluster.multiselect(
                "Cluster", options=list(CLUSTER_ORDER), default=list(CLUSTER_ORDER),
                key="ml_cluster_clusters",
            )
            filtered = prepare_cluster_data(clusters_df, year, countries, clusters)
            fig = build_cluster_strip(filtered)
            insight = ""
            summary = summarize_clusters(filtered) if fig is not None else None
            if fig is not None:
                medians = summary["Median EV sales share (%)"]
                top = medians.idxmax()
                shown = _count(len(filtered), "country", "countries")
                if len(summary) == 1:
                    insight = (
                        f"In {year}, the {top} cluster has a median EV sales share of "
                        f"{medians[top]:.1f}% across the {shown} shown."
                    )
                else:
                    insight = (
                        f"In {year}, the {top} cluster has the highest median EV sales "
                        f"share ({medians[top]:.1f}%) among the {shown} shown. Clusters also "
                        "reflect EV stock and charging density, so their sales-share ranges "
                        "overlap."
                    )
            card_plot(fig, key="ml_clustering_chart")
            if summary is not None:
                st.markdown("**Cluster summary (active filters)**")
                st.dataframe(summary, width="stretch")
        card_result(
            fig, key="ml_clustering_chart", insight=insight,
            scope=(f"Historical · {year} · {_count(len(filtered), 'country', 'countries')} shown · "
                   f"{len(clusters)} of {len(CLUSTER_ORDER)} clusters selected · "
                   "EV sales share (%)"),
            methodology=_clustering_methodology(clusters_df),
        )

with tabs[1]:
    results_df = load_regression()
    overall = summarize_errors(prepare_regression_errors(results_df))
    with st.container(border=False, key="chart_group_ml_regression", gap="small"):
        card_header(
            "02 · Box Plot — Next-Year EV Sales Share Prediction Errors",
            "How accurately do models predict a country's 2025 EV sales share from 2024 indicators?",
        )
        with st.container(border=True, key="card_plot_ml_regression_chart"):
            col_model, col_country = st.columns(2)
            models = col_model.multiselect(
                "Model", options=list(MODELS), default=list(MODELS), key="ml_reg_models",
            )
            countries = col_country.multiselect(
                "Country", options=sorted(results_df["region_country"].unique()),
                placeholder="All countries", key="ml_reg_countries",
            )
            errors = prepare_regression_errors(results_df, models, countries)
            fig = build_error_boxplot(errors)
            insight = ""
            summary = summarize_errors(errors) if fig is not None else None
            shown = _count(errors["region_country"].nunique(), "country", "countries")
            if fig is not None and len(summary) == 1:
                model = summary.index[0]
                row = summary.iloc[0]
                insight = (
                    f"{model} has an MAE of {row['MAE (pp)']:.2f} pp, a median error of "
                    f"{row['Median error (pp)']:.2f} pp and a maximum error of "
                    f"{row['Max error (pp)']:.2f} pp across {shown}."
                )
            elif fig is not None:
                best_mae = summary["MAE (pp)"].idxmin()
                best_median = summary["Median error (pp)"].idxmin()
                insight = (
                    f"Across {shown} and {len(summary)} selected models, {best_mae} has the "
                    f"lowest observed MAE ({summary.loc[best_mae, 'MAE (pp)']:.2f} pp) and "
                    f"{best_median} the lowest observed median error "
                    f"({summary.loc[best_median, 'Median error (pp)']:.2f} pp); small "
                    "differences between models may not be meaningful."
                )
            card_plot(fig, key="ml_regression_chart")
            if summary is not None:
                st.markdown("**Performance summary (active filters)**")
                st.dataframe(summary, width="stretch")
            lin = overall.loc["Linear Regression"]
            xgb = overall.loc["XGBoost"]
            ci = bootstrap_intervals()
            ml_pairs = [("Linear Regression", "XGBoost"), ("Linear Regression", "Random Forest")]
            includes_zero = all(ci[p][0] <= 0 <= ci[p][1] for p in ml_pairs)
            beats_baseline = all(
                ci[(m, "Persistence Baseline")][1] < 0
                for m in ("Linear Regression", "Random Forest", "XGBoost")
            )
            st.info(
                f"Overall, unfiltered ({int(lin['Countries'])} countries): Linear Regression "
                f"has the lowest observed 2025 test MAE ({lin['MAE (pp)']:.3f} percentage "
                f"points), while XGBoost has the lowest median error "
                f"({xgb['Median error (pp)']:.3f} pp). In a bootstrap over countries (10,000 "
                "resamples), the 95% interval for the MAE difference of Linear Regression "
                f"versus XGBoost is {_interval(*ci[ml_pairs[0]])} and versus Random Forest "
                f"{_interval(*ci[ml_pairs[1]])}"
                + (", both including zero, so the ML models are not clearly distinguishable. "
                   if includes_zero else ". ")
                + ("All three ML models improved on the Persistence Baseline in the 2025 test "
                   "(intervals below zero), but the Persistence Baseline performed best on "
                   "the 2023–2024 validation data."
                   if beats_baseline else
                   "The Persistence Baseline performed best on the 2023–2024 validation data.")
            )
        card_result(
            fig, key="ml_regression_chart", insight=insight,
            scope=(f"Test year 2025 · {shown} · "
                   f"{len(models)} of {len(MODELS)} models · Absolute error in percentage points"),
            methodology=_regression_methodology(results_df),
        )
