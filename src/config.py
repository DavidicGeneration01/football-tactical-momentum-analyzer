"""
File path via importlib.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROOT_CONFIG_FILE = ROOT / "config" / "config.py"

spec = importlib.util.spec_from_file_location("root_config", ROOT_CONFIG_FILE)
root_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(root_config)  # type: ignore[union-attr]

ASSETS_DIR = root_config.ASSETS_DIR
CHARTS_DIR = root_config.CHARTS_DIR
DATA_DIR = root_config.DATA_DIR
DATA_REPORTS_DIR = root_config.DATA_REPORTS_DIR
DEFAULT_MIN_EVENTS = root_config.DEFAULT_MIN_EVENTS
LOG_FILE = root_config.LOG_FILE
LOG_LEVEL = root_config.LOG_LEVEL
LOGS_DIR = root_config.LOGS_DIR
MOMENTUM_DECAY = root_config.MOMENTUM_DECAY
MOMENTUM_EVENT_WEIGHTS = root_config.MOMENTUM_EVENT_WEIGHTS
MOMENTUM_WINDOW_MINUTES = root_config.MOMENTUM_WINDOW_MINUTES
PITCH_LENGTH = root_config.PITCH_LENGTH
PITCH_WIDTH = root_config.PITCH_WIDTH
PROCESSED_DATA_DIR = root_config.PROCESSED_DATA_DIR
PROCESSED_EVENTS_CSV = root_config.PROCESSED_EVENTS_CSV
PROCESSED_EVENTS_FILE = root_config.PROCESSED_EVENTS_FILE
RANDOM_SEED = root_config.RANDOM_SEED
RAW_DATA_DIR = root_config.RAW_DATA_DIR
RAW_EVENTS_FILE = root_config.RAW_EVENTS_FILE
REPORTS_DIR = root_config.REPORTS_DIR
ROOT_DIR = root_config.ROOT_DIR
TEAMS = root_config.TEAMS
XT_GRID_X = root_config.XT_GRID_X
XT_GRID_Y = root_config.XT_GRID_Y
ensure_directories = root_config.ensure_directories

__all__ = [
    "ASSETS_DIR",
    "CHARTS_DIR",
    "DATA_DIR",
    "DATA_REPORTS_DIR",
    "DEFAULT_MIN_EVENTS",
    "LOG_FILE",
    "LOG_LEVEL",
    "LOGS_DIR",
    "MOMENTUM_DECAY",
    "MOMENTUM_EVENT_WEIGHTS",
    "MOMENTUM_WINDOW_MINUTES",
    "PITCH_LENGTH",
    "PITCH_WIDTH",
    "PROCESSED_DATA_DIR",
    "PROCESSED_EVENTS_CSV",
    "PROCESSED_EVENTS_FILE",
    "RANDOM_SEED",
    "RAW_DATA_DIR",
    "RAW_EVENTS_FILE",
    "REPORTS_DIR",
    "ROOT_DIR",
    "TEAMS",
    "XT_GRID_X",
    "XT_GRID_Y",
    "ensure_directories",
]
