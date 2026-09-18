"""
Unit Tests for Multi-Horizon Synchronization & Human-in-the-Loop Lifecycle Safety.
"""

import pytest
import pandas as pd
from datetime import datetime
from app.services.approval.approval_service import ApprovalService
from app.services.optimization.planning_service import PlanningService
from app.core.exceptions import InvalidApprovalActionException


@pytest.fixture
def services(tmp_path):
    ps = PlanningService()
    appr = ApprovalService()
    # Ensure weekly and monthly plans are generated
    ps.generate_weekly_plan(start_date="2026-09-01")
    ps.generate_monthly_plan(start_date="2026-09-01")
    return ps, appr


def test_execute_unapproved_block_fails(services):
    _, appr = services
    w_df = appr.weekly_repo.read_csv()
    assert not w_df.empty

    # Pick a block in PROPOSED status
    proposed = w_df[w_df["status"] == "PROPOSED"]
    assert not proposed.empty
    test_block_id = proposed.iloc[0]["block_id"]

    # Attempting to execute an unapproved block directly MUST fail
    with pytest.raises(InvalidApprovalActionException) as exc_info:
        appr.record_execution_outcome(test_block_id, {
            "actual_duration_minutes": 110,
            "outcome": "COMPLETED",
            "notes": "Field team finished early"
        })

    assert "Cannot execute unapproved block" in str(exc_info.value)


def test_approve_then_execute_flow_syncs(services):
    _, appr = services
    w_df = appr.weekly_repo.read_csv()
    test_block_id = w_df.iloc[0]["block_id"]
    task_id = w_df.iloc[0].get("task_ids", "")

    # 1. Controller approves the block
    res_appr = appr.approve_block(test_block_id, {
        "approved_by": "Senior Section Engineer / P-Way",
        "role": "Controller",
        "notes": "Approved for possession"
    })
    assert res_appr["status"] == "APPROVED"

    # Verify status in weekly plan
    w_df_after = appr.weekly_repo.read_csv()
    assert w_df_after[w_df_after["block_id"] == test_block_id]["status"].iloc[0] == "APPROVED"

    # 2. Field execution records outcome
    res_exec = appr.record_execution_outcome(test_block_id, {
        "actual_duration_minutes": 115,
        "outcome": "COMPLETED",
        "notes": "Welding and track inspection completed on time"
    })
    assert res_exec["outcome"] == "COMPLETED"

    # Verify status in weekly plan is now EXECUTED
    w_df_final = appr.weekly_repo.read_csv()
    assert w_df_final[w_df_final["block_id"] == test_block_id]["status"].iloc[0] == "EXECUTED"

    # Verify execution was appended to execution_repo
    exec_df = appr.execution_repo.read_csv()
    assert test_block_id in exec_df["block_id"].values


def test_modify_block_syncs(services):
    _, appr = services
    w_df = appr.weekly_repo.read_csv()
    test_block_id = w_df.iloc[0]["block_id"]

    res_mod = appr.modify_block(test_block_id, {
        "new_start_time": "2026-09-01 02:00:00",
        "new_end_time": "2026-09-01 04:30:00",
        "modified_by": "Divisional Operations Controller",
        "role": "Controller",
        "reason": "Adjusted window for freight crossing"
    })
    assert res_mod["status"] == "MODIFIED"
    assert res_mod["new_start_time"] == "2026-09-01 02:00:00"

    w_df_after = appr.weekly_repo.read_csv()
    row = w_df_after[w_df_after["block_id"] == test_block_id].iloc[0]
    assert row["status"] == "MODIFIED"
    assert row["start_time"] == "2026-09-01 02:00:00"


def test_reject_block_syncs(services):
    _, appr = services
    w_df = appr.weekly_repo.read_csv()
    test_block_id = w_df.iloc[-1]["block_id"]

    res_rej = appr.reject_block(test_block_id, {
        "rejected_by": "Chief Dispatcher",
        "role": "Controller",
        "reason": "High passenger traffic density window"
    })
    assert res_rej["status"] == "REJECTED"

    w_df_after = appr.weekly_repo.read_csv()
    row = w_df_after[w_df_after["block_id"] == test_block_id].iloc[0]
    assert row["status"] == "REJECTED"
    assert "rejection_reason" in row and row["rejection_reason"] == "High passenger traffic density window"

    rej_df = appr.rejected_repo.read_csv()
    assert test_block_id in rej_df["block_id"].values
