"""Focused tests for the EV-mode parallel-coordinates chart."""

from pathlib import Path
import unittest

import pandas as pd
from pandas.testing import assert_frame_equal
import plotly.graph_objects as go

from src.charts.parallel_coordinates import MODE_COLORS, PCP_MODES, build_ev_mode_pcp


DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "data" / "analysisdataset" / "global_ev_cleaned.csv"
)


def fixture() -> pd.DataFrame:
    starts = dict(zip(PCP_MODES, [5.0, 10.0, 2.0, 3.0, 20.0]))
    changes = dict(zip(PCP_MODES, [2.0, -0.2, 1.0, 0.5, 0.0]))
    rows = [
        dict(
            region_country="World", category="Historical",
            parameter="EV sales share", mode=mode, powertrain="EV",
            year=year, unit="percent",
            value=starts[mode] + changes[mode] * (year - 2020),
        )
        for mode in PCP_MODES
        for year in range(2020, 2026)
    ]
    rows.extend([
        {**rows[0], "region_country": "China"},
        {**rows[0], "category": "Projection-STEPS"},
        {**rows[0], "parameter": "EV stock share"},
        {**rows[0], "powertrain": "BEV"},
        {**rows[0], "mode": "All cars"},
    ])
    return pd.DataFrame(rows)


class ParallelCoordinatesTests(unittest.TestCase):
    def test_figure_dimensions_colors_and_changes(self):
        fig = build_ev_mode_pcp(fixture())

        self.assertIsInstance(fig, go.Figure)
        trace = fig.data[0]
        self.assertEqual(trace.type, "parcoords")
        self.assertEqual([d.label for d in trace.dimensions], [
            "2020", "2021", "2022", "2023", "2024", "2025",
        ])
        for dimension in trace.dimensions:
            self.assertEqual(tuple(dimension.range), (0, 100))
            self.assertEqual(len(dimension.values), 5)
            # Custom ticks made Plotly treat brushed axes as ordinal.
            self.assertIsNone(dimension.tickvals)
            self.assertIsNone(dimension.ticktext)
        self.assertEqual(tuple(trace.line.colorbar.ticktext), PCP_MODES)
        self.assertEqual(
            {stop[1] for stop in trace.line.colorscale},
            set(MODE_COLORS.values()),
        )
        self.assertAlmostEqual(fig.layout.meta["change_pp"]["Cars"], 10)
        self.assertAlmostEqual(fig.layout.meta["change_pp"]["Buses"], -1)
        self.assertAlmostEqual(fig.layout.meta["average_pp_per_year"]["Cars"], 2)
        self.assertEqual(
            fig.layout.meta["brushing_status"],
            "manual browser verification required",
        )
        fig.to_json()

    def test_exact_filters_and_input_are_preserved(self):
        data = fixture()
        original = data.copy(deep=True)

        fig = build_ev_mode_pcp(data)

        self.assertEqual(list(fig.data[0].dimensions[0].values), [5, 10, 2, 3, 20])
        assert_frame_equal(data, original)

    def test_incomplete_modes_are_excluded_without_zero_filling(self):
        data = fixture()
        missing = (
            data["region_country"].eq("World")
            & data["mode"].eq("Trucks")
            & data["year"].eq(2023)
        )
        fig = build_ev_mode_pcp(data.loc[~missing].copy())

        self.assertEqual(fig.layout.meta["excluded_modes"], ["Trucks"])
        self.assertTrue(all(len(d.values) == 4 for d in fig.data[0].dimensions))
        self.assertTrue(all(0 not in d.values for d in fig.data[0].dimensions))

        keep_cars = data["mode"].eq("Cars") | ~data["mode"].isin(PCP_MODES)
        self.assertIsNone(build_ev_mode_pcp(data.loc[keep_cars].copy()))

    def test_duplicate_is_rejected(self):
        data = fixture()
        row = data.loc[
            data["region_country"].eq("World")
            & data["mode"].eq("Cars")
            & data["year"].eq(2020)
        ].iloc[[0]]
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            build_ev_mode_pcp(pd.concat([data, row], ignore_index=True))

    def test_invalid_schema_units_values_and_years(self):
        with self.assertRaisesRegex(ValueError, "Missing required"):
            build_ev_mode_pcp(fixture().drop(columns="unit"))

        bad_unit = fixture()
        bad_unit.loc[0, "unit"] = "Vehicles"
        with self.assertRaisesRegex(ValueError, "percent"):
            build_ev_mode_pcp(bad_unit)

        for value in [101, -1, "invalid"]:
            data = fixture().astype({"value": object})
            data.loc[0, "value"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                build_ev_mode_pcp(data)

        for start, end in [(2025, 2025), (2025.5, 2026), (True, 2025)]:
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                build_ev_mode_pcp(fixture(), start, end)

    def test_shorter_year_range(self):
        fig = build_ev_mode_pcp(fixture(), 2021, 2023)
        self.assertEqual([d.label for d in fig.data[0].dimensions], [
            "2021", "2022", "2023",
        ])
        self.assertAlmostEqual(fig.layout.meta["change_pp"]["Cars"], 4)

    def test_real_csv_contract(self):
        data = pd.read_csv(DATA_PATH)
        selected = data.loc[
            data["category"].eq("Historical")
            & data["region_country"].eq("World")
            & data["parameter"].eq("EV sales share")
            & data["powertrain"].eq("EV")
            & data["mode"].isin(PCP_MODES)
            & data["year"].between(2020, 2025)
        ]
        self.assertEqual(len(selected), 30)
        self.assertFalse(selected.duplicated(["mode", "year"]).any())

        fig = build_ev_mode_pcp(data)
        self.assertEqual(len(fig.data[0].dimensions), 6)
        self.assertEqual(fig.layout.meta["excluded_modes"], [])
        expected = dict(zip(PCP_MODES, [20.6, -0.2, 8.69, 3.3, 0.0]))
        for mode, change in expected.items():
            self.assertAlmostEqual(fig.layout.meta["change_pp"][mode], change)


if __name__ == "__main__":
    unittest.main()
