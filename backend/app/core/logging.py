"""Structured Logging Setup for Project Campus."""

import logging
import sys
from app.core.config import settings


def setup_logging() -> None:
    """Configure standard application logging."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
