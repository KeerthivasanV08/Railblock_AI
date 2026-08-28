"""
Backward-compatibility shim for core.logging.
Canonical logging configuration is now located in app.config.logging.
"""

from app.config.logging import LOG_FORMAT, configure_logging  # noqa: F401
