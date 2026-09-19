"""
Unit Tests for 26-Week Rolling Block Planning Engine.
"""

import pytest
from app.services.optimization.planning_service import PlanningService


@pytest.fixture
def service():
    return PlanningService()


def test_generate_rolling_plan_structure(service):
    df = service.generate_rolling_plan(start_date="2026-08-26", horizon_weeks=4, persist=False)
    assert not df.empty
    assert "week_number" in df.columns
    assert "overdue_days_projected" in df.columns
    assert "seasonal_risk_score_projected" in df.columns
    assert "maintenance_type" in df.columns

    # Verify weeks 1 to 4 are represented
    assert set(df["week_number"].unique()) == {1, 2, 3, 4}


def test_rolling_plan_escalates_overdue_days(service):
    df = service.generate_rolling_plan(start_date="2026-08-26", horizon_weeks=8, persist=False)
    w1_overdue = df[df["week_number"] == 1]["overdue_days_projected"].iloc[0]
    w8_overdue = df[df["week_number"] == 8]["overdue_days_projected"].iloc[0]
    # Week 8 must accumulate overdue days over Week 1
    assert w8_overdue > w1_overdue


def test_rolling_plan_injects_cyclic_maintenance(service):
    df = service.generate_rolling_plan(start_date="2026-08-26", horizon_weeks=12, persist=False)
    # Check for presence of cyclic blocks
    cyclic_blocks = df[df["maintenance_type"].str.startswith("CYCLIC_")]
    assert len(cyclic_blocks) > 0


def test_generate_rolling_plan_full_26_weeks(service):
    """Verify that full 26-week horizon is completely generated with all 26 weeks populated."""
    df = service.generate_rolling_plan(start_date="2026-08-26", horizon_weeks=26, persist=True)
    assert not df.empty
    assert len(df) == 93

    # All weeks 1 through 26 must exist
    unique_weeks = set(df["week_number"].unique())
    assert unique_weeks == set(range(1, 27))

    # Verify Weeks 13 through 26 specifically
    for wk in range(13, 27):
        wk_blocks = df[df["week_number"] == wk]
        assert len(wk_blocks) >= 3, f"Week {wk} should have at least 3 blocks scheduled"
        assert not wk_blocks["block_id"].isnull().any()
        assert not wk_blocks["section_id"].isnull().any()
        assert not wk_blocks["departments"].isnull().any()
        assert (wk_blocks["duration_minutes"] > 0).all()
        assert (wk_blocks["priority"] > 0).all()

