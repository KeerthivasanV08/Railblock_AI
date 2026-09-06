"""
Unit tests for OR-Tools MILP Block Optimization Engine.
"""

import pytest
import pandas as pd
import numpy as np
from app.services.optimization.milp_solver import OptimizationEngine


@pytest.fixture
def sample_candidates():
    records = []
    for i in range(25):
        records.append({
            "task_id": f"TASK_{i:04d}",
            "section_id": f"SEC_{i % 5:03d}",
            "priority_score": 50.0 + (i * 2.0),
            "spatial_overlap_score": 0.8 if i % 2 == 0 else 0.2,
            "traffic_density": 0.3 + (i % 4) * 0.15,
            "required_resource_type": "Ballast Cleaning Machine" if i < 8 else ("Tower Wagon" if i < 16 else "S&T crew"),
            "estimated_train_delay_min": 15.0 + (i % 3) * 5.0,
            "integrated_block_candidate": i % 2 == 0,
            "overall_feasible": True
        })
    return pd.DataFrame(records)


def test_solver_selects_optimal_subset(sample_candidates):
    engine = OptimizationEngine()
    selected_df, metrics = engine.optimize_blocks(
        candidates_df=sample_candidates,
        max_blocks_per_day=10,
        max_train_delay_allowance=200.0
    )

    assert metrics["status"] in ("OPTIMAL", "FEASIBLE")
    assert len(selected_df) <= 10
    assert len(selected_df) > 0
    assert "optimization_score" in selected_df.columns
    assert metrics["total_estimated_delay_min"] <= 200.0 + 1e-3


def test_solver_respects_max_blocks_per_day(sample_candidates):
    engine = OptimizationEngine()
    selected_df, metrics = engine.optimize_blocks(
        candidates_df=sample_candidates,
        max_blocks_per_day=4,
        max_train_delay_allowance=500.0
    )

    assert len(selected_df) <= 4
    assert metrics["selected_count"] <= 4


def test_solver_respects_resource_fleet_limits(sample_candidates):
    engine = OptimizationEngine()
    selected_df, metrics = engine.optimize_blocks(
        candidates_df=sample_candidates,
        max_blocks_per_day=20,
        max_train_delay_allowance=1000.0
    )

    # Ballast Cleaning Machine limit is 3
    if "required_resource_type" in selected_df.columns:
        bcm_count = (selected_df["required_resource_type"] == "Ballast Cleaning Machine").sum()
        assert bcm_count <= 3


def test_solver_handles_empty_candidates():
    engine = OptimizationEngine()
    selected_df, metrics = engine.optimize_blocks(pd.DataFrame())

    assert len(selected_df) == 0
    assert metrics["status"] == "NO_FEASIBLE_SOLUTION"


def test_solver_handles_all_infeasible(sample_candidates):
    engine = OptimizationEngine()
    infeasible_df = sample_candidates.copy()
    infeasible_df["overall_feasible"] = False

    selected_df, metrics = engine.optimize_blocks(infeasible_df)
    assert len(selected_df) == 0
    assert metrics["status"] == "NO_FEASIBLE_SOLUTION"
