"""
Unit Tests for Disruption Event Classification & Multi-Dimensional Impact Assessment.
"""

import pytest
from app.services.rescheduler.impact_analyzer import DisruptionEngine, DisruptionEventType, DisruptionImpactAssessment


@pytest.fixture
def engine():
    return DisruptionEngine()


def test_classify_event_types(engine):
    assert engine.classify_event_type("late train") == DisruptionEventType.LATE_TRAIN
    assert engine.classify_event_type("emergency defect") == DisruptionEventType.EMERGENCY_DEFECT
    assert engine.classify_event_type("rail fracture") == DisruptionEventType.EMERGENCY_DEFECT
    assert engine.classify_event_type("machine failure") == DisruptionEventType.MACHINE_DELAY
    assert engine.classify_event_type("block overrun") == DisruptionEventType.BLOCK_OVERRUN
    assert engine.classify_event_type("weather disruption") == DisruptionEventType.WEATHER_DISRUPTION
    assert engine.classify_event_type("CREW_DELAY") == DisruptionEventType.CREW_DELAY
    assert engine.classify_event_type("INFRASTRUCTURE_FAILURE") == DisruptionEventType.INFRASTRUCTURE_FAILURE


def test_assess_impact_moderate_late_train(engine):
    event = {
        "event_id": "EVT-101",
        "event_type": "Late Train",
        "section_id": "SEC_005",
        "severity": "Medium",
        "delay_minutes": 45.0,
    }
    block = {
        "block_id": "RB-501",
        "duration_minutes": 120.0,
        "priority_score": 75.0,
        "traffic_density": 0.60,
        "machine_available": True,
        "crew_available": True,
    }
    assessment = engine.assess_impact(event, block)

    assert isinstance(assessment, DisruptionImpactAssessment)
    assert assessment.event_type == DisruptionEventType.LATE_TRAIN.value
    assert assessment.schedule_delay_min == 45.0
    assert assessment.train_conflicts_count >= 1
    assert 0.0 <= assessment.composite_impact_score <= 100.0
    assert assessment.maintenance_mdps_exposure == 75.0
    assert "Impact Score:" in assessment.impact_summary


def test_assess_impact_emergency_defect_triggers_immediate_reschedule(engine):
    event = {
        "event_id": "EVT-EMG-01",
        "event_type": "Emergency Defect",
        "section_id": "SEC_030",
        "severity": "Critical",
    }
    block = {
        "block_id": "RB-301",
        "priority_score": 95.0,
        "machine_available": True,
        "crew_available": True,
    }
    assessment = engine.assess_impact(event, block)
    assert assessment.requires_immediate_reschedule is True
    assert assessment.event_type == DisruptionEventType.EMERGENCY_DEFECT.value


def test_assess_impact_machine_unavailability(engine):
    event = {
        "event_id": "EVT-RES-02",
        "event_type": "Resource Unavailable",
        "section_id": "SEC_012",
        "severity": "High",
    }
    block = {
        "block_id": "RB-121",
        "machine_available": False,
        "crew_available": True,
    }
    assessment = engine.assess_impact(event, block)
    assert assessment.resource_impact_score >= 70.0
    assert assessment.requires_immediate_reschedule is True
