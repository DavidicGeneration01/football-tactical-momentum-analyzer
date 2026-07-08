"""Clean raw event data."""

from __future__ import annotations

import pandas as pd

from config import PITCH_LENGTH, PITCH_WIDTH, PROCESSED_EVENTS_CSV, PROCESSED_EVENTS_FILE
from logger import get_logger

log = get_logger(__name__)

REQUIRED_COLUMNS = {
    "event_id", "match_id", "team", "opponent", "player", "minute",
    "second", "event_type", "x", "y", "outcome", "xg",
}


def validate_schema(df: pd.DataFrame) -> None:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Raw data is missing required columns: {sorted(missing)}")


def clean_events(df: pd.DataFrame) -> pd.DataFrame:
    validate_schema(df)
    before = len(df)

    df = df.drop_duplicates(subset="event_id").copy()

    numeric_cols = ["minute", "second", "x", "y", "xg", "match_id"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    text_cols = ["team", "opponent", "player", "event_type", "outcome"]
    for col in text_cols:
        df[col] = df[col].astype(str).str.strip()

    # no use keeping rows that cannot be placed on the pitch
    df = df.dropna(subset=["minute", "x", "y", "event_type", "team"])

    df["x"] = df["x"].clip(0, PITCH_LENGTH)
    df["y"] = df["y"].clip(0, PITCH_WIDTH)
    df["xg"] = df["xg"].fillna(0).clip(0, 1)

    # let stoppage time breathe a bit
    df = df[(df["minute"] >= 0) & (df["minute"] <= 100)]

    df["match_seconds"] = df["minute"] * 60 + df["second"].fillna(0)

    df = df.sort_values(["match_id", "match_seconds"]).reset_index(drop=True)

    after = len(df)
    log.info("Cleaned events: %d -> %d rows (%d dropped)", before, after, before - after)
    return df


def save_processed(df: pd.DataFrame) -> None:
    PROCESSED_EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        df.to_parquet(PROCESSED_EVENTS_FILE, index=False)
        log.info("Saved processed parquet to %s", PROCESSED_EVENTS_FILE)
    except Exception as exc:  # pragma: no cover - parquet engine may be missing
        log.warning("Parquet save failed (%s); falling back to CSV only", exc)
    df.to_csv(PROCESSED_EVENTS_CSV, index=False)
    log.info("Saved processed CSV to %s", PROCESSED_EVENTS_CSV)


def load_processed() -> pd.DataFrame:
    if PROCESSED_EVENTS_FILE.exists():
        return pd.read_parquet(PROCESSED_EVENTS_FILE)
    return pd.read_csv(PROCESSED_EVENTS_CSV)
