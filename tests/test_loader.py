import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from data_loader import generate_synthetic_events  # noqa: E402


@pytest.fixture(scope="module")
def events() -> pd.DataFrame:
    return generate_synthetic_events(n_events=1000, n_matches=2, seed=1)


def test_generates_minimum_row_count(events: pd.DataFrame) -> None:
    assert len(events) >= 800  # per_match floor guarantees a healthy minimum


def test_has_required_columns(events: pd.DataFrame) -> None:
    required = {
        "event_id", "match_id", "team", "opponent", "player", "minute",
        "second", "event_type", "x", "y", "outcome", "xg",
    }
    assert required.issubset(set(events.columns))


def test_coordinates_within_pitch_bounds(events: pd.DataFrame) -> None:
    assert events["x"].between(0, 120).all()
    assert events["y"].between(0, 80).all()


def test_xg_within_probability_bounds(events: pd.DataFrame) -> None:
    assert events["xg"].between(0, 1).all()


def test_event_ids_are_unique(events: pd.DataFrame) -> None:
    assert events["event_id"].is_unique


def test_two_matches_generated(events: pd.DataFrame) -> None:
    assert events["match_id"].nunique() == 2
