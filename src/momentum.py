"""Tactical Momentum Index."""

from __future__ import annotations

import numpy as np
import pandas as pd

from config import MOMENTUM_DECAY, MOMENTUM_EVENT_WEIGHTS, MOMENTUM_WINDOW_MINUTES, PITCH_LENGTH
from logger import get_logger

log = get_logger(__name__)


def _field_position_multiplier(x: pd.Series) -> pd.Series:
    progress = (x / PITCH_LENGTH).clip(0, 1)
    return 0.7 + 0.9 * progress


def compute_event_value(df: pd.DataFrame) -> pd.Series:
    base_weight = df["event_type"].map(MOMENTUM_EVENT_WEIGHTS).fillna(0.0)
    position_mult = _field_position_multiplier(df["x"])
    xg_bonus = df.get("xg", pd.Series(0, index=df.index)).fillna(0) * 8.0
    value = base_weight * position_mult + xg_bonus
    return value


def compute_momentum_index(
    df: pd.DataFrame,
    match_id: int | None = None,
    window_minutes: int = MOMENTUM_WINDOW_MINUTES,
    decay: float = MOMENTUM_DECAY,
) -> pd.DataFrame:
    data = df if match_id is None else df[df["match_id"] == match_id]
    if data.empty:
        raise ValueError("No events found for the requested match_id")

    teams = sorted(data["team"].unique())
    if len(teams) != 2:
        log.warning("Expected 2 teams, found %d: %s", len(teams), teams)

    data = data.copy()
    data["event_value"] = compute_event_value(data)

    max_minute = int(data["minute"].max()) + 1
    minutes = np.arange(0, max_minute + 1)

    team_series = {}
    for team in teams:
        team_events = data[data["team"] == team]
        per_minute = team_events.groupby("minute")["event_value"].sum()
        per_minute = per_minute.reindex(minutes, fill_value=0.0)

        # recent minutes matter more than old pressure
        decayed = np.zeros(len(per_minute))
        running = 0.0
        for i, val in enumerate(per_minute.values):
            running = running * decay + val
            decayed[i] = running

        rolled = pd.Series(decayed, index=minutes).rolling(
            window=window_minutes, min_periods=1
        ).mean()
        team_series[team] = rolled

    result = pd.DataFrame(team_series)
    result.index.name = "minute"

    # keep the chart scale readable
    max_abs = result.abs().to_numpy().max() or 1.0
    scale = 100.0 / max_abs
    result = (result * scale).round(2)

    if len(teams) == 2:
        result["momentum_diff"] = (result[teams[0]] - result[teams[1]]).round(2)
        result["leader"] = np.where(
            result["momentum_diff"] > 0, teams[0],
            np.where(result["momentum_diff"] < 0, teams[1], "Even"),
        )

    log.info(
        "Computed momentum index for match %s over %d minutes",
        match_id if match_id is not None else "ALL",
        max_minute,
    )
    return result.reset_index()


def momentum_summary(momentum_df: pd.DataFrame, team_a: str, team_b: str) -> dict:
    total_minutes = len(momentum_df)
    a_minutes = int((momentum_df["leader"] == team_a).sum())
    b_minutes = int((momentum_df["leader"] == team_b).sum())
    even_minutes = total_minutes - a_minutes - b_minutes

    swings = int((momentum_df["leader"] != momentum_df["leader"].shift()).sum() - 1)
    peak_a = float(momentum_df[team_a].max())
    peak_b = float(momentum_df[team_b].max())

    return {
        "total_minutes": total_minutes,
        f"{team_a}_minutes_led": a_minutes,
        f"{team_b}_minutes_led": b_minutes,
        "even_minutes": even_minutes,
        f"{team_a}_share_pct": round(100 * a_minutes / total_minutes, 1) if total_minutes else 0,
        f"{team_b}_share_pct": round(100 * b_minutes / total_minutes, 1) if total_minutes else 0,
        "lead_changes": max(swings, 0),
        f"{team_a}_peak_momentum": round(peak_a, 1),
        f"{team_b}_peak_momentum": round(peak_b, 1),
    }
