"""Focused tests for the national EV charging SPLOM."""

from pathlib import Path
import unittest

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import plotly.graph_objects as go

from src.charts.splom import (
    PUBLIC_CHARGER_TYPES,
    SPLOM_DIMENSIONS,
    build_charging_splom,
    prepare_charging_splom_data,
)


DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "data" / "analysisdataset" / "global_ev_cleaned.csv"
)


def row(country, parameter, mode, powertrain, value, unit, **changes):
    result = dict(
        region_country=country,
        category="Historical",
        parameter=parameter,
        mode=mode,
        powertrain=powertrain,
        year=2025,
        unit=unit,
        value=value,
        **{"Aggregate group": "Other"},
    )
    result.update(changes)
    return result


def country_rows(country, stock, share, chargers=(100.0, 10.0, 1.0), group="Other"):
    rows = [
        row(country, "EV stock", "Cars", "EV", stock, "Vehicles"),
        row(country, "EV sales share", "Cars", "EV", share, "percent"),
    ]
    rows.extend(
        row(
            country, "EV charging points", "EVSE", charger_type,
            value, "charging points",
        )
        for charger_type, value in zip(PUBLIC_CHARGER_TYPES, chargers, strict=True)
    )
    for item in rows:
        item["Aggregate group"] = group
    return rows


