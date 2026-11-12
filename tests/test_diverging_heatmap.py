"""Scenario pairing, missingness, normalization and reference design checks."""

from pathlib import Path
import unittest

import numpy as np
import pandas as pd
import plotly.colors
import plotly.graph_objects as go

from src.charts.diverging_heatmap import SCENARIO_METRICS, build_scenario_heatmap


def fixture():
    return pd.DataFrame([
        dict(region_country=geo, parameter=parameter, mode=mode,
             powertrain=pt, year=2035, unit=unit,
             **{"Projection-CPS": 20.0, "Projection-STEPS": steps})
        for parameter, mode, pt, _, unit in SCENARIO_METRICS
        for geo, steps in [("China", 30.0), ("World", 10.0)]
    ])


class DivergingHeatmapTests(unittest.TestCase):
    def test_real_csv(self):
        path = Path(__file__).resolve().parents[1] / "data/analysisdataset/ev_2035_scenario_comparison.csv"
        sc = pd.read_csv(path)
        original = sc.copy(deep=True)
        fig = build_scenario_heatmap(sc)
        self.assertIsInstance(fig, go.Figure)
        trace = fig.data[0]
        self.assertEqual(len(trace.x), 9)
        self.assertEqual(list(trace.x), ["China", "Europe", "India", "Japan", "Korea",
                                        "Latin America", "Southeast Asia", "USA", "World"])
        self.assertEqual(list(trace.y), [m[3] for m in SCENARIO_METRICS])
        z = np.asarray(trace.z, dtype=float)
        self.assertEqual(z.shape, (9, 9))
        self.assertEqual(int(np.isfinite(z).sum()), 81)
        self.assertEqual((int((z > 0).sum()), int((z == 0).sum()), int((z < 0).sum())), (62, 9, 10))
        self.assertEqual((z.min(), z.max()), (-9.375, 400.0))
        for i, (parameter, mode, pt, _, unit) in enumerate(SCENARIO_METRICS):
            for j, geo in enumerate(trace.x):
                rows = sc.loc[sc.year.eq(2035) & sc.parameter.eq(parameter)
                              & sc["mode"].eq(mode) & sc.powertrain.eq(pt)
                              & sc.region_country.eq(geo)]
                self.assertEqual(len(rows), 1)
                row = rows.iloc[0]
                self.assertEqual(row.unit, unit)
                self.assertAlmostEqual(z[i, j], 100 * (row["Projection-STEPS"] - row["Projection-CPS"]) / abs(row["Projection-CPS"]))
                self.assertEqual(list(trace.customdata[i, j, :4]), [parameter, mode, pt, unit])
                self.assertEqual(trace.customdata[i, j, 4], row["Projection-CPS"])
                self.assertEqual(trace.customdata[i, j, 5], row["Projection-STEPS"])
        self.assertEqual(fig.layout.coloraxis.cmin, -400)
        self.assertEqual(fig.layout.coloraxis.cmax, 400)
        self.assertEqual(len(fig.data), 1)
        fig.to_json()
        pd.testing.assert_frame_equal(sc, original)

    def test_notebook_design_and_english_hover(self):
        fig = build_scenario_heatmap(fixture())
        self.assertEqual(fig.data[0].type, "heatmap")
        expected = plotly.colors.get_colorscale("RdBu_r")
        actual = fig.layout.coloraxis.colorscale
        self.assertEqual([c for _, c in actual], [c for _, c in expected])
        np.testing.assert_allclose([v for v, _ in actual], [v for v, _ in expected])
        self.assertEqual(fig.layout.coloraxis.cmid, 0)
        self.assertEqual(fig.layout.coloraxis.cmin, -50)
        self.assertEqual(fig.layout.coloraxis.cmax, 50)
        self.assertEqual(fig.layout.coloraxis.colorbar.title.text, "STEPS − CPS (%)")
        self.assertEqual(fig.layout.xaxis.title.text, "Geography")
        self.assertEqual(fig.layout.yaxis.title.text, "Indicator / vehicle")
        self.assertEqual(fig.layout.yaxis.autorange, "reversed")
        self.assertEqual(fig.layout.xaxis.tickangle, -30)
        self.assertEqual(fig.layout.height, 660)
        self.assertEqual(fig.layout.plot_bgcolor, "#e2e8f0")
        self.assertFalse(fig.layout.xaxis.fixedrange)
        self.assertFalse(fig.layout.yaxis.fixedrange)
        self.assertFalse(fig.layout.sliders)
        for text in ["Geography:", "Year: 2035", "Parameter:", "Mode:", "Powertrain:",
                     "CPS:", "STEPS:", "Relative difference:"]:
            self.assertIn(text, fig.data[0].hovertemplate)

    def test_zero_missing_and_absent_pairs(self):
        sc = fixture()
        sc.loc[0, "Projection-CPS"] = 0
        sc.loc[1, "Projection-STEPS"] = np.nan
        sc.loc[2, "Projection-STEPS"] = 20
        sc = sc.drop(index=3)
        fig = build_scenario_heatmap(sc)
        z = np.asarray(fig.data[0].z)
        self.assertTrue(np.isnan(z[0]).all())
        self.assertEqual(z[1, 0], 0)
        self.assertTrue(np.isnan(z[1, 1]))
        custom = fig.data[0].customdata
        self.assertIn("CPS=0", custom[0, 0, 6])
        self.assertEqual(custom[0, 1, 5], "Missing")
        self.assertEqual(custom[1, 1, 6], "No matching scenario record")
        overlay = fig.data[1]
        self.assertTrue(np.isnan(overlay.z[1][0]))  # Real zero stays in main color scale.
        self.assertEqual(overlay.z[0][0], 0)  # Mask only, not a scenario measurement.
        self.assertIn("Not defined", overlay.hovertemplate)
        self.assertFalse(overlay.showscale)
        fig.to_json()

    def test_empty_and_all_nan(self):
        sc = fixture()
        self.assertIsNone(build_scenario_heatmap(sc.iloc[:0]))
        for column, value in [("Projection-CPS", 0), ("Projection-CPS", np.nan),
                              ("Projection-STEPS", np.nan)]:
            with self.subTest(column=column, value=value):
                self.assertIsNone(build_scenario_heatmap(sc.assign(**{column: value})))

    def test_missing_rows_and_columns_are_retained(self):
        sc = fixture()
        sc = sc.loc[sc.parameter.ne("EV stock")].copy()
        sc.loc[sc.region_country.eq("World"), "Projection-CPS"] = np.nan
        trace = build_scenario_heatmap(sc).data[0]
        self.assertEqual(list(trace.x), ["China", "World"])
        self.assertEqual(len(trace.y), 9)
        self.assertTrue(np.isnan(np.asarray(trace.z)[2]).all())
        self.assertTrue(np.isnan(np.asarray(trace.z)[:, 1]).all())

    def test_filters_and_unused_difference(self):
        sc = fixture()
        extras = []
        for column, value in [("year", 2025), ("parameter", "EV stock share"),
                              ("mode", "Buses"), ("powertrain", "BEV"),
                              ("region_country", "Not in selected geographies")]:
            row = sc.iloc[[0]].copy()
            row[column] = value
            row["Projection-CPS"] = np.inf
            extras.append(row)
        combined = pd.concat([sc, *extras], ignore_index=True).assign(difference=-999999)
        np.testing.assert_array_equal(build_scenario_heatmap(sc).data[0].z,
                                      build_scenario_heatmap(combined).data[0].z)

    def test_invalid_data(self):
        sc = fixture()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            build_scenario_heatmap(pd.concat([sc, sc.iloc[[0]]]))
        with self.assertRaisesRegex(ValueError, "Missing required"):
            build_scenario_heatmap(sc.drop(columns="unit"))
        for unit in ["GWh", None]:
            bad = sc.copy()
            bad.loc[0, "unit"] = unit
            with self.assertRaisesRegex(ValueError, "Expected unit"):
                build_scenario_heatmap(bad)
        for column in ["Projection-CPS", "Projection-STEPS", "year"]:
            for value in [np.inf, -np.inf, "invalid"]:
                bad = sc.astype({column: object})
                bad.loc[0, column] = value
                with self.subTest(column=column, value=value), self.assertRaises(ValueError):
                    build_scenario_heatmap(bad)

    def test_relative_percent_minimum_scale_and_absolute_denominator(self):
        sc = fixture()
        sc["Projection-STEPS"] = 20.2
        sc.loc[sc.parameter.eq("EV sales share"), "Projection-CPS"] = 20
        fig = build_scenario_heatmap(sc)
        np.testing.assert_allclose(fig.data[0].z, 1)  # 1%, not 0.2 percentage points.
        self.assertEqual(fig.layout.coloraxis.cmin, -5)
        self.assertEqual(fig.layout.coloraxis.cmax, 5)
        sc["Projection-CPS"] = -20
        sc["Projection-STEPS"] = -10
        np.testing.assert_allclose(build_scenario_heatmap(sc).data[0].z, 50)
        sc["Projection-CPS"] = sc["Projection-STEPS"] = 20
        fig = build_scenario_heatmap(sc)
        np.testing.assert_array_equal(fig.data[0].z, 0)
        self.assertEqual(len(fig.data), 1)


if __name__ == "__main__":
    unittest.main()
