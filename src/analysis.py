# Team stats, ratings, correlations, and a small xT model.

from __future__ import annotations

import numpy as np
import pandas as pd

from config import PITCH_LENGTH, PITCH_WIDTH, XT_GRID_X, XT_GRID_Y
from logger import get_logger

log = get_logger(__name__)

def team_match_stats(df: pd.DataFrame) -> pd.DataFrame:
    def _agg(g: pd.DataFrame) -> pd.Series:
        passes = g[g["event_type"].isin(["Pass", "Progressive Pass", "Dangerous Pass", "Cross"])]
        shots = g[g["event_type"].isin(["Shot", "Shot on Target", "Goal", "Big Chance"])]
        goals = g[g["event_type"] == "Goal"]
        shots_on_target = g[g["event_type"].isin(["Shot on Target", "Goal"])]

        pass_complete = (passes["outcome"] == "Complete").sum()
        pass_total = len(passes)

        return pd.Series(
            {
                "events": len(g),
                "passes": pass_total,
                "pass_accuracy_pct": round(100 * pass_complete / pass_total, 1) if pass_total else 0.0,
                "shots": len(shots),
                "shots_on_target": len(shots_on_target),
                "goals": len(goals),
                "xg": round(g["xg"].sum(), 2),
                "fouls": (g["event_type"] == "Foul").sum(),
                "tackles": (g["event_type"] == "Tackle").sum(),
                "interceptions": (g["event_type"] == "Interception").sum(),
                "yellow_cards": (g["event_type"] == "Yellow Card").sum(),
                "red_cards": (g["event_type"] == "Red Card").sum(),
            }
        )

    stats = df.groupby(["match_id", "team"]).apply(_agg, include_groups=False).reset_index()

    # rough possession, based on event share
    match_totals = stats.groupby("match_id")["events"].transform("sum")
    stats["possession_pct"] = round(100 * stats["events"] / match_totals, 1)
    return stats


def performance_summary(stats: pd.DataFrame) -> pd.DataFrame:
    agg = stats.groupby("team").agg(
        matches=("match_id", "nunique"),
        goals=("goals", "sum"),
        xg=("xg", "sum"),
        shots=("shots", "sum"),
        shots_on_target=("shots_on_target", "sum"),
        avg_possession_pct=("possession_pct", "mean"),
        avg_pass_accuracy_pct=("pass_accuracy_pct", "mean"),
        fouls=("fouls", "sum"),
        yellow_cards=("yellow_cards", "sum"),
        red_cards=("red_cards", "sum"),
    ).reset_index()

    agg["goals_per_match"] = round(agg["goals"] / agg["matches"], 2)
    agg["xg_per_match"] = round(agg["xg"] / agg["matches"], 2)
    agg["shot_conversion_pct"] = np.where(
        agg["shots"] > 0, round(100 * agg["goals"] / agg["shots"], 1), 0.0
    )
    agg["avg_possession_pct"] = agg["avg_possession_pct"].round(1)
    agg["avg_pass_accuracy_pct"] = agg["avg_pass_accuracy_pct"].round(1)
    return agg.sort_values("xg_per_match", ascending=False).reset_index(drop=True)

def team_ratings(stats: pd.DataFrame) -> pd.DataFrame:
    df = stats.copy()

    def norm(col: str) -> pd.Series:
        lo, hi = df[col].min(), df[col].max()
        if hi == lo:
            return pd.Series(0.5, index=df.index)
        return (df[col] - lo) / (hi - lo)

    attack_score = 0.4 * norm("xg") + 0.3 * norm("shots_on_target") + 0.3 * norm("goals")
    control_score = 0.6 * norm("possession_pct") + 0.4 * norm("pass_accuracy_pct")
    discipline_penalty = 0.6 * norm("fouls") + 0.4 * norm("yellow_cards") * 2

    rating = 100 * (0.5 * attack_score + 0.35 * control_score - 0.15 * discipline_penalty)
    df["team_rating"] = rating.clip(0, 100).round(1)
    return df[["match_id", "team", "team_rating"]]


def match_ratings(stats: pd.DataFrame) -> pd.DataFrame:
    ratings = team_ratings(stats)
    merged = ratings.groupby("match_id")["team_rating"].agg(["mean", "std", "max", "min"])
    merged = merged.rename(
        columns={
            "mean": "match_quality",
            "std": "competitiveness_spread",
            "max": "top_team_rating",
            "min": "bottom_team_rating",
        }
    ).reset_index()
    merged["match_quality"] = merged["match_quality"].round(1)
    merged["competitiveness_spread"] = merged["competitiveness_spread"].fillna(0).round(1)
    return merged

def correlation_matrix(stats: pd.DataFrame) -> pd.DataFrame:
    numeric_cols = stats.select_dtypes(include=[np.number]).drop(columns=["match_id"], errors="ignore")
    return numeric_cols.corr().round(2)


def _xt_grid() -> np.ndarray:
    """Hand-tuned danger surface. Good enough for this project."""
    xs = np.linspace(0, 1, XT_GRID_X)
    ys = np.linspace(0, 1, XT_GRID_Y)
    grid = np.zeros((XT_GRID_Y, XT_GRID_X))
    for i, y in enumerate(ys):
        for j, x in enumerate(xs):
            central = 1 - abs(y - 0.5) * 1.6
            central = max(central, 0.15)
            grid[i, j] = (x ** 1.7) * central
    grid = grid / grid.max()
    return grid


_XT_SURFACE = _xt_grid()


def xt_value(x: float, y: float) -> float:
    col = int(np.clip(x / PITCH_LENGTH, 0, 0.999) * XT_GRID_X)
    row = int(np.clip(y / PITCH_WIDTH, 0, 0.999) * XT_GRID_Y)
    return float(_XT_SURFACE[row, col])


def add_xt_column(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["xt"] = df.apply(lambda r: xt_value(r["x"], r["y"]), axis=1)
    return df


def team_xt_summary(xt_df: pd.DataFrame) -> pd.DataFrame:
    moves = xt_df[
        xt_df["event_type"].isin(
            ["Pass", "Progressive Pass", "Dangerous Pass", "Cross", "Successful Dribble"]
        )
    ]
    summary = moves.groupby(["match_id", "team"])["xt"].sum().reset_index()
    summary = summary.rename(columns={"xt": "total_xt"})
    summary["total_xt"] = summary["total_xt"].round(2)
    return summary
