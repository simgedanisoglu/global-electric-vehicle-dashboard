"""Focused tests for the ML Insights chart builders."""

from pathlib import Path
import unittest

import pandas as pd
import plotly.graph_objects as go

from src.charts.ml_clustering import (
    CLUSTER_COLORS, CLUSTER_ORDER, build_cluster_strip, prepare_cluster_data,
    summarize_clusters,
)
from src.charts.ml_regression import (
    ACTUAL_COLUMN, MODELS, bootstrap_mae_difference, build_error_boxplot,
    prepare_regression_errors, summarize_errors,
)

MODEL_DIR = Path(__file__).resolve().parents[1] / "data" / "modeldataset"


class ClusteringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = pd.read_csv(MODEL_DIR / "clustering" / "clustering_results.csv")

    def test_year_filter_and_uniqueness(self):
        data = prepare_cluster_data(self.df, 2025, [], list(CLUSTER_ORDER))
        self.assertEqual(len(data), 33)
        self.assertFalse(data["region_country"].duplicated().any())

    def test_country_and_cluster_filters(self):
        data = prepare_cluster_data(self.df, 2025, ["Norway"], ["Advanced EV Adoption"])
        self.assertTrue(set(data["region_country"]) <= {"Norway"})
        self.assertEqual(prepare_cluster_data(self.df, 2025, [], []).shape[0], 0)

    def test_figure_colors_order_and_empty(self):
        data = prepare_cluster_data(self.df, 2025, [], list(CLUSTER_ORDER))
        fig = build_cluster_strip(data)
        self.assertIsInstance(fig, go.Figure)
        for trace in fig.data:
            self.assertEqual(trace.marker.color, CLUSTER_COLORS[trace.name])
        self.assertEqual(list(fig.layout.xaxis.categoryarray), list(CLUSTER_ORDER))
        self.assertIsNone(build_cluster_strip(data.iloc[0:0]))

    def test_summary_matches_filter(self):
        data = prepare_cluster_data(self.df, 2025, [], list(CLUSTER_ORDER))
        summary = summarize_clusters(data)
        self.assertEqual(int(summary["Countries"].sum()), len(data))
        one = prepare_cluster_data(self.df, 2025, [], ["Early EV Adoption"])
        self.assertEqual(list(summarize_clusters(one).index), ["Early EV Adoption"])

    def test_missing_columns_raise(self):
        with self.assertRaises(ValueError):
            prepare_cluster_data(self.df.drop(columns=["cluster_name"]))

    def test_hover_includes_cluster_name_and_values(self):
        data = prepare_cluster_data(self.df, 2025, ["India"], list(CLUSTER_ORDER))
        fig = build_cluster_strip(data)
        trace = fig.data[0]
        self.assertIn("EV Adoption Cluster=%{x}", trace.hovertemplate)
        self.assertIn("EV Stock Share (%)", trace.hovertemplate)
        self.assertIn("Year", trace.hovertemplate)
        self.assertEqual(trace.x[0], "Early EV Adoption")

    def test_single_country_summary_follows_filter(self):
        data = prepare_cluster_data(self.df, 2025, ["India"], list(CLUSTER_ORDER))
        summary = summarize_clusters(data)
        self.assertEqual(summary["Countries"].tolist(), [1])


class RegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = pd.read_csv(
            MODEL_DIR / "regression" / "regression_results_2025.csv", encoding="utf-8-sig")

    def test_overall_metrics(self):
        summary = summarize_errors(prepare_regression_errors(self.df))
        self.assertEqual(summary.loc["Linear Regression", "MAE (pp)"], 4.114)
        self.assertEqual(summary["MAE (pp)"].idxmin(), "Linear Regression")
        self.assertEqual(summary["Median error (pp)"].idxmin(), "XGBoost")
        self.assertTrue((summary["Countries"] == 60).all())

    def test_error_matches_source_columns(self):
        data = prepare_regression_errors(self.df, ["Random Forest"])
        source = self.df.set_index("region_country")["Random Forest Hata"]
        for row in data.itertuples():
            self.assertAlmostEqual(row.abs_error, source[row.region_country], places=4)

    def test_filters_and_summary_follow_them(self):
        data = prepare_regression_errors(self.df, ["XGBoost"], ["Norway", "Austria"])
        self.assertEqual(set(data["model"]), {"XGBoost"})
        self.assertEqual(len(data), 2)
        self.assertEqual(int(summarize_errors(data).loc["XGBoost", "Countries"]), 2)
        self.assertTrue(prepare_regression_errors(self.df, []).empty)

    def test_figure(self):
        fig = build_error_boxplot(prepare_regression_errors(self.df))
        self.assertEqual([t.name for t in fig.data], list(MODELS))
        self.assertTrue(all(t.boxpoints == "all" for t in fig.data))
        self.assertIsNone(build_error_boxplot(prepare_regression_errors(self.df, [])))

    def test_missing_columns_raise(self):
        with self.assertRaises(ValueError):
            prepare_regression_errors(self.df.drop(columns=[ACTUAL_COLUMN]))

    def test_single_model_single_country_summary(self):
        data = prepare_regression_errors(self.df, ["XGBoost"], ["Norway"])
        summary = summarize_errors(data)
        self.assertEqual(list(summary.index), ["XGBoost"])
        self.assertEqual(int(summary.loc["XGBoost", "Countries"]), 1)
        self.assertEqual(summary.loc["XGBoost", "MAE (pp)"],
                         summary.loc["XGBoost", "Median error (pp)"])

    def test_predictions_are_unchanged_and_may_exceed_valid_range(self):
        data = prepare_regression_errors(self.df, ["Linear Regression"], ["Norway"])
        self.assertAlmostEqual(data["prediction"].iloc[0], 101.94, places=2)

    def test_bootstrap_interval_is_reproducible_and_ordered(self):
        low, high = bootstrap_mae_difference(self.df, "Linear Regression", "XGBoost")
        again = bootstrap_mae_difference(self.df, "Linear Regression", "XGBoost")
        self.assertEqual((low, high), again)
        self.assertLess(low, high)
        self.assertLessEqual(low, 0)       # ML models not clearly distinguishable
        self.assertGreaterEqual(high, 0)
        low_p, high_p = bootstrap_mae_difference(
            self.df, "Linear Regression", "Persistence Baseline")
        self.assertLess(high_p, 0)         # improvement over persistence is clear


if __name__ == "__main__":
    unittest.main()
