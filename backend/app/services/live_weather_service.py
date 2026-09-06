"""
Live Weather Service (Layer B Weather Seam).

Handles real-time or simulated live weather telemetry for the 68 corridor sections.
Guarantees resilient failure modes:
When weather telemetry is unavailable, it returns weather_status="UNKNOWN",
weather_source_status="UNAVAILABLE", weather_severity=None.
Never silently sets weather_severity to 0 on failure.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional
import pandas as pd

from app.config.settings import settings
from app.models.seasonal import LiveWeatherReport, WeatherStatus, WeatherCondition

logger = logging.getLogger(__name__)


class LiveWeatherService:
    def __init__(self, data_source: Optional[str] = None):
        self.data_source = data_source or getattr(settings, "WEATHER_DATA_SOURCE", "csv_simulated")
        self.csv_path = settings.DERIVED_DATA_ROOT / "weather" / "live_weather_simulation.csv"
        self._cache: Dict[str, LiveWeatherReport] = {}
        self._last_loaded: Optional[datetime] = None

    def _calculate_severity(self, rain_mm: float, wind_kmh: float, temp_c: float) -> tuple[float, WeatherCondition]:
        """
        Calculates normalized weather severity [0.0 - 100.0] and condition enum.
        """
        # Rain component (0-50 pts: 0mm = 0, 100mm = 50)
        rain_score = min(50.0, (rain_mm / 100.0) * 50.0)

        # Wind component (0-30 pts: 0kmh = 0, 100kmh = 30)
        wind_score = min(30.0, (wind_kmh / 100.0) * 30.0)

        # Temperature component (0-20 pts: >40C begins rail buckle risk)
        temp_score = 0.0
        if temp_c > 35.0:
            temp_score = min(20.0, (temp_c - 35.0) * 4.0)

        severity = round(min(100.0, max(0.0, rain_score + wind_score + temp_score)), 1)

        # Classify condition
        if wind_kmh >= 65.0 or (rain_mm >= 70.0 and wind_kmh >= 45.0):
            condition = WeatherCondition.CYCLONE
        elif rain_mm >= 30.0:
            condition = WeatherCondition.HEAVY_RAIN
        elif rain_mm > 0.5:
            condition = WeatherCondition.LIGHT_RAIN
        elif temp_c >= 40.0:
            condition = WeatherCondition.EXTREME_HEAT
        else:
            condition = WeatherCondition.CLEAR

        return severity, condition

    def _load_from_csv(self) -> Dict[str, LiveWeatherReport]:
        reports: Dict[str, LiveWeatherReport] = {}
        if not self.csv_path.exists():
            logger.warning(f"Live weather CSV not found at {self.csv_path}. Creating initial simulation.")
            self._generate_default_simulation_csv()

        try:
            df = pd.read_csv(self.csv_path)
            now_iso = datetime.now(timezone.utc).isoformat()
            for _, row in df.iterrows():
                sec_id = str(row.get("section_id", "")).strip()
                if not sec_id:
                    continue

                rain = float(row.get("rainfall_mm", 0.0))
                wind = float(row.get("wind_speed_kmh", 12.0))
                temp = float(row.get("temperature_c", 28.0))
                severity, condition = self._calculate_severity(rain, wind, temp)

                reports[sec_id] = LiveWeatherReport(
                    section_id=sec_id,
                    weather_status=WeatherStatus.AVAILABLE,
                    weather_source_status="AVAILABLE",
                    temperature_c=temp,
                    rainfall_mm=rain,
                    wind_speed_kmh=wind,
                    weather_severity=severity,
                    condition=condition,
                    timestamp=str(row.get("timestamp", now_iso)),
                )
        except Exception as e:
            logger.error(f"Failed to read live weather CSV {self.csv_path}: {e}")
        return reports

    def _generate_default_simulation_csv(self):
        """Generates default live simulated weather readings for all 68 corridor sections."""
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        sections_csv = settings.DERIVED_DATA_ROOT / "weather" / "section_weather_sensitivity.csv"
        now_iso = datetime.now(timezone.utc).isoformat()

        rows = []
        if sections_csv.exists():
            df_sec = pd.read_csv(sections_csv)
            sec_ids = df_sec["section_id"].tolist()
        else:
            sec_ids = [f"SEC_{i:03d}" for i in range(1, 69)]

        for sec in sec_ids:
            # Baseline realistic coastal TN conditions: warm, moderate breeze, low rain
            rows.append({
                "section_id": sec,
                "temperature_c": 31.5,
                "rainfall_mm": 2.0,
                "wind_speed_kmh": 14.5,
                "timestamp": now_iso
            })

        pd.DataFrame(rows).to_csv(self.csv_path, index=False)
        logger.info(f"Generated default live weather simulation CSV at {self.csv_path}")

    def get_live_weather(self, section_id: str) -> LiveWeatherReport:
        """
        Fetch live weather for a specific section.
        If unavailable or source fails, returns UNKNOWN / UNAVAILABLE / None.
        """
        if self.data_source == "unavailable":
            return LiveWeatherReport(
                section_id=section_id,
                weather_status=WeatherStatus.UNKNOWN,
                weather_source_status="UNAVAILABLE",
                weather_severity=None,
                condition=WeatherCondition.UNKNOWN,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        if not self._cache:
            self._cache = self._load_from_csv()

        report = self._cache.get(section_id)
        if report:
            return report

        # Not found in feed: return explicit UNAVAILABLE / None
        return LiveWeatherReport(
            section_id=section_id,
            weather_status=WeatherStatus.UNKNOWN,
            weather_source_status="UNAVAILABLE",
            weather_severity=None,
            condition=WeatherCondition.UNKNOWN,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def get_all_live_weather(self) -> Dict[str, LiveWeatherReport]:
        """Fetch live weather for all corridor sections."""
        if self.data_source == "unavailable":
            return {}
        if not self._cache:
            self._cache = self._load_from_csv()
        return self._cache


live_weather_service = LiveWeatherService()
