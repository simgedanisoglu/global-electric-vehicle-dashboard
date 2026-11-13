from pathlib import Path

import pandas as pd
import streamlit as st

from src.charts.ml_clustering import (
    CLUSTER_ORDER, build_cluster_strip, prepare_cluster_data, summarize_clusters,
)
from src.charts.ml_regression import (
    MODELS, build_error_boxplot, prepare_regression_errors, summarize_errors,
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
                top = summary["Median EV sales share (%)"].idxmax()
                insight = (
                    f"In {year}, {top} has the highest median EV sales share "
                    f"({summary.loc[top, 'Median EV sales share (%)']:.1f}%) among the "
                    f"{len(filtered)} selected countries."
                )
            card_plot(fig, key="ml_clustering_chart")
            if summary is not None:
                st.markdown("**Cluster summary (active filters)**")
                st.dataframe(summary, width="stretch")
        card_result(
            fig, key="ml_clustering_chart", insight=insight,
            scope=(f"Historical · {year} · {len(filtered)} countries shown · "
                   f"{len(clusters)} of {len(CLUSTER_ORDER)} clusters selected · "
                   "EV sales share (%)"),
            methodology=(
                "Country-year observations were grouped by K-Means (k = 3) on standardized "
                "EV sales share, EV stock share, EV stock and slow, fast and ultra-fast "
                "public chargers per 1,000 EVs; cluster labels were assigned by the "
                "analysis and describe relative adoption, not official categories. Each point "
                "is one country, jittered horizontally for readability. Cluster membership is "
                "fixed per country-year in the results file and is not recomputed when filters "
                "change; the summary counts and medians use only the filtered countries. "
                "Only countries with complete inputs are clustered, so coverage is smaller "
                "than the full dataset. Hover for values; zoom and pan with the toolbar."
            ),
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
            if fig is not None:
                best_mae = summary["MAE (pp)"].idxmin()
                best_median = summary["Median error (pp)"].idxmin()
                insight = (
                    f"Among the selected models and {errors['region_country'].nunique()} "
                    f"countries, {best_mae} has the lowest MAE "
                    f"({summary.loc[best_mae, 'MAE (pp)']:.2f} pp) and {best_median} the "
                    f"lowest median error ({summary.loc[best_median, 'Median error (pp)']:.2f} pp)."
                )
            card_plot(fig, key="ml_regression_chart")
            if summary is not None:
                st.markdown("**Performance summary (active filters)**")
                st.dataframe(summary, width="stretch")
            lin = overall.loc["Linear Regression"]
            xgb = overall.loc["XGBoost"]
            st.info(
                f"Overall, unfiltered ({int(lin['Countries'])} countries): Linear Regression "
                f"achieved the lowest test MAE ({lin['MAE (pp)']:.3f} percentage points), "
                f"but XGBoost had the lowest median error "
                f"({xgb['Median error (pp)']:.3f} pp)."
            )
        card_result(
            fig, key="ml_regression_chart", insight=insight,
            scope=(f"Test year 2025 · {errors['region_country'].nunique()} countries · "
                   f"{len(models)} of {len(MODELS)} models · Absolute error in percentage points"),
            methodology=(
                "Each model predicts a country's 2025 EV sales share from 2024 historical "
                "indicators. Absolute error = |actual − prediction| in percentage points, "
                "not percentage growth. The Persistence Baseline simply repeats the 2024 "
                "value. Results are read from a stored results file; no model is retrained "
                "here. The test set is small (one year, one country each), so differences "
                "between models are tentative. MAE and median error can rank models "
                "differently because a few large misses weigh heavily on the mean. The "
                "highlighted overall metrics cover all countries; the table and insight "
                "above follow the active filters."
            ),
        )
