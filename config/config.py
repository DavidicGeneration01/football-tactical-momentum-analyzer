"""
Global configuration for the Football Tactical Momentum Analyzer.

This module is the single source of truth for filesystem paths and
project-wide constants. `src/config.py` re-exports everything from here
so that code under `src/` can simply do `from config import settings`-style
imports without caring whether it's running from the repo root or a
notebook.
"""

from __future__ import annotations

from pathlib import Path

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
ROOT_DIR: Path = Path(__file__).resolve().parent.parent

ASSETS_DIR: Path = ROOT_DIR / "assets"
CHARTS_DIR: Path = ROOT_DIR / "charts"

DATA_DIR: Path = ROOT_DIR / "data"
RAW_DATA_DIR: Path = DATA_DIR / "raw"
PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
DATA_REPORTS_DIR: Path = DATA_DIR / "reports"

REPORTS_DIR: Path = ROOT_DIR / "reports"
LOGS_DIR: Path = ROOT_DIR / "logs"

RAW_EVENTS_FILE: Path = RAW_DATA_DIR / "events.csv"
PROCESSED_EVENTS_FILE: Path = PROCESSED_DATA_DIR / "events_clean.parquet"
PROCESSED_EVENTS_CSV: Path = PROCESSED_DATA_DIR / "events_clean.csv"

# --------------------------------------------------------------------------
# Pitch dimensions (StatsBomb-style 120 x 80 coordinate system)
# --------------------------------------------------------------------------
PITCH_LENGTH: float = 120.0
PITCH_WIDTH: float = 80.0

# --------------------------------------------------------------------------
# Momentum Index parameters
# --------------------------------------------------------------------------
MOMENTUM_WINDOW_MINUTES: int = 5          # rolling window size
MOMENTUM_DECAY: float = 0.85              # exponential decay factor per event
MOMENTUM_EVENT_WEIGHTS: dict[str, float] = {
    "Goal": 10.0,
    "Shot": 4.0,
    "Shot on Target": 5.5,
    "Big Chance": 6.0,
    "Dangerous Pass": 2.0,
    "Successful Dribble": 1.8,
    "Pass": 0.4,
    "Progressive Pass": 1.2,
    "Cross": 1.0,
    "Corner": 1.5,
    "Interception": 1.3,
    "Tackle": 1.2,
    "Foul": -0.8,
    "Yellow Card": -1.5,
    "Red Card": -6.0,
    "Turnover": -1.5,
    "Offside": -0.5,
}

# --------------------------------------------------------------------------
# Expected Threat (xT) grid resolution
# --------------------------------------------------------------------------
XT_GRID_X: int = 12
XT_GRID_Y: int = 8

# --------------------------------------------------------------------------
# Synthetic data generation
# --------------------------------------------------------------------------
DEFAULT_MIN_EVENTS: int = 5000
RANDOM_SEED: int = 42

# 2025-26 Nigeria Premier Football League (NPFL) clubs
TEAMS: list[str] = [
    "Abia Warriors",
    "Barau",
    "Bayelsa United",
    "Bendel Insurance",
    "El-Kanemi Warriors",
    "Enugu Rangers",
    "Enyimba",
    "Ikorodu City",
    "Kano Pillars",
    "Katsina United",
    "Kun Khalifat",
    "Kwara United",
    "Nasarawa United",
    "Niger Tornadoes",
    "Plateau United",
    "Remo Stars",
    "Rivers United",
    "Shooting Stars",
    "Warri Wolves",
    "Wikki Tourists",
]

# --------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------
LOG_LEVEL: str = "INFO"
LOG_FILE: Path = LOGS_DIR / "app.log"


def ensure_directories() -> None:
    """Create every directory this project writes to, if missing."""
    for directory in (
        ASSETS_DIR,
        CHARTS_DIR,
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        DATA_REPORTS_DIR,
        REPORTS_DIR,
        LOGS_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)