def fixture():
    rows = []
    for index, country in enumerate(["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]):
        rows.extend(country_rows(
            country,
            stock=1_000 * (index + 1),
            share=10 * (index + 1),
            chargers=(100 * (index + 1), 10, 1),
            group="Projection_country" if country == "Beta" else "Other",
        ))
    rows.extend(country_rows("Partialia", 2_500, 25)[:-1])
    rows.extend(country_rows("NoCharge", 3_000, 30)[:2])
    rows.extend([
        row("World", "EV stock", "Cars", "EV", 999_999, "Vehicles",
            **{"Aggregate group": "_World"}),
        row("Alpha", "EV stock", "Cars", "EV", 999_999, "Vehicles", year=2024),
        row("Alpha", "EV stock", "Cars", "EV", 999_999, "Vehicles",
            category="Projection-STEPS"),
    ])
    return pd.DataFrame(rows)


class SplomTests(unittest.TestCase):
    def test_prepare_filters_matches_and_calculates(self):
        profile = prepare_charging_splom_data(fixture())

        self.assertEqual(profile["region_country"].tolist(), [
            "Alpha", "Beta", "Delta", "Epsilon", "Gamma",
        ])
        alpha = profile.set_index("region_country").loc["Alpha"]
        self.assertAlmostEqual(alpha["Public_chargers"], 111)
        self.assertAlmostEqual(alpha["Cars_per_point"], 1_000 / 111)
        self.assertAlmostEqual(alpha["log_EV_stock"], 3)
        self.assertAlmostEqual(alpha["log_Public_chargers"], np.log10(111))
        self.assertEqual(profile.attrs["incomplete_charger_countries"], ["Partialia"])
        self.assertEqual(profile.attrs["no_charger_record_countries"], ["NoCharge"])
        self.assertFalse(profile.duplicated(["region_country", "year"]).any())

    def test_duplicate_metric_records_are_rejected(self):
        base = fixture()
        masks = [
            base["parameter"].eq("EV stock") & base["region_country"].eq("Alpha"),
            base["parameter"].eq("EV sales share") & base["region_country"].eq("Alpha"),
            base["parameter"].eq("EV charging points")
            & base["region_country"].eq("Alpha")
            & base["powertrain"].eq(PUBLIC_CHARGER_TYPES[0]),
        ]
        for mask in masks:
            duplicate = base.loc[mask].iloc[[0]]
            with self.subTest(parameter=duplicate.iloc[0]["parameter"]):
                with self.assertRaisesRegex(ValueError, "Duplicate"):
                    prepare_charging_splom_data(
                        pd.concat([base, duplicate], ignore_index=True)
                    )

    def test_missing_and_nonpositive_values_are_not_zero_filled(self):
        data = fixture()
        data = pd.concat([
            data,
            pd.DataFrame(
                country_rows("ZeroStock", 0, 20)
                + country_rows("ZeroChargers", 1_000, 20, (0, 0, 0))
            ),
        ], ignore_index=True)
        profile = prepare_charging_splom_data(data)

        self.assertNotIn("Partialia", profile["region_country"].tolist())
        self.assertNotIn("ZeroStock", profile["region_country"].tolist())
        self.assertNotIn("ZeroChargers", profile["region_country"].tolist())
        self.assertTrue(np.isfinite(profile[list(SPLOM_DIMENSIONS)]).all().all())

    def test_invalid_schema_units_values_share_and_year(self):
        with self.assertRaisesRegex(ValueError, "Missing required"):
            prepare_charging_splom_data(fixture().drop(columns="unit"))

        bad_unit = fixture()
        bad_unit.loc[bad_unit["parameter"].eq("EV charging points"), "unit"] = "stations"
        with self.assertRaisesRegex(ValueError, "charging points"):
            prepare_charging_splom_data(bad_unit)

        bad_value = fixture().astype({"value": object})
        bad_value.loc[0, "value"] = "invalid"
        with self.assertRaises(ValueError):
            prepare_charging_splom_data(bad_value)

        bad_share = fixture()
        bad_share.loc[bad_share["parameter"].eq("EV sales share"), "value"] = 101
        with self.assertRaisesRegex(ValueError, "between 0 and 100"):
            prepare_charging_splom_data(bad_share)

        with self.assertRaisesRegex(ValueError, "integer year"):
            prepare_charging_splom_data(fixture(), year=2025.5)

    def test_figure_has_four_linked_dimensions_hover_and_selection(self):
        fig = build_charging_splom(fixture())

        self.assertIsInstance(fig, go.Figure)
        trace = fig.data[0]
        self.assertEqual(trace.type, "splom")
        self.assertEqual(len(trace.dimensions), 4)
        self.assertEqual(list(trace.ids), ["Alpha", "Beta", "Delta", "Epsilon", "Gamma"])
        self.assertEqual(len(trace.customdata), 5)
        self.assertEqual(list(trace.customdata[0]), ["Alpha", 1_000, 111, 10])
        self.assertEqual(trace.marker.cmin, 0)
        self.assertEqual(trace.marker.cmax, 100)
        self.assertEqual(fig.layout.dragmode, "select")
        self.assertEqual(trace.selected.marker.opacity, 1)
        self.assertEqual(trace.unselected.marker.opacity, 0.18)
        for field in ["customdata[0]", "customdata[1]", "customdata[2]", "customdata[3]"]:
            self.assertIn(field, trace.hovertemplate)
        self.assertEqual(
            fig.layout.meta["selection_status"],
            "manual browser verification required",
        )
        fig.to_json()

    def test_fewer_than_four_countries_returns_none_and_input_is_unchanged(self):
        data = fixture()
        original = data.copy(deep=True)
        keep = data["region_country"].isin(["Alpha", "Beta", "Gamma"])

        self.assertIsNone(build_charging_splom(data.loc[keep].copy()))
        build_charging_splom(data)
        assert_frame_equal(data, original)

    def test_real_csv_contract(self):
        data = pd.read_csv(DATA_PATH)
        profile = prepare_charging_splom_data(data)

        self.assertEqual(len(profile), 33)
        self.assertEqual(profile["region_country"].nunique(), 33)
        self.assertEqual(len(profile.attrs["incomplete_charger_countries"]), 10)
        self.assertEqual(
            profile.attrs["no_charger_record_countries"],
            ["Cambodia", "Lao PDR", "Uzbekistan"],
        )
        fig = build_charging_splom(data)
        self.assertEqual(len(fig.data[0].ids), 33)
        self.assertGreater(fig.layout.meta["spearman_ev_stock_public_chargers"], 0.9)


if __name__ == "__main__":
    unittest.main()
