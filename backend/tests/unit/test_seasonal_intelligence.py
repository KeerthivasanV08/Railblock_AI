"""
Unit tests for Seasonal Intelligence, Live Weather Seam, SRS formula, and Hard Safety Gates.
"""

import pytest
from datetime import datetime
from app.models.seasonal import WeatherStatus, RiskClassification
from app.services.live_weather_service import LiveWeatherService
from app.engines.seasonal_risk_engine import SeasonalRiskEngine
from app.services.seasonal_service import SeasonalService
from app.services.optimization.constraints import ConstraintEngine
from app.core.constants import RejectionReason
import pandas as pd


def test_live_weather_service_csv():
    service = LiveWeatherService()
    report = service.get_live_weather("SEC_001")
    assert report.section_id == "SEC_001"
    assert report.weather_status == WeatherStatus.AVAILABLE
    assert report.weather_source_status == "AVAILABLE"
    assert report.weather_severity is not None
    assert 0.0 <= report.weather_severity <= 100.0


def test_live_weather_service_unavailable_resilience():
    service = LiveWeatherService(data_source="unavailable")
    report = service.get_live_weather("SEC_001")
    assert report.section_id == "SEC_001"
    assert report.weather_status == WeatherStatus.UNKNOWN
    assert report.weather_source_status == "UNAVAILABLE"
    assert report.weather_severity is None


def test_srs_formula_and_asset_multipliers():
    engine = SeasonalRiskEngine()
    test_dt = datetime(2026, 1, 15)  # Winter (score 15.0)

    # Track asset (default 1.0 multiplier)
    track_risk = engine.calculate_srs("SEC_001", asset_type="TRACK", dt=test_dt)
    assert 0.0 <= track_risk.srs <= 100.0
    assert track_risk.asset_multiplier == 1.0

    # OHE asset (1.3 multiplier)
    ohe_risk = engine.calculate_srs("SEC_001", asset_type="OHE", dt=test_dt)
    assert ohe_risk.asset_multiplier >= 1.2
    assert ohe_risk.srs >= track_risk.srs

    # Signal asset (1.1 multiplier)
    signal_risk = engine.calculate_srs("SEC_001", asset_type="SIGNAL", dt=test_dt)
    assert signal_risk.asset_multiplier >= 1.05


def test_srs_when_weather_unavailable():
    engine = SeasonalRiskEngine()
    unavail_service = LiveWeatherService(data_source="unavailable")
    live_unavail = unavail_service.get_live_weather("SEC_001")

    risk = engine.calculate_srs("SEC_001", live_weather=live_unavail)
    assert risk.weather_source_status == "UNAVAILABLE"
    assert risk.live_weather_severity is None
    assert 0.0 <= risk.srs <= 100.0


def test_hard_safety_exclusion_threshold():
    engine = SeasonalRiskEngine()
    # Mock cyclone season (score 75) with extreme weather to exceed threshold
    test_dt = datetime(2026, 11, 15)  # NE Monsoon / Cyclone season
    unavail_service = LiveWeatherService()
    report = unavail_service.get_live_weather("SEC_001")
    report.weather_severity = 95.0

    risk = engine.calculate_srs("SEC_001", asset_type="OHE", dt=test_dt, live_weather=report)
    assert risk.srs >= 75.0
    assert risk.hard_safety_exclusion is True
    assert risk.risk_level == RiskClassification.CRITICAL


def test_constraint_engine_weather_rejection():
    constraint_engine = ConstraintEngine()
    tasks_df = pd.DataFrame([
        {
            "task_id": "TASK_SAFE_01",
            "section_id": "SEC_001",
            "traffic_density": 0.3,
            "machine_available": True,
            "crew_available": True,
            "estimated_duration_minutes": 120,
            "mapped_chainage_km": 5.0,
            "srs": 35.0,
        },
        {
            "task_id": "TASK_HAZARD_02",
            "section_id": "SEC_001",
            "traffic_density": 0.3,
            "machine_available": True,
            "crew_available": True,
            "estimated_duration_minutes": 120,
            "mapped_chainage_km": 5.0,
            "srs": 82.5,
        }
    ])

    result_df = constraint_engine.check_feasibility(tasks_df)
    assert result_df.loc[0, "overall_feasible"] == True
    assert result_df.loc[0, "weather_feasible"] == True
    assert result_df.loc[0, "rejection_reason"] == RejectionReason.NONE.value

    assert result_df.loc[1, "overall_feasible"] == False
    assert result_df.loc[1, "weather_feasible"] == False
    assert result_df.loc[1, "rejection_reason"] == RejectionReason.WEATHER_HAZARD_EXCLUSION.value
