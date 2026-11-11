"""Connected scatter data, chronological path, and notebook design checks."""

from pathlib import Path
import unittest

import numpy as np
import pandas as pd
import plotly.colors
import plotly.graph_objects as go

from src.charts.connected_scatter import build_market_connected_scatter


def fixture():
    # Sales deliberately decrease with time, so sorting on X would be wrong.
    values = {2010: (200, 120, 80), 2011: (100, 30, 70), 2012: (150, 90, 60)}
    return pd.DataFrame([
        dict(region_country="World", category="Historical", parameter="EV sales",
             mode="Cars", powertrain=pt, year=year, unit="Vehicles", value=value)
        for year, sales in values.items()
        for pt, value in zip(("EV", "BEV", "PHEV"), sales)
    ])


class ConnectedScatterTests(unittest.TestCase):
    def test_real_csv(self):
        path = Path(__file__).resolve().parents[1] / "data/analysisdataset/global_ev_cleaned.csv"
        df = pd.read_csv(path)
        original = df.copy(deep=True)
        selected = df.loc[
            df.category.eq("Historical") & df.region_country.eq("World")
            & df.parameter.eq("EV sales") & df["mode"].eq("Cars")
            & df.powertrain.isin(["EV", "BEV", "PHEV"])
            & df.year.between(2010, 2025)
        ]
        self.assertEqual(len(selected), 48)
        self.assertFalse(selected.duplicated(["year", "powertrain"]).any())
        self.assertEqual(set(selected.unit), {"Vehicles"})
        wide = selected.pivot(index="year", columns="powertrain", values="value").sort_index()
        with self.assertLogs("src.charts.connected_scatter", level="INFO") as logs:
            fig = build_market_connected_scatter(df)
        self.assertIn("original totals retained", logs.output[0])
        self.assertIsInstance(fig, go.Figure)
        trace = fig.data[0]
        self.assertEqual(list(trace.text), [str(year) for year in range(2010, 2026)])
        self.assertEqual(fig.layout.meta["common_years"], 16)
        np.testing.assert_array_equal(trace.x, wide.EV)
        np.testing.assert_allclose(trace.y, 100 * wide.BEV / (wide.BEV + wide.PHEV))
        np.testing.assert_allclose(trace.customdata[:, 0], 100 * wide.PHEV / (wide.BEV + wide.PHEV))
        np.testing.assert_array_equal(trace.customdata[:, 1], wide.BEV)
        np.testing.assert_array_equal(trace.customdata[:, 2], wide.PHEV)
        self.assertEqual(trace.x[-1], 21000000)
        self.assertAlmostEqual(trace.y[-1], 100 * 14000000 / 21200000)
        self.assertEqual(int(wide.EV.ne(wide.BEV + wide.PHEV).sum()), 11)
        fig.to_json()
        pd.testing.assert_frame_equal(df, original)

    def test_chronology_and_notebook_design(self):
        fig = build_market_connected_scatter(fixture().sample(frac=1, random_state=3))
        trace = fig.data[0]
        self.assertEqual(list(trace.x), [200, 100, 150])
        np.testing.assert_allclose(trace.y, [60, 30, 60])
        self.assertEqual(list(trace.text), ["2010", "2011", "2012"])
        self.assertEqual(trace.mode, "lines+markers+text")
        self.assertEqual(trace.line.color, "#64748b")
        self.assertEqual(trace.line.width, 2.5)
        self.assertEqual(trace.marker.size, 11)
        self.assertEqual(list(trace.marker.color), [2010, 2011, 2012])
        expected_scale = plotly.colors.get_colorscale("Viridis")
        self.assertEqual([color for _, color in trace.marker.colorscale],
                         [color for _, color in expected_scale])
        np.testing.assert_allclose([position for position, _ in trace.marker.colorscale],
                                   [position for position, _ in expected_scale])
        self.assertTrue(trace.marker.showscale)
        self.assertEqual(trace.marker.colorbar.title.text, "Year")
        self.assertEqual(trace.textposition, "top center")
        for field in ["%{text}", "%{x:,.0f}", "%{y:.1f}", "%{customdata[0]", "%{customdata[1]", "%{customdata[2]"]:
            self.assertIn(field, trace.hovertemplate)
        self.assertIn("BEV+PHEV", fig.layout.yaxis.title.text)
        self.assertEqual(fig.layout.title.text, "01 · World EV sales volume and BEV share over time")
        self.assertEqual(fig.layout.xaxis.title.text, "Annual electric car sales (EV, vehicles)")
        self.assertEqual(fig.layout.yaxis.title.text, "BEV share of BEV+PHEV sales (%)")
        for label in ["Year:", "EV sales:", "BEV share:", "PHEV share:", "BEV sales:", "PHEV sales:"]:
            self.assertIn(label, trace.hovertemplate)
        self.assertFalse(fig.layout.xaxis.fixedrange)
        self.assertFalse(fig.layout.yaxis.fixedrange)
        self.assertFalse(fig.layout.sliders)
        self.assertFalse(fig.layout.updatemenus)
        self.assertEqual(fig.layout.height, 610)
        self.assertEqual(fig.layout.annotations[0].text, "Latest year")
        self.assertEqual(fig.layout.annotations[0].x, 150)

    def test_exact_filters(self):
        base = fixture()
        extras = []
        for column, value in [("category", "Projection-CPS"), ("region_country", "China"),
                              ("parameter", "EV stock"), ("mode", "Buses"),
                              ("powertrain", "ICEV"), ("year", 2035), ("year", 2009)]:
            row = base.iloc[[0]].copy()
            row[column] = value
            row["value"] = -1
            extras.append(row)
        fig = build_market_connected_scatter(pd.concat([base, *extras], ignore_index=True))
        self.assertEqual(list(fig.data[0].x), [200, 100, 150])

    def test_duplicates_raise(self):
        df = fixture()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            build_market_connected_scatter(pd.concat([df, df.iloc[[0]]]))

    def test_missing_year_or_technology_is_not_filled(self):
        df = fixture()
        for selected in [df.drop(index=4), df.assign(value=df.value.mask(df.index == 4)),
                         df.loc[df.year.ne(2011)]]:
            with self.subTest(rows=len(selected)):
                trace = build_market_connected_scatter(selected).data[0]
                self.assertEqual(list(trace.text), ["2010", "2012"])
                self.assertEqual(list(trace.x), [200, 150])
        self.assertIsNone(build_market_connected_scatter(df.loc[df.powertrain.ne("PHEV")]))
        self.assertIsNone(build_market_connected_scatter(df.iloc[:0]))

    def test_nonpositive_totals_and_component_zero(self):
        df = fixture()
        df.loc[df.year.eq(2010) & df.powertrain.eq("EV"), "value"] = 0
        df.loc[df.year.eq(2011) & df.powertrain.ne("EV"), "value"] = 0
        trace = build_market_connected_scatter(df).data[0]
        self.assertEqual(list(trace.text), ["2012"])
        df["value"] = 0
        self.assertIsNone(build_market_connected_scatter(df))
        for zero_pt, expected in [("BEV", 0), ("PHEV", 100)]:
            df = fixture()
            df.loc[df.powertrain.eq(zero_pt), "value"] = 0
            trace = build_market_connected_scatter(df).data[0]
            np.testing.assert_allclose(trace.y, [expected] * 3)

    def test_invalid_schema_units_values_years(self):
        with self.assertRaisesRegex(ValueError, "Missing required"):
            build_market_connected_scatter(fixture().drop(columns="value"))
        for unit in ["percent", None]:
            df = fixture()
            df.loc[0, "unit"] = unit
            with self.assertRaisesRegex(ValueError, "Vehicles"):
                build_market_connected_scatter(df)
        for value in [-1, np.inf, -np.inf, "invalid"]:
            df = fixture().astype({"value": object})
            df.loc[0, "value"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                build_market_connected_scatter(df)
        for year in [2010.5, np.nan, np.inf, "invalid"]:
            df = fixture().astype({"year": object})
            df.loc[0, "year"] = year
            with self.subTest(year=year), self.assertRaises(ValueError):
                build_market_connected_scatter(df)

    def test_numeric_strings_and_no_mutation(self):
        df = fixture().astype({"year": str, "value": str})
        original = df.copy(deep=True)
        self.assertEqual(list(build_market_connected_scatter(df).data[0].x), [200, 100, 150])
        pd.testing.assert_frame_equal(df, original)


if __name__ == "__main__":
    unittest.main()
