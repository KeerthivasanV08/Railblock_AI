"""
Logging configuration for RailBlock AI backend.
"""

import logging
from app.config.settings import settings

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def configure_logging(level: str = None) -> None:
    log_level = level or settings.LOG_LEVEL.upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format=LOG_FORMAT
    )
