"""
Seasonal Risk Engine (Deterministic Task-Aware SRS).

Calculates Section Seasonal Risk Score (SRS) based on:
1. Climatological seasonal vulnerability (Layer A)
2. Historical section terrain/flood vulnerability (Layer A)
3. Real-time / simulated live weather telemetry (Layer B)
4. Task / Asset specific multiplier (Track, OHE, Signal)

Enforces Hard Safety Threshold: SRS >= 75 triggers hard exclusion gate.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd

from app.config.settings import settings
from app.models.seasonal import (
    LiveWeatherReport,
    RiskClassification,
    SectionSeasonalRisk,
    SeasonalContextResponse,
    WeatherStatus,
)
from app.services.live_weather_service import live_weather_service

logger = logging.getLogger(__name__)


class SeasonalRiskEngine:
    def __init__(self):
        self.sensitivity_file = settings.DERIVED_DATA_ROOT / "weather" / "section_weather_sensitivity.csv"
        self._section_profiles: Dict[str, Dict] = {}
        self._load_profiles()

    def _load_profiles(self):
        if not self.sensitivity_file.exists():
            logger.warning(f"Section sensitivity file not found at {self.sensitivity_file}")
            return

        try:
            df = pd.read_csv(self.sensitivity_file)
            for _, row in df.iterrows():
                sec_id = str(row.get("section_id", "")).strip()
                if sec_id:
                    self._section_profiles[sec_id] = row.to_dict()
        except Exception as e:
            logger.error(f"Failed to load section sensitivity profiles: {e}")

    def get_season_name_and_score(self, dt: Optional[datetime] = None) -> Tuple[str, float]:
        """
        Returns the Tamil Nadu climatic season and base regional risk score (0-100).
        - Winter: Jan-Feb (low risk, 15.0)
        - Summer: Mar-May (extreme heat, rail buckle risk, 40.0)
        - Southwest Monsoon: Jun-Sep (moderate rain in TN, 30.0)
        - Northeast Monsoon / Cyclone: Oct-Dec (peak coastal cyclones & floods, 75.0)
        """
        if dt is None:
            dt = datetime.now()

        month = dt.month
        if month in (1, 2):
            return "Winter (Dry)", 15.0
        elif month in (3, 4, 5):
            return "Summer (High Rail Temp)", 40.0
        elif month in (6, 7, 8, 9):
            return "Southwest Monsoon", 30.0
        else:
            return "Northeast Monsoon (Cyclone Season)", 75.0

    def calculate_srs(
        self,
        section_id: str,
        asset_type: str = "TRACK",
        dt: Optional[datetime] = None,
        live_weather: Optional[LiveWeatherReport] = None,
    ) -> SectionSeasonalRisk:
        """
        Calculates deterministic task-aware SRS for a corridor section.
        Formula:
          SRS = min(100.0, (season_score * Ws + vuln_score * Wv + live_severity * Wl) * M_asset)
        """
        if not self._section_profiles:
            self._load_profiles()

        profile = self._section_profiles.get(section_id, {})
        season_name, season_score = self.get_season_name_and_score(dt)

        # Climatological Section Vulnerability (0 - 100)
        vuln_raw = float(profile.get("overall_section_vulnerability", 0.5))
        vuln_score = round(min(100.0, max(0.0, vuln_raw * 100.0)), 1)

        # Live Weather Component
        if live_weather is None:
            live_weather = live_weather_service.get_live_weather(section_id)

        ws = getattr(settings, "SRS_WEIGHT_SEASON", 0.25)
        wv = getattr(settings, "SRS_WEIGHT_VULNERABILITY", 0.35)
        wl = getattr(settings, "SRS_WEIGHT_LIVE_WEATHER", 0.40)

        weather_source_status = live_weather.weather_source_status
        live_severity = live_weather.weather_severity

        if live_severity is not None and weather_source_status == "AVAILABLE":
            weighted_sum = (season_score * ws) + (vuln_score * wv) + (live_severity * wl)
        else:
            # Rescale weights across available components if live feed is unavailable
            norm = ws + wv
            w_s_norm = ws / norm
            w_v_norm = wv / norm
            weighted_sum = (season_score * w_s_norm) + (vuln_score * w_v_norm)

        # Asset Multiplier
        asset_clean = asset_type.upper().strip()
        if "OHE" in asset_clean or "TRD" in asset_clean or "ELECTRICAL" in asset_clean:
            asset_multiplier = float(profile.get("asset_multiplier_ohe", 1.3))
        elif "SIGNAL" in asset_clean or "S&T" in asset_clean or "TELECOM" in asset_clean:
            asset_multiplier = float(profile.get("asset_multiplier_signal", 1.1))
        else:
            asset_multiplier = float(profile.get("asset_multiplier_track", 1.0))

        raw_srs = round(min(100.0, weighted_sum), 2)
        srs = round(min(100.0, max(0.0, raw_srs * asset_multiplier)), 1)

        # Risk Classification
        if srs < 40.0:
            risk_level = RiskClassification.LOW
        elif srs < 75.0:
            risk_level = RiskClassification.MEDIUM
        else:
            risk_level = RiskClassification.CRITICAL

        hard_safety_threshold = getattr(settings, "HARD_WEATHER_SAFETY_THRESHOLD", 75.0)
        hard_safety_exclusion = bool(srs >= hard_safety_threshold)

        return SectionSeasonalRisk(
            section_id=section_id,
            section_name=f"{profile.get('from_station', section_id)} - {profile.get('to_station', '')}".strip(" -"),
            start_station=str(profile.get("from_station", "")),
            end_station=str(profile.get("to_station", "")),
            climate_zone="Coastal Tamil Nadu" if vuln_raw > 0.6 else "Interior Plains",
            season_name=season_name,
            season_score=season_score,
            vulnerability_score=vuln_score,
            live_weather_severity=live_severity,
            raw_srs=raw_srs,
            asset_type=asset_type,
            asset_multiplier=asset_multiplier,
            srs=srs,
            risk_level=risk_level,
            hard_safety_exclusion=hard_safety_exclusion,
            weather_source_status=weather_source_status,
        )

    def get_corridor_seasonal_risks(
        self,
        asset_type: str = "TRACK",
        dt: Optional[datetime] = None,
    ) -> List[SectionSeasonalRisk]:
        """Calculates seasonal risks for all 68 corridor sections."""
        if not self._section_profiles:
            self._load_profiles()

        live_reports = live_weather_service.get_all_live_weather()
        results = []
        for sec_id in sorted(self._section_profiles.keys()):
            live = live_reports.get(sec_id)
            risk = self.calculate_srs(sec_id, asset_type=asset_type, dt=dt, live_weather=live)
            results.append(risk)
        return results

    def get_context_response(self, section_id: str, dt: Optional[datetime] = None) -> SeasonalContextResponse:
        """Returns comprehensive seasonal context and recommendations for API response."""
        live = live_weather_service.get_live_weather(section_id)
        risk = self.calculate_srs(section_id, dt=dt, live_weather=live)

        recs = []
        if risk.hard_safety_exclusion:
            recs.append("CRITICAL: Severe environmental hazard active. Block allocation strictly forbidden by safety gates.")
        elif risk.risk_level == RiskClassification.MEDIUM:
            recs.append("ADVISORY: Moderate weather risk. Provide contingency buffer (+15 min) and deploy safety spotters.")
        else:
            recs.append("NORMAL: Favorable meteorological conditions for planned maintenance operations.")

        if risk.season_name.startswith("Northeast Monsoon"):
            recs.append("Track drainage inspection and culvert clearing prioritized during NE Monsoon.")
        elif "Summer" in risk.season_name:
            recs.append("Track temperature monitoring mandatory; de-stressing and LWR welding restrictions apply > 45°C.")

        date_str = (dt or datetime.now()).strftime("%Y-%m-%d")
        return SeasonalContextResponse(
            section_id=section_id,
            corridor="Chennai Egmore - Thoothukudi",
            date=date_str,
            season=risk.season_name,
            risk=risk,
            live_weather=live,
            recommendations=recs,
        )


seasonal_risk_engine = SeasonalRiskEngine()
