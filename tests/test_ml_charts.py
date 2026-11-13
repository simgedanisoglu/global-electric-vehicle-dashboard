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
    ACTUAL_COLUMN, MODELS, build_error_boxplot, prepare_regression_errors,
    summarize_errors,
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


if __name__ == "__main__":
    unittest.main()
