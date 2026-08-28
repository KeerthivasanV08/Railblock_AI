"""
Application Configuration / Settings for RailBlock AI.

This is the canonical settings module. Moved from app.core.config during
the 2026-08-27 repository restructure. app.core.config re-exports from here
for backward compatibility.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "RailBlock AI Backend"
    APP_ENV: str = "development"
    API_PREFIX: str = "/api"
    FRONTEND_URL: str = "http://localhost:5173"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:5174,http://127.0.0.1:5174,"
        "http://localhost:4173,http://127.0.0.1:4173,"
        "http://localhost:8080,http://127.0.0.1:8080"
    )

    # Live train provider. Keep simulation as the safe default until the real
    # railway API contract and credentials are supplied.
    LIVE_TRAIN_PROVIDER: str = "simulation"
    EXTERNAL_LIVE_API_BASE_URL: str = ""
    EXTERNAL_LIVE_API_TOKEN: str = ""
    EXTERNAL_LIVE_API_TIMEOUT_SECONDS: float = 5.0

    # Base Paths — resolved relative to the repository root
    BASE_DIR: Path = Path(__file__).resolve().parents[3]  # d:/Railblock_AI
    DATA_ROOT: Path = BASE_DIR / "data"
    RAW_DATA_ROOT: Path = DATA_ROOT / "raw"
    PROCESSED_DATA_ROOT: Path = DATA_ROOT / "processed"
    OUTPUT_DATA_ROOT: Path = DATA_ROOT / "outputs"

    # ML artifact root — points to backend/app/ml/models/ for runtime inference.
    # The canonical training artifacts are at ml/mdps/artifacts/ (top-level ml/).
    # data/models/ is kept for backward compatibility with older pipeline scripts.
    MODEL_ROOT: Path = BASE_DIR / "backend" / "app" / "ml" / "models"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else (settings.BASE_DIR / path).resolve()


settings.DATA_ROOT = _resolve_path(settings.DATA_ROOT)
settings.RAW_DATA_ROOT = _resolve_path(settings.RAW_DATA_ROOT)
settings.PROCESSED_DATA_ROOT = _resolve_path(settings.PROCESSED_DATA_ROOT)
settings.OUTPUT_DATA_ROOT = _resolve_path(settings.OUTPUT_DATA_ROOT)
settings.MODEL_ROOT = _resolve_path(settings.MODEL_ROOT)
