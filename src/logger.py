# Project logging setup.

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from config import LOG_FILE, LOG_LEVEL, LOGS_DIR

_CONFIGURED = False


def _configure_root() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger("momentum_analyzer")
    root.setLevel(LOG_LEVEL)
    root.propagate = False

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)
    console_handler.setLevel(LOG_LEVEL)

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=2_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    file_handler.setLevel(LOG_LEVEL)

    root.addHandler(console_handler)
    root.addHandler(file_handler)

    _CONFIGURED = True


def get_logger(name: str = "momentum_analyzer") -> logging.Logger:
    _configure_root()
    if name == "momentum_analyzer":
        return logging.getLogger(name)
    return logging.getLogger(f"momentum_analyzer.{name}")
