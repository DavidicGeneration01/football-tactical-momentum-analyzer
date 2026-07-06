"""
Thin convenience wrapper so anything inside `src/` can do:

    from config import RAW_EVENTS_FILE, MOMENTUM_EVENT_WEIGHTS

instead of reaching up into the top-level `config/` package. All real
values live in `config/config.py`; this file just re-exports them.

Implementation note: this file is itself importable as a top-level module
named `config` (because `src/` sits on sys.path), which would collide with
the top-level `config/` *package* at the project root if we tried a normal
`import config.config`. To dodge that name clash we load
`config/config.py` directly from its file path via importlib.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_ROOT_CONFIG_FILE = _ROOT / "config" / "config.py"

_spec = importlib.util.spec_from_file_location("_root_config", _ROOT_CONFIG_FILE)
_root_config = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_root_config)  # type: ignore[union-attr]

ASSETS_DIR = _root_config.ASSETS_DIR
CHARTS_DIR = _root_config.CHARTS_DIR
DATA_DIR = _root_config.DATA_DIR
DATA_REPORTS_DIR = _root_config.DATA_REPORTS_DIR
DEFAULT_MIN_EVENTS = _root_config.DEFAULT_MIN_EVENTS
LOG_FILE = _root_config.LOG_FILE
LOG_LEVEL = _root_config.LOG_LEVEL
LOGS_DIR = _root_config.LOGS_DIR
MOMENTUM_DECAY = _root_config.MOMENTUM_DECAY
MOMENTUM_EVENT_WEIGHTS = _root_config.MOMENTUM_EVENT_WEIGHTS
MOMENTUM_WINDOW_MINUTES = _root_config.MOMENTUM_WINDOW_MINUTES
PITCH_LENGTH = _root_config.PITCH_LENGTH
PITCH_WIDTH = _root_config.PITCH_WIDTH
PROCESSED_DATA_DIR = _root_config.PROCESSED_DATA_DIR
PROCESSED_EVENTS_CSV = _root_config.PROCESSED_EVENTS_CSV
PROCESSED_EVENTS_FILE = _root_config.PROCESSED_EVENTS_FILE
RANDOM_SEED = _root_config.RANDOM_SEED
RAW_DATA_DIR = _root_config.RAW_DATA_DIR
RAW_EVENTS_FILE = _root_config.RAW_EVENTS_FILE
REPORTS_DIR = _root_config.REPORTS_DIR
ROOT_DIR = _root_config.ROOT_DIR
TEAMS = _root_config.TEAMS
XT_GRID_X = _root_config.XT_GRID_X
XT_GRID_Y = _root_config.XT_GRID_Y
ensure_directories = _root_config.ensure_directories

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
