"""
Seasonal Intelligence Service.

Coordinates seasonal risk calculations, live weather telemetry, and corridor section safety evaluations.
"""

from datetime import datetime
from typing import Dict, List, Optional

from app.engines.seasonal_risk_engine import seasonal_risk_engine
from app.models.seasonal import (
    LiveWeatherReport,
    SectionSeasonalRisk,
    SeasonalContextResponse,
)
from app.services.live_weather_service import live_weather_service


class SeasonalService:
    def __init__(self):
        self.engine = seasonal_risk_engine
        self.live_service = live_weather_service

    def get_section_context(self, section_id: str, dt: Optional[datetime] = None) -> SeasonalContextResponse:
        """Retrieves seasonal context, live weather, and advisories for a block section."""
        return self.engine.get_context_response(section_id, dt=dt)

    def get_all_corridor_risks(
        self, asset_type: str = "TRACK", dt: Optional[datetime] = None
    ) -> List[SectionSeasonalRisk]:
        """Calculates seasonal risk scores across all 68 corridor sections."""
        return self.engine.get_corridor_seasonal_risks(asset_type=asset_type, dt=dt)

    def get_live_weather_report(self, section_id: str) -> LiveWeatherReport:
        """Gets live weather telemetry report for a section."""
        return self.live_service.get_live_weather(section_id)

    def is_maintenance_allowed(self, section_id: str, asset_type: str = "TRACK") -> bool:
        """
        Hard safety check: Returns False if SRS >= HARD_WEATHER_SAFETY_THRESHOLD.
        """
        risk = self.engine.calculate_srs(section_id, asset_type=asset_type)
        return not risk.hard_safety_exclusion


seasonal_service = SeasonalService()
