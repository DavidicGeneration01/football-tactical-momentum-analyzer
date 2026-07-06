import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cleaner import clean_events, validate_schema  # noqa: E402
from data_loader import generate_synthetic_events  # noqa: E402


@pytest.fixture(scope="module")
def raw_events() -> pd.DataFrame:
    return generate_synthetic_events(n_events=800, n_matches=2, seed=2)


def test_validate_schema_passes_on_good_data(raw_events: pd.DataFrame) -> None:
    validate_schema(raw_events)  # should not raise


def test_validate_schema_raises_on_missing_columns() -> None:
    bad_df = pd.DataFrame({"team": ["A"]})
    with pytest.raises(ValueError):
        validate_schema(bad_df)


def test_clean_events_deduplicates(raw_events: pd.DataFrame) -> None:
    doubled = pd.concat([raw_events, raw_events.iloc[:20]], ignore_index=True)
    cleaned = clean_events(doubled)
    assert cleaned["event_id"].is_unique


def test_clean_events_clips_coordinates() -> None:
    df = pd.DataFrame(
        {
            "event_id": [1, 2],
            "match_id": [1, 1],
            "team": ["A", "A"],
            "opponent": ["B", "B"],
            "player": ["P1", "P2"],
            "minute": [10, 20],
            "second": [0, 0],
            "event_type": ["Pass", "Shot"],
            "x": [-10, 500],
            "y": [-5, 999],
            "outcome": ["Complete", "On Target"],
            "xg": [0.1, 2.0],
        }
    )
    cleaned = clean_events(df)
    assert cleaned["x"].between(0, 120).all()
    assert cleaned["y"].between(0, 80).all()
    assert cleaned["xg"].between(0, 1).all()


def test_clean_events_adds_match_seconds(raw_events: pd.DataFrame) -> None:
    cleaned = clean_events(raw_events)
    assert "match_seconds" in cleaned.columns
    assert (cleaned["match_seconds"] >= 0).all()


def test_clean_events_drops_bad_minutes() -> None:
    df = pd.DataFrame(
        {
            "event_id": [1, 2],
            "match_id": [1, 1],
            "team": ["A", "A"],
            "opponent": ["B", "B"],
            "player": ["P1", "P2"],
            "minute": [10, 500],
            "second": [0, 0],
            "event_type": ["Pass", "Shot"],
            "x": [10, 10],
            "y": [10, 10],
            "outcome": ["Complete", "On Target"],
            "xg": [0.1, 0.2],
        }
    )
    cleaned = clean_events(df)
    assert len(cleaned) == 1
