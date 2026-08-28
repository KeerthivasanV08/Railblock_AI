"""Provider interfaces for simulated and future external live train data."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from app.core.config import settings


class NormalizedLiveTrain(BaseModel):
    train_id: str
    train_number: str | None = None
    train_type: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    speed: float | None = None
    heading: float | None = None
    current_station: str | None = None
    next_station: str | None = None
    current_segment: str | None = None
    delay_minutes: int = 0
    status: str = "UNKNOWN"
    event_time: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    received_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: str = "UNKNOWN"
    freshness_seconds: int | None = None


class LiveTrainProvider(ABC):
    source = "UNKNOWN"
    provider_name = "unknown"

    @abstractmethod
    def get_train_positions(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    def get_train_position(self, train_id: str) -> dict[str, Any] | None:
        return next((item for item in self.get_train_positions() if item["train_id"] == train_id), None)

    def get_status(self) -> dict[str, Any]:
        return {
            "status": "available",
            "provider": self.provider_name,
            "source": self.source,
            "external_configured": False,
        }


class ExternalLiveTrainProvider(LiveTrainProvider):
    """Adapter boundary for the real provider, intentionally not connected yet."""

    source = "EXTERNAL_PROVIDER"
    provider_name = "external"

    def __init__(self, base_url: str = "", token: str = "", timeout: float = 5.0):
        self.base_url = base_url
        self.token = token
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.token)

    def get_train_positions(self) -> list[dict[str, Any]]:
        return []

    def get_status(self) -> dict[str, Any]:
        if not self.configured:
            status = "not_configured"
            reason = "EXTERNAL_LIVE_API_BASE_URL and EXTERNAL_LIVE_API_TOKEN are required."
        else:
            status = "unavailable"
            reason = "External API contract is not connected yet."
        return {
            "status": status,
            "provider": self.provider_name,
            "source": self.source,
            "external_configured": self.configured,
            "base_url_configured": bool(self.base_url),
            "token_configured": bool(self.token),
            "adapter_ready": True,
            "data_fabricated": False,
            "reason": reason,
        }


def get_live_train_provider() -> LiveTrainProvider:
    if settings.LIVE_TRAIN_PROVIDER.lower() == "external":
        return ExternalLiveTrainProvider(
            base_url=settings.EXTERNAL_LIVE_API_BASE_URL,
            token=settings.EXTERNAL_LIVE_API_TOKEN,
            timeout=settings.EXTERNAL_LIVE_API_TIMEOUT_SECONDS,
        )

    from app.live.simulator import SimulatedLiveTrainProvider

    return SimulatedLiveTrainProvider()
