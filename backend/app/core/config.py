"""
Backward-compatibility shim for core.config.
Canonical settings are now located in app.config.settings.
"""

from app.config.settings import Settings, settings, _resolve_path  # noqa: F401
