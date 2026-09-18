"""
Unit Tests for Dynamic 4-Week Monthly Block Planning Engine & API.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.optimization.planning_service import PlanningService


@pytest.fixture
def service():
    return PlanningService()


@pytest.fixture
def client():
    return TestClient(app)


def test_generate_monthly_plan_dynamic_progression(service):
    df = service.generate_monthly_plan(start_date="2026-09-01")
    assert not df.empty, "Monthly plan should not be empty"
    assert set(df["week_number"].unique()) == {1, 2, 3, 4}, "Monthly plan must represent weeks 1 to 4"
    assert (df["horizon"] == "MONTHLY").all(), "All rows must have horizon=MONTHLY"

    # Verify dynamic overdue progression across weeks
    w1_overdue = df[df["week_number"] == 1]["overdue_days_projected"].iloc[0]
    w4_overdue = df[df["week_number"] == 4]["overdue_days_projected"].iloc[0]
    assert w4_overdue > w1_overdue, f"Week 4 overdue ({w4_overdue}) must accumulate over Week 1 ({w1_overdue})"

    # Verify cyclic maintenance injected in week 4 (e.g. ULTRASONIC_RAIL_TEST at interval=4)
    w4_cyclic = df[(df["week_number"] == 4) & (df["maintenance_type"].str.startswith("CYCLIC_"))]
    assert len(w4_cyclic) > 0, "Week 4 must contain injected cyclic maintenance"


def test_monthly_plan_schema_compatibility(service):
    df = service.generate_monthly_plan(start_date="2026-09-01")
    required_cols = [
        "block_id", "section_id", "start_time", "end_time", "duration_minutes",
        "task_ids", "departments", "priority", "optimization_score", "utilization",
        "status", "xai_reason", "week_number", "month_week"
    ]
    for col in required_cols:
        assert col in df.columns, f"Required column '{col}' missing from monthly plan"


def test_monthly_plan_api_endpoint(client):
    response = client.post("/api/planner/monthly?start_date=2026-09-01")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert "monthly_plan" in data
    plan_items = data["monthly_plan"]
    assert len(plan_items) > 0

    weeks = {item.get("week_number") for item in plan_items if "week_number" in item}
    assert 1 in weeks and 4 in weeks
