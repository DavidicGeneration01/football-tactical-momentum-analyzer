import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cleaner import clean_events  # noqa: E402
from data_loader import generate_synthetic_events  # noqa: E402
from momentum import compute_event_value, compute_momentum_index, momentum_summary  # noqa: E402


@pytest.fixture(scope="module")
def cleaned_events() -> pd.DataFrame:
    raw = generate_synthetic_events(n_events=1500, n_matches=2, seed=3)
    return clean_events(raw)


def test_compute_event_value_goal_scores_highest(cleaned_events: pd.DataFrame) -> None:
    values = compute_event_value(cleaned_events)
    goal_mask = cleaned_events["event_type"] == "Goal"
    pass_mask = cleaned_events["event_type"] == "Pass"
    if goal_mask.any() and pass_mask.any():
        assert values[goal_mask].mean() > values[pass_mask].mean()


def test_momentum_index_has_expected_columns(cleaned_events: pd.DataFrame) -> None:
    match_id = int(cleaned_events["match_id"].iloc[0])
    result = compute_momentum_index(cleaned_events, match_id=match_id)
    assert "minute" in result.columns
    assert "momentum_diff" in result.columns
    assert "leader" in result.columns


def test_momentum_index_bounded(cleaned_events: pd.DataFrame) -> None:
    match_id = int(cleaned_events["match_id"].iloc[0])
    result = compute_momentum_index(cleaned_events, match_id=match_id)
    teams = [c for c in result.columns if c not in ("minute", "momentum_diff", "leader")]
    for team in teams:
        assert result[team].abs().max() <= 100.01


def test_momentum_index_raises_on_missing_match(cleaned_events: pd.DataFrame) -> None:
    with pytest.raises(ValueError):
        compute_momentum_index(cleaned_events, match_id=999999)


def test_momentum_summary_shares_sum_to_total(cleaned_events: pd.DataFrame) -> None:
    match_id = int(cleaned_events["match_id"].iloc[0])
    result = compute_momentum_index(cleaned_events, match_id=match_id)
    teams = sorted(cleaned_events[cleaned_events["match_id"] == match_id]["team"].unique())
    if len(teams) == 2:
        summary = momentum_summary(result, teams[0], teams[1])
        total = (
            summary[f"{teams[0]}_minutes_led"]
            + summary[f"{teams[1]}_minutes_led"]
            + summary["even_minutes"]
        )
        assert total == summary["total_minutes"]
