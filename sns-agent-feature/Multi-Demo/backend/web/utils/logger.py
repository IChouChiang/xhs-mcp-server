"""Logging helpers for the backend service."""
from __future__ import annotations

import logging
from logging.config import dictConfig
from typing import Any, Dict

LOGGING_CONFIG: Dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
}

dictConfig(LOGGING_CONFIG)


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger instance."""
    return logging.getLogger(name)
