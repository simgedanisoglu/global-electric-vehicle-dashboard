
import pandas as pd

from src.charts.sunburst import (
    PARAMETER_GROUPS,
    prepare_sunburst_data,
    build_sunburst,
)
from src.charts.rank_dumbbell import (
    prepare_rank_dumbbell_data,
    build_rank_dumbbell,
)
from src.charts.sankey import (
    prepare_energy_transition_data,
    build_energy_transition_sankey,
)


DATA_PATH = "data/analysisdataset/global_ev_cleaned.csv"


def load_data():
    return pd.read_csv(DATA_PATH)


def test_sunburst():
    df = load_data()

    for group in PARAMETER_GROUPS:
        prepared = prepare_sunburst_data(df, group)

        assert not prepared.empty
        assert not prepared.duplicated(
            ["parameter", "mode", "powertrain"]
        ).any()

        fig = build_sunburst(df, group)
        assert fig is not None


def test_rank_dumbbell():
    df = load_data()

    prepared = prepare_rank_dumbbell_data(
        df, year=2025, top_n=12
    )

    assert not prepared.empty
    assert prepared["region_country"].is_unique

    assert prepared["sales_rank"].ge(1).all()
    assert prepared["share_rank"].ge(1).all()

    assert (
        prepared["rank_gap"]
        == prepared["share_rank"] - prepared["sales_rank"]
    ).all()

    fig = build_rank_dumbbell(
        df, year=2025, top_n=12
    )
    assert fig is not None


def test_sankey():
    df = load_data()

    prepared, thresholds = prepare_energy_transition_data(df)

    assert not prepared.empty
    assert prepared["region_country"].is_unique

    assert thresholds[0] <= thresholds[1]

    fig = build_energy_transition_sankey(df)
    assert fig is not None

    # Each matched country must appear once
    assert sum(fig.data[0].link.value) == len(prepared)
