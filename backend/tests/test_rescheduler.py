"""
Unit and Integration Tests for Rescheduler Constraint Validation and Policy Engine.
"""

import pytest
from app.services.rescheduler.policy_engine import ReschedulerEngine
from app.services.rescheduler.rescheduler_service import ReschedulingService
from app.services.optimization.constraints import ConstraintEngine


def test_constraint_engine_single_feasible_candidate():
    engine = ConstraintEngine()
    candidate = {
        "section_id": "SEC_001",
        "traffic_density": 0.4,
        "machine_available": True,
        "crew_available": True,
        "duration_minutes": 120,
        "mapped_chainage_km": 15.2,
        "spatial_mapping_status": "MAPPED",
    }
    result = engine.check_feasibility_single(candidate)
    assert result["feasible"] is True
    assert result["rejection_reason"] == "NONE"
    assert len(result["failed_constraints"]) == 0
    assert len(result["satisfied_constraints"]) == 5


def test_constraint_engine_single_infeasible_candidate():
    engine = ConstraintEngine()
    # High traffic density
    candidate_traffic = {
        "section_id": "SEC_001",
        "traffic_density": 0.92,
        "machine_available": True,
        "crew_available": True,
        "duration_minutes": 120,
        "mapped_chainage_km": 15.2,
    }
    res_traffic = engine.check_feasibility_single(candidate_traffic)
    assert res_traffic["feasible"] is False
    assert "traffic" in res_traffic["failed_constraints"]
    assert res_traffic["rejection_reason"] == "NO_TRAFFIC_GAP"

    # Missing machine
    candidate_machine = {
        "section_id": "SEC_001",
        "traffic_density": 0.4,
        "machine_available": False,
        "crew_available": True,
        "duration_minutes": 120,
        "mapped_chainage_km": 15.2,
    }
    res_machine = engine.check_feasibility_single(candidate_machine)
    assert res_machine["feasible"] is False
    assert "machine" in res_machine["failed_constraints"]
    assert res_machine["rejection_reason"] == "MACHINE_UNAVAILABLE"


def test_rescheduler_engine_generates_and_validates_candidates():
    engine = ReschedulerEngine()
    disruption = {"event_id": "DIS_TEST_01", "section_id": "SEC_001", "severity": "High"}
    block = {
        "block_id": "BLK_TEST_01",
        "section_id": "SEC_001",
        "criticality_score": 85.0,
        "duration_minutes": 180,
        "mapped_chainage_km": 10.5,
        "spatial_mapping_status": "MAPPED",
        "required_machine_type": "TAMPING_MACHINE",
        "required_crew_count": 2,
    }
    options = engine.generate_reschedule_options(disruption, block)
    assert len(options) == 3
    for opt in options:
        assert "feasible" in opt
        assert "failed_constraints" in opt
        assert "rejection_reason" in opt
        assert "action_type" in opt
        assert opt["action_type"] in ["delay", "shift", "reallocate"]
        if opt["feasible"]:
            assert opt["optimization_score"] > 0
        else:
            assert opt["optimization_score"] == 0.0


def test_rescheduler_service_approval_enforcement():
    service = ReschedulingService()
    # Reject approval if not confirmed feasible
    unconfirmed = service.accept_reschedule_option(
        option_id="BLK-RESCHED-A-01",
        actor="TestController",
        confirmed_feasible=False,
    )
    assert unconfirmed["status"] == "REJECTED_PENDING_VALIDATION"

    # Accept when confirmed feasible
    confirmed = service.accept_reschedule_option(
        option_id="BLK-RESCHED-A-01",
        actor="TestController",
        confirmed_feasible=True,
    )
    assert confirmed["status"] == "ACCEPTED"
    assert confirmed["accepted_by"] == "TestController"
