"""Focused tests for country-level BEV–ICEV price-gap violins."""

from pathlib import Path
import unittest

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import plotly.graph_objects as go

from src.charts.violin import PRICE_SEGMENTS, build_price_violin, prepare_price_violin_data


DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "data" / "analysisdataset" / "global_ev_cleaned.csv"
)


def price_row(country, segment, powertrain, value, **changes):
    result = dict(
        region_country=country,
        category="Historical",
        parameter="price_p50_2025USD",
        mode=segment,
        powertrain=powertrain,
        year=2025,
        unit="2025 USD",
        value=value,
        **{"Aggregate group": "Other"},
    )
    result.update(changes)
    return result


def fixture():
    rows = []
    for country_index, country in enumerate(["Alpha", "Beta", "Gamma", "Delta"]):
        for segment_index, segment in enumerate(PRICE_SEGMENTS):
            icev = 20_000 + 1_000 * country_index + 2_000 * segment_index
            gap = 10 * (country_index + 1) + segment_index
            group = "Projection_country" if country == "Beta" else "Other"
            rows.extend([
                price_row(
                    country, segment, "BEV", icev * (1 + gap / 100),
                    **{"Aggregate group": group},
                ),
                price_row(
                    country, segment, "ICEV", icev,
                    **{"Aggregate group": group},
                ),
            ])
    rows.extend([
        price_row("Partialia", "City car", "BEV", 30_000),
        price_row("World", "City car", "BEV", 999_999,
                  **{"Aggregate group": "_World"}),
        price_row("Alpha", "City car", "BEV", 999_999, year=2024),
        price_row("Alpha", "City car", "BEV", 999_999,
                  category="Projection-STEPS"),
        price_row("Alpha", "All cars", "BEV", 999_999),
    ])
    return pd.DataFrame(rows)


class ViolinTests(unittest.TestCase):
    def test_prepare_filters_pairs_and_calculates_gap(self):
        data = prepare_price_violin_data(fixture())

        self.assertEqual(len(data), 20)
        self.assertEqual(data["region_country"].nunique(), 4)
        self.assertNotIn("World", data["region_country"].tolist())
        self.assertNotIn("Partialia", data["region_country"].tolist())
        alpha = data.loc[
            data["region_country"].eq("Alpha") & data["mode"].eq("City car")
        ].iloc[0]
        self.assertAlmostEqual(alpha["BEV_median"], 22_000)
        self.assertAlmostEqual(alpha["ICEV_median"], 20_000)
        self.assertAlmostEqual(alpha["price_gap_pct"], 10)

    def test_duplicate_is_rejected(self):
        data = fixture()
        duplicate = data.loc[
            data["region_country"].eq("Alpha")
            & data["mode"].eq("City car")
            & data["powertrain"].eq("BEV")
            & data["year"].eq(2025)
            & data["category"].eq("Historical")
        ].iloc[[0]]
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            prepare_price_violin_data(pd.concat([data, duplicate], ignore_index=True))

    def test_missing_and_nonpositive_pairs_are_excluded(self):
        data = fixture()
        data.loc[
            data["region_country"].eq("Alpha")
            & data["mode"].eq("City car")
            & data["powertrain"].eq("ICEV"),
            "value",
        ] = 0
        data.loc[
            data["region_country"].eq("Beta")
            & data["mode"].eq("Medium car")
            & data["powertrain"].eq("BEV"),
            "value",
        ] = np.nan

        prepared = prepare_price_violin_data(data)

        self.assertEqual(len(prepared), 18)
        self.assertTrue(prepared["ICEV_median"].gt(0).all())
        self.assertTrue(np.isfinite(prepared["price_gap_pct"]).all())

    def test_invalid_schema_units_values_segments_and_year(self):
        with self.assertRaisesRegex(ValueError, "Missing required"):
            prepare_price_violin_data(fixture().drop(columns="unit"))

        bad_unit = fixture()
        bad_unit.loc[0, "unit"] = "USD"
        with self.assertRaisesRegex(ValueError, "2025 USD"):
            prepare_price_violin_data(bad_unit)

        bad_value = fixture().astype({"value": object})
        bad_value.loc[0, "value"] = "invalid"
        with self.assertRaises(ValueError):
            prepare_price_violin_data(bad_value)

        with self.assertRaisesRegex(ValueError, "Unsupported"):
            prepare_price_violin_data(fixture(), ["All cars"])
        with self.assertRaisesRegex(ValueError, "integer year"):
            prepare_price_violin_data(fixture(), year=2025.5)
        self.assertIsNone(build_price_violin(fixture(), []))

    def test_subset_order_input_and_figure_contract(self):
        source = fixture()
        original = source.copy(deep=True)
        fig = build_price_violin(
            source,
            ["Large SUV/Pick-up", "Medium car"],
        )

        self.assertIsInstance(fig, go.Figure)
        self.assertEqual([trace.name for trace in fig.data], [
            "Medium car", "Large SUV/Pick-up",
        ])
        self.assertEqual(fig.layout.meta["observation_count"], 8)
        self.assertEqual(fig.layout.meta["segment_counts"], {
            "Medium car": 4, "Large SUV/Pick-up": 4,
        })
        for trace in fig.data:
            self.assertEqual(trace.type, "violin")
            self.assertTrue(trace.box.visible)
            self.assertEqual(trace.points, "all")
            self.assertEqual(trace.hoveron, "points")
            for field in ["customdata[0]", "customdata[1]", "customdata[2]"]:
                self.assertIn(field, trace.hovertemplate)
        self.assertEqual(fig.layout.shapes[0].y0, 0)
        assert_frame_equal(source, original)
        fig.to_json()

    def test_real_csv_contract(self):
        data = pd.read_csv(DATA_PATH)
        prepared = prepare_price_violin_data(data)

        self.assertEqual(len(prepared), 50)
        self.assertEqual(prepared["region_country"].nunique(), 10)
        self.assertEqual(
            prepared.groupby("mode")["region_country"].nunique().to_dict(),
            {segment: 10 for segment in PRICE_SEGMENTS},
        )
        self.assertLess(prepared["price_gap_pct"].min(), -70)
        self.assertGreater(prepared["price_gap_pct"].max(), 500)

        fig = build_price_violin(data)
        self.assertEqual(len(fig.data), 5)
        self.assertEqual(sum(len(trace.y) for trace in fig.data), 50)


if __name__ == "__main__":
    unittest.main()
