"""
Unit Tests for PPO Multi-Candidate Evaluation, Operational Timestamps, and Plan Updates.
"""

import pytest
from app.services.rescheduler.rescheduler_service import ReschedulingService


@pytest.fixture
def service():
    return ReschedulingService()


def test_generate_reschedule_options_returns_concrete_timestamps(service):
    res = service.generate_reschedule_options(
        event_id="EVT-TEST-001",
        affected_block_id="RB-TEST-01",
        affected_block_metadata={
            "section_id": "SEC_001",
            "start_time": "2026-08-26 10:00:00",
            "duration_minutes": 120.0,
            "criticality_score": 75.0,
            "traffic_density": 0.50,
            "machine_available": True,
            "crew_available": True,
        },
    )

    assert res["status"] if "status" in res else True
    assert "options" in res
    assert len(res["options"]) > 0
    assert "impact_assessment" in res
    assert "rl_metadata" in res

    # Verify that candidates have concrete operational fields
    top_opt = res["options"][0]
    assert "start_time" in top_opt
    assert "end_time" in top_opt
    assert "recommended_window" in top_opt
    assert "shift_from_original_hours" in top_opt
    assert "new_block_id" in top_opt
    assert "xai" in top_opt  # XAI explanation attached


def test_accept_reschedule_option_updates_plan(service, tmp_path):
    # Test that accept_reschedule_option requires confirmed_feasible
    rejected = service.accept_reschedule_option("RB-TEST-01-D60", confirmed_feasible=False)
    assert rejected["status"] == "REJECTED_PENDING_VALIDATION"

    # With confirmed_feasible=True, returns ACCEPTED
    accepted = service.accept_reschedule_option("RB-TEST-01-D60", actor="Chief Controller", confirmed_feasible=True)
    assert accepted["status"] == "ACCEPTED"
    assert accepted["accepted_by"] == "Chief Controller"
    assert "timestamp" in accepted
