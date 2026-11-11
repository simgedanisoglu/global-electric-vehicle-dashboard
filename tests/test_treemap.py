"""Treemap data contract and Figure checks; no UI or file writes."""

from pathlib import Path
import unittest

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.charts.treemap import METRICS, MODES, MODE_COLORS, build_energy_treemap


def fixture(metric="Oil displacement Mlge"):
    return pd.DataFrame([
        dict(category="Historical", region_country="World", year=2025,
             powertrain="EV", mode=mode, parameter=metric,
             unit=METRICS[metric][1], value=float(i + 1))
        for i, mode in enumerate(MODES)
    ])


class TreemapTests(unittest.TestCase):
    def test_real_csv_metrics(self):
        source = Path(__file__).resolve().parents[1] / "data/analysisdataset/global_ev_cleaned.csv"
        df = pd.read_csv(source)
        original = df.copy(deep=True)
        totals = [97200, 1182, 254800]
        for metric, total in zip(METRICS, totals):
            with self.subTest(metric=metric):
                fig = build_energy_treemap(df, metric)
                self.assertIsInstance(fig, go.Figure)
                trace = fig.data[0]
                leaves = [(name, value, custom, color) for name, value, custom, color
                          in zip(trace.labels, trace.values, trace.customdata, trace.marker.colors)
                          if name in MODES]
                self.assertEqual(len(leaves), 5)
                self.assertAlmostEqual(sum(row[1] for row in leaves), total)
                self.assertAlmostEqual(sum(row[2][4] for row in leaves), 100)
                for name, value, custom, color in leaves:
                    expected = df.loc[
                        df.category.eq("Historical") & df.region_country.eq("World")
                        & df.year.eq(2025) & df.powertrain.eq("EV")
                        & df.parameter.eq(metric) & df["mode"].eq(name), "value"]
                    self.assertEqual(len(expected), 1)
                    self.assertEqual(value, expected.iloc[0])
                    self.assertEqual(custom[1], 2025)
                    self.assertEqual(custom[2], metric)
                    self.assertEqual(custom[3], METRICS[metric][1])
                    self.assertEqual(color, MODE_COLORS[name])
                self.assertEqual(trace.branchvalues, "total")
                self.assertIn("World", trace.parents)
                self.assertFalse(fig.layout.updatemenus)
                self.assertIn(METRICS[metric][1], fig.layout.title.text)
                self.assertEqual(fig.layout.title.text,
                                 f"05 · 2025 World | {METRICS[metric][0]} ({METRICS[metric][1]})")
                self.assertEqual(dict(zip(trace.ids, trace.marker.colors))["World"], "#FFD700")
                for label in ["Vehicle type / scope:", "Year:", "Metric:", "Value:",
                              "Share of World total (five vehicle modes):"]:
                    self.assertIn(label, trace.hovertemplate)
                fig.to_json()
        pd.testing.assert_frame_equal(df, original)

    def test_excludes_unrelated_rows(self):
        base = fixture()
        extras = []
        for column, value in [("category", "Projection-CPS"),
                              ("region_country", "China"), ("year", 2035),
                              ("powertrain", "BEV"), ("mode", "EVSE"),
                              ("parameter", "Electricity demand")]:
            extra = base.iloc[[0]].copy()
            extra[column] = value
            extra["value"] = 999999
            extras.append(extra)
        fig = build_energy_treemap(pd.concat([base, *extras], ignore_index=True))
        self.assertEqual(dict(zip(fig.data[0].labels, fig.data[0].values))["World"], 15)

    def test_duplicate_is_rejected(self):
        df = fixture()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            build_energy_treemap(pd.concat([df, df.iloc[[0]]]))

    def test_incomplete_and_empty_return_none(self):
        df = fixture()
        self.assertIsNone(build_energy_treemap(df.iloc[:0]))
        self.assertIsNone(build_energy_treemap(df.iloc[:-1]))
        df.loc[0, "value"] = np.nan
        self.assertIsNone(build_energy_treemap(df))

    def test_invalid_values(self):
        for value in [-1, np.inf, -np.inf, "invalid"]:
            with self.subTest(value=value):
                df = fixture().astype({"value": "object"})
                df.loc[0, "value"] = value
                with self.assertRaises(ValueError):
                    build_energy_treemap(df)

    def test_zero_values(self):
        df = fixture()
        df.loc[0, "value"] = 0
        fig = build_energy_treemap(df)
        self.assertEqual(fig.layout.annotations[0].text, "Zero value (no area): Cars")
        self.assertEqual(dict(zip(fig.data[0].labels, fig.data[0].values))["Cars"], 0)
        df["value"] = 0
        self.assertIsNone(build_energy_treemap(df))

    def test_schema_metric_unit_year(self):
        with self.assertRaisesRegex(ValueError, "Missing required"):
            build_energy_treemap(fixture().drop(columns="unit"))
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            build_energy_treemap(fixture(), "invalid")
        for unit in ["GWh", None]:
            df = fixture()
            df.loc[0, "unit"] = unit
            with self.assertRaisesRegex(ValueError, "Expected unit"):
                build_energy_treemap(df)
        for year in [2035, 2009, 2025.5, True]:
            with self.subTest(year=year), self.assertRaises(ValueError):
                build_energy_treemap(fixture(), year=year)


if __name__ == "__main__":
    unittest.main()
