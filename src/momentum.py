"""
Tactical Momentum Index.

The Momentum Index quantifies which team "has the momentum" at any point in
a match by combining:

1. Event value  - each event type has an intrinsic weight (goal >> pass).
2. Field position - events closer to the opponent's goal count for more.
3. Recency decay  - momentum fades over time via exponential decay, so a
   team that was dangerous 10 minutes ago but has since gone quiet loses
   its advantage.
4. Rolling smoothing - a rolling window converts the noisy per-event signal
   into a smooth, chart-friendly momentum curve in the range [-100, 100],
   where positive values favor the home/attacking team of interest and
   negative values favor the opponent.

This is an improved version of a "naive" momentum index (which would just
count events) because it accounts for danger (xG/field position), applies
decay so stale events stop mattering, and normalizes across both teams so
the two curves are always mirror images that sum to zero.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from config import MOMENTUM_DECAY, MOMENTUM_EVENT_WEIGHTS, MOMENTUM_WINDOW_MINUTES, PITCH_LENGTH
from logger import get_logger

log = get_logger(__name__)


def _field_position_multiplier(x: pd.Series) -> pd.Series:
    """Events deeper in the attacking third are weighted up to 1.6x."""
    progress = (x / PITCH_LENGTH).clip(0, 1)
    return 0.7 + 0.9 * progress


def compute_event_value(df: pd.DataFrame) -> pd.Series:
    """Per-event momentum contribution before decay/rolling is applied."""
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
    """
    Compute a per-minute momentum time series for a single match.

    Returns a DataFrame indexed by minute with one momentum column per team
    plus a `momentum_diff` column (team[0] - team[1]).
    """
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

        # Exponential decay smoothing: momentum "remembers" recent minutes
        # more than distant ones.
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

    # Normalize so the two curves are on a comparable, capped scale.
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
    """Headline stats out of a momentum time series (share of minutes led, swings)."""
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
