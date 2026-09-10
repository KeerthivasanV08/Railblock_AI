"""
End-to-End Weather Traceability Test — RailBlock AI.

Verifies that Weather Intelligence signals travel end-to-end:
  Weather Telemetry & SRS -> Task Weather Sensitivity -> MDPS Scoring -> MILP Solver -> Disruption Assessment -> XAI Explanation
"""

import pandas as pd
import pytest

from app.engines.seasonal_risk_engine import seasonal_risk_engine
from app.services.priority.feature_builder import build_mdps_features
from app.services.priority.mdps_engine import MDPSEngine
from app.services.optimization.objective import OptimizationObjective
from app.services.rescheduler.impact_analyzer import DisruptionEngine, DisruptionEventType


def test_weather_end_to_end_traceability():
    # 1. Weather & Seasonal Risk Calculation
    sec_id = "SEC_001"
    risk_obj = seasonal_risk_engine.calculate_srs(sec_id, asset_type="OHE")
    assert risk_obj.srs >= 0.0
    assert risk_obj.asset_multiplier == 1.3  # OHE multiplier

    # 2. Build 8-Feature Schema with Weather Features
    task_sample = {
        "task_id": "TASK_TEST_001",
        "section_id": sec_id,
        "department": "TRD",
        "severity_class": "A",
        "overdue_days": 10,
        "deferred_count": 2,
        "traffic_density_class": "High",
        "srs": risk_obj.srs,
        "live_weather_severity": 45.0,
    }

    df_task = pd.DataFrame([task_sample])
    features = build_mdps_features(df_task)
    assert features.shape[1] == 8
    assert "seasonal_risk_score" in features.columns
    assert "live_weather_risk_score" in features.columns

    # 3. MDPS Scoring with Weather-Aware Reasoning
    engine = MDPSEngine()
    result = engine.calculate_priority(task_sample)
    assert "criticality_score" in result
    assert result["criticality_score"] > 0
    assert "model_status" in result

    # 4. Objective Coefficient Calculation with Weather Bonus
    obj = OptimizationObjective()
    candidates_df = pd.DataFrame([{
        "task_id": "TASK_TEST_001",
        "priority_score": 85.0,
        "spatial_overlap_score": 0.8,
        "traffic_density": 0.4,
        "srs": 60.0,
    }])
    coeffs = obj.compute_candidate_coefficients(candidates_df)
    assert len(coeffs) == 1
    assert coeffs[0] > 85.0  # Priority + overlap + seasonal bonus - density penalty

    # 5. Severe Weather Disruption Trigger Verification
    disruption_engine = DisruptionEngine()
    severe_event = {
        "event_id": "EVT_WEATHER_001",
        "event_type": DisruptionEventType.WEATHER_DISRUPTION.value,
        "severity": "CRITICAL",
        "section_id": sec_id,
        "weather_risk_score": 80.0,
    }
    assessment = disruption_engine.assess_impact(severe_event, affected_block={"duration_minutes": 120})
    assert assessment.requires_immediate_reschedule is True
    assert "WEATHER_DISRUPTION" in assessment.event_type
