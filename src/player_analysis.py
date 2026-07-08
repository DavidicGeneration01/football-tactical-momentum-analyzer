"""Player ratings and comparison tables."""

from __future__ import annotations

import numpy as np
import pandas as pd

from logger import get_logger

log = get_logger(__name__)

ACTION_WEIGHTS = {
    "Goal": 10.0,
    "Shot on Target": 3.0,
    "Big Chance": 3.5,
    "Shot": 1.5,
    "Successful Dribble": 1.6,
    "Progressive Pass": 1.2,
    "Dangerous Pass": 1.4,
    "Cross": 0.8,
    "Pass": 0.15,
    "Tackle": 1.3,
    "Interception": 1.3,
    "Corner": 0.5,
    "Foul": -1.0,
    "Yellow Card": -2.0,
    "Red Card": -8.0,
    "Turnover": -1.2,
    "Offside": -0.5,
}


def player_match_stats(df: pd.DataFrame) -> pd.DataFrame:
    def _agg(g: pd.DataFrame) -> pd.Series:
        passes = g[g["event_type"].isin(["Pass", "Progressive Pass", "Dangerous Pass", "Cross"])]
        pass_complete = (passes["outcome"] == "Complete").sum()
        pass_total = len(passes)
        return pd.Series(
            {
                "team": g["team"].iloc[0],
                "position": g["position"].iloc[0] if "position" in g else "N/A",
                "events": len(g),
                "goals": (g["event_type"] == "Goal").sum(),
                "shots": g["event_type"].isin(["Shot", "Shot on Target", "Goal", "Big Chance"]).sum(),
                "xg": round(g["xg"].sum(), 2),
                "passes": pass_total,
                "pass_accuracy_pct": round(100 * pass_complete / pass_total, 1) if pass_total else 0.0,
                "dribbles": (g["event_type"] == "Successful Dribble").sum(),
                "tackles": (g["event_type"] == "Tackle").sum(),
                "interceptions": (g["event_type"] == "Interception").sum(),
                "fouls": (g["event_type"] == "Foul").sum(),
                "yellow_cards": (g["event_type"] == "Yellow Card").sum(),
                "red_cards": (g["event_type"] == "Red Card").sum(),
            }
        )

    stats = df.groupby(["match_id", "player"]).apply(_agg, include_groups=False).reset_index()
    return stats


def player_rating(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["_weight"] = df["event_type"].map(ACTION_WEIGHTS).fillna(0.0)
    df["_score"] = df["_weight"] + df.get("xg", 0).fillna(0) * 6.0

    scores = df.groupby(["match_id", "player"])["_score"].sum().reset_index()
    scores = scores.rename(columns={"_score": "raw_score"})

    lo = scores.groupby("match_id")["raw_score"].transform("min")
    hi = scores.groupby("match_id")["raw_score"].transform("max")
    span = (hi - lo).replace(0, np.nan)
    scaled = 40 + 60 * (scores["raw_score"] - lo) / span
    scores["rating"] = scaled.fillna(60.0).round(1)
    return scores.drop(columns="raw_score")


def top_performers(player_stats: pd.DataFrame, ratings: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    merged = ratings.merge(player_stats, on=["match_id", "player"], how="left")
    return merged.sort_values("rating", ascending=False).head(n).reset_index(drop=True)


def compare_players(player_stats: pd.DataFrame, player_a: str, player_b: str) -> pd.DataFrame:
    numeric_cols = player_stats.select_dtypes(include=[np.number]).columns.tolist()
    numeric_cols = [c for c in numeric_cols if c != "match_id"]

    agg = player_stats.groupby("player")[numeric_cols].sum()
    agg["matches"] = player_stats.groupby("player")["match_id"].nunique()

    rows = []
    for p in (player_a, player_b):
        if p not in agg.index:
            log.warning("Player %s not found in stats", p)
            continue
        rows.append(agg.loc[p].rename(p))

    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, axis=1)
