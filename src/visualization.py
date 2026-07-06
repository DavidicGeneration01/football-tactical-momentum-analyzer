"""
Static chart generation (matplotlib/seaborn) used by the report generator,
and shared figure builders reused by the Streamlit dashboard's Plotly views.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless-safe backend for report generation
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from config import CHARTS_DIR, PITCH_LENGTH, PITCH_WIDTH
from logger import get_logger

log = get_logger(__name__)

sns.set_theme(style="darkgrid")
PALETTE = ["#1f9e5c", "#e8543f", "#3f7fe8", "#e8b13f"]


def _save(fig: plt.Figure, name: str) -> Path:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    path = CHARTS_DIR / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    log.info("Saved chart: %s", path)
    return path


def plot_momentum_timeline(momentum_df: pd.DataFrame, teams: list[str], title: str = "Momentum Timeline") -> Path:
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.axhline(0, color="white", linewidth=0.8, alpha=0.5)
    ax.fill_between(
        momentum_df["minute"], momentum_df["momentum_diff"], 0,
        where=(momentum_df["momentum_diff"] >= 0), color=PALETTE[0], alpha=0.55,
        label=teams[0],
    )
    ax.fill_between(
        momentum_df["minute"], momentum_df["momentum_diff"], 0,
        where=(momentum_df["momentum_diff"] < 0), color=PALETTE[1], alpha=0.55,
        label=teams[1],
    )
    ax.set_xlabel("Minute")
    ax.set_ylabel("Momentum (diff)")
    ax.set_title(title)
    ax.legend(loc="upper right")
    return _save(fig, "momentum_timeline.png")


def plot_shot_map(df: pd.DataFrame, team: str) -> Path:
    shots = df[(df["team"] == team) & (df["event_type"].isin(["Shot", "Shot on Target", "Goal", "Big Chance"]))]
    fig, ax = plt.subplots(figsize=(8, 5.5))
    _draw_pitch(ax)
    sizes = 40 + shots["xg"].fillna(0) * 300
    colors = np.where(shots["event_type"] == "Goal", PALETTE[1], PALETTE[2])
    ax.scatter(shots["x"], shots["y"], s=sizes, c=colors, alpha=0.75, edgecolors="white", linewidths=0.5)
    ax.set_title(f"{team} — Shot Map (bubble size = xG)")
    return _save(fig, f"shot_map_{team.replace(' ', '_')}.png")


def plot_heatmap(df: pd.DataFrame, team: str) -> Path:
    team_events = df[df["team"] == team]
    fig, ax = plt.subplots(figsize=(8, 5.5))
    _draw_pitch(ax)
    sns.kdeplot(
        x=team_events["x"], y=team_events["y"], fill=True, cmap="rocket",
        alpha=0.65, thresh=0.05, levels=40, ax=ax,
    )
    ax.set_xlim(0, PITCH_LENGTH)
    ax.set_ylim(0, PITCH_WIDTH)
    ax.set_title(f"{team} — Activity Heatmap")
    return _save(fig, f"heatmap_{team.replace(' ', '_')}.png")


def plot_correlation_heatmap(corr: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax, square=True)
    ax.set_title("Stat Correlation Heatmap")
    return _save(fig, "correlation_heatmap.png")


def plot_team_ratings_bar(perf_summary: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5))
    order = perf_summary.sort_values("xg_per_match", ascending=False)
    palette = sns.color_palette("husl", n_colors=order["team"].nunique())
    sns.barplot(data=order, x="team", y="xg_per_match", hue="team", palette=palette, legend=False, ax=ax)
    ax.set_ylabel("xG per match")
    ax.set_title("Team Attacking Output (xG/match)")
    ax.tick_params(axis="x", rotation=35)
    return _save(fig, "team_ratings_bar.png")


def plot_player_ratings(top_players: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(9, 6))
    order = top_players.sort_values("rating")
    palette = sns.color_palette("husl", n_colors=order["team"].nunique())
    sns.barplot(data=order, x="rating", y="player", hue="team", palette=palette, ax=ax)
    ax.set_xlabel("Match Rating")
    ax.set_title("Top Performers")
    return _save(fig, "top_player_ratings.png")


def _draw_pitch(ax: plt.Axes) -> None:
    """Minimal top-down pitch outline in the 120x80 coordinate system."""
    ax.set_facecolor("#0f2e1c")
    ax.plot([0, 0, PITCH_LENGTH, PITCH_LENGTH, 0], [0, PITCH_WIDTH, PITCH_WIDTH, 0, 0], color="white", linewidth=1)
    ax.axvline(PITCH_LENGTH / 2, color="white", linewidth=1)
    centre_circle = plt.Circle((PITCH_LENGTH / 2, PITCH_WIDTH / 2), 9.15, color="white", fill=False, linewidth=1)
    ax.add_patch(centre_circle)
    # penalty boxes
    ax.plot([0, 18, 18, 0], [18, 18, 62, 62], color="white", linewidth=1)
    ax.plot(
        [PITCH_LENGTH, PITCH_LENGTH - 18, PITCH_LENGTH - 18, PITCH_LENGTH],
        [18, 18, 62, 62], color="white", linewidth=1,
    )
    ax.set_xlim(-2, PITCH_LENGTH + 2)
    ax.set_ylim(-2, PITCH_WIDTH + 2)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect("equal")


def generate_all_charts(
    df: pd.DataFrame,
    momentum_df: pd.DataFrame,
    teams: list[str],
    perf_summary: pd.DataFrame,
    corr: pd.DataFrame,
    top_players: pd.DataFrame,
) -> list[Path]:
    """Convenience entry point used by main.py to build every static chart."""
    paths = [
        plot_momentum_timeline(momentum_df, teams),
        plot_correlation_heatmap(corr),
        plot_team_ratings_bar(perf_summary),
        plot_player_ratings(top_players),
    ]
    for team in teams:
        paths.append(plot_shot_map(df, team))
        paths.append(plot_heatmap(df, team))
    return paths
