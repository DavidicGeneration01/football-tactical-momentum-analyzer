# Modules.

from __future__ import annotations

import functools
import time
from typing import Any, Callable, TypeVar

import pandas as pd

from logger import get_logger

log = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def timer(func: F) -> F:

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        log.info("%s completed in %.3fs", func.__name__, elapsed)
        return result

    return wrapper  # type: ignore[return-value]


def minute_to_clock(minute: int, second: int = 0) -> str:
    if minute > 90:
        return f"90+{minute - 90}'"
    return f"{minute}'"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    return numerator / denominator if denominator else default


def normalize_series(series: pd.Series) -> pd.Series:
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series(0.5, index=series.index)
    return (series - lo) / (hi - lo)


def team_pair(df: pd.DataFrame, match_id: int) -> tuple[str, str]:
    row = df[df["match_id"] == match_id].iloc[0]
    return row["home_team"], row["away_team"]


def list_matches(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df[["match_id", "home_team", "away_team"]]
        .drop_duplicates()
        .sort_values("match_id")
        .reset_index(drop=True)
    )
