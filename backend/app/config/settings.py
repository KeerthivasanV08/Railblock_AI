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

    # Base Paths — dynamically resolved for local dev, Render, or Docker
    BASE_DIR: Path = Path(__file__).resolve().parents[3]  # d:/Railblock_AI or parent
    DATA_ROOT: Path = Path(__file__).resolve().parents[2] / "data"  # Default to backend/data
    RAW_DATA_ROOT: Path = DATA_ROOT / "raw"
    DERIVED_DATA_ROOT: Path = DATA_ROOT / "derived"
    PROCESSED_DATA_ROOT: Path = DATA_ROOT / "processed"
    OUTPUT_DATA_ROOT: Path = DATA_ROOT / "outputs"

    # Weather & Seasonal Risk Intelligence
    WEATHER_DATA_SOURCE: str = "csv_simulated"
    WEATHER_API_BASE_URL: str = ""
    WEATHER_API_KEY: str = ""
    SRS_WEIGHT_SEASON: float = 0.25
    SRS_WEIGHT_VULNERABILITY: float = 0.35
    SRS_WEIGHT_LIVE_WEATHER: float = 0.40
    HARD_WEATHER_SAFETY_THRESHOLD: float = 75.0

    # ML artifact root — points to backend/app/ml/models/ for runtime inference.
    MODEL_ROOT: Path = Path(__file__).resolve().parents[1] / "ml" / "models"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()


def _resolve_data_root() -> Path:
    # 1. Check if DATA_ROOT or DATA_DIR explicitly set in environment
    import os
    env_data = os.environ.get("DATA_ROOT") or os.environ.get("DATA_DIR")
    if env_data and Path(env_data).exists():
        return Path(env_data).resolve()

    # 2. Check backend/data (where CSVs are copied for deployment)
    backend_data = (Path(__file__).resolve().parents[2] / "data").resolve()
    if backend_data.exists() and (backend_data / "processed").exists():
        return backend_data

    # 3. Check repo root / data
    repo_data = (Path(__file__).resolve().parents[3] / "data").resolve()
    if repo_data.exists() and (repo_data / "processed").exists():
        return repo_data

    # 4. Check cwd
    cwd_data = Path.cwd() / "data"
    if cwd_data.exists():
        return cwd_data.resolve()

    return backend_data


settings.DATA_ROOT = _resolve_data_root()
settings.RAW_DATA_ROOT = settings.DATA_ROOT / "raw"
settings.DERIVED_DATA_ROOT = settings.DATA_ROOT / "derived"
settings.PROCESSED_DATA_ROOT = settings.DATA_ROOT / "processed"
settings.OUTPUT_DATA_ROOT = settings.DATA_ROOT / "outputs"
if not settings.MODEL_ROOT.exists():
    fallback_model = settings.DATA_ROOT / "models"
    if fallback_model.exists():
        settings.MODEL_ROOT = fallback_model


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else (settings.BASE_DIR / path).resolve()


