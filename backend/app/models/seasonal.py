"""
Pydantic Models for Seasonal Intelligence and Weather Risk.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class WeatherStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class WeatherCondition(str, Enum):
    CLEAR = "CLEAR"
    CLOUDY = "CLOUDY"
    LIGHT_RAIN = "LIGHT_RAIN"
    HEAVY_RAIN = "HEAVY_RAIN"
    CYCLONE = "CYCLONE"
    EXTREME_HEAT = "EXTREME_HEAT"
    FOG = "FOG"
    UNKNOWN = "UNKNOWN"


class RiskClassification(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    CRITICAL = "CRITICAL"


class LiveWeatherReport(BaseModel):
    section_id: str
    weather_status: WeatherStatus = WeatherStatus.UNKNOWN
    weather_source_status: str = "UNAVAILABLE"
    temperature_c: Optional[float] = None
    rainfall_mm: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    weather_severity: Optional[float] = None
    condition: WeatherCondition = WeatherCondition.UNKNOWN
    timestamp: Optional[str] = None


class SectionSeasonalRisk(BaseModel):
    section_id: str
    section_name: str
    start_station: str
    end_station: str
    climate_zone: str
    season_name: str
    season_score: float = Field(ge=0.0, le=100.0)
    vulnerability_score: float = Field(ge=0.0, le=100.0)
    live_weather_severity: Optional[float] = None
    raw_srs: float = Field(ge=0.0, le=100.0)
    asset_type: str = "TRACK"
    asset_multiplier: float = Field(ge=0.5, le=2.0)
    srs: float = Field(ge=0.0, le=100.0)
    risk_level: RiskClassification
    hard_safety_exclusion: bool = False
    weather_source_status: str = "AVAILABLE"


class SeasonalContextResponse(BaseModel):
    section_id: str
    corridor: str = "Chennai Egmore - Thoothukudi"
    date: str
    season: str
    risk: SectionSeasonalRisk
    live_weather: LiveWeatherReport
    recommendations: List[str] = Field(default_factory=list)
