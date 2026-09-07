"""
Unit Tests for 26-Week Rolling Block Planning Engine.
"""

import pytest
from app.services.optimization.planning_service import PlanningService


@pytest.fixture
def service():
    return PlanningService()


def test_generate_rolling_plan_structure(service):
    df = service.generate_rolling_plan(start_date="2026-08-26", horizon_weeks=4)
    assert not df.empty
    assert "week_number" in df.columns
    assert "overdue_days_projected" in df.columns
    assert "seasonal_risk_score_projected" in df.columns
    assert "maintenance_type" in df.columns

    # Verify weeks 1 to 4 are represented
    assert set(df["week_number"].unique()) == {1, 2, 3, 4}


def test_rolling_plan_escalates_overdue_days(service):
    df = service.generate_rolling_plan(start_date="2026-08-26", horizon_weeks=8)
    w1_overdue = df[df["week_number"] == 1]["overdue_days_projected"].iloc[0]
    w8_overdue = df[df["week_number"] == 8]["overdue_days_projected"].iloc[0]
    # Week 8 must accumulate overdue days over Week 1
    assert w8_overdue > w1_overdue


def test_rolling_plan_injects_cyclic_maintenance(service):
    df = service.generate_rolling_plan(start_date="2026-08-26", horizon_weeks=12)
    # Check for presence of cyclic blocks
    cyclic_blocks = df[df["maintenance_type"].str.startswith("CYCLIC_")]
    assert len(cyclic_blocks) > 0
