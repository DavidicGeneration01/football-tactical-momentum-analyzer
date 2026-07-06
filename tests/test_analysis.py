import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from analysis import (  # noqa: E402
    add_xt_column,
    correlation_matrix,
    match_ratings,
    performance_summary,
    team_match_stats,
    team_ratings,
    xt_value,
)
from cleaner import clean_events  # noqa: E402
from data_loader import generate_synthetic_events  # noqa: E402


@pytest.fixture(scope="module")
def cleaned_events() -> pd.DataFrame:
    raw = generate_synthetic_events(n_events=1500, n_matches=3, seed=4)
    return clean_events(raw)


@pytest.fixture(scope="module")
def stats(cleaned_events: pd.DataFrame) -> pd.DataFrame:
    return team_match_stats(cleaned_events)


def test_team_match_stats_row_per_team_match(cleaned_events: pd.DataFrame, stats: pd.DataFrame) -> None:
    expected_rows = cleaned_events.groupby(["match_id", "team"]).ngroups
    assert len(stats) == expected_rows


def test_possession_sums_to_100_per_match(stats: pd.DataFrame) -> None:
    totals = stats.groupby("match_id")["possession_pct"].sum()
    assert (totals.round(0) == 100).all()


def test_performance_summary_has_one_row_per_team(stats: pd.DataFrame) -> None:
    summary = performance_summary(stats)
    assert summary["team"].is_unique


def test_team_ratings_bounded(stats: pd.DataFrame) -> None:
    ratings = team_ratings(stats)
    assert ratings["team_rating"].between(0, 100).all()


def test_match_ratings_one_row_per_match(stats: pd.DataFrame) -> None:
    mr = match_ratings(stats)
    assert mr["match_id"].is_unique


def test_correlation_matrix_is_symmetric(stats: pd.DataFrame) -> None:
    corr = correlation_matrix(stats)
    assert (corr.values == corr.values.T).all()


def test_xt_value_increases_toward_goal() -> None:
    deep_value = xt_value(10, 40)
    attacking_value = xt_value(115, 40)
    assert attacking_value > deep_value


def test_add_xt_column(cleaned_events: pd.DataFrame) -> None:
    df_xt = add_xt_column(cleaned_events)
    assert "xt" in df_xt.columns
    assert df_xt["xt"].between(0, 1).all()
