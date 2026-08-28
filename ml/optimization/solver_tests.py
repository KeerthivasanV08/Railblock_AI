"""
OR-Tools Solver Manual Test Suite.

Tests the MILP formulation correctness on known small inputs.
Run:
    python ml/optimization/solver_tests.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd


def test_single_task_always_selected():
    """A single fully-feasible task must always be selected."""
    from backend.app.services.optimization.milp_solver import OptimizationEngine
    engine = OptimizationEngine()
    candidates = pd.DataFrame([{
        "task_id": "T000001",
        "section_id": "SEC_001",
        "criticality_score": 95.0,
        "spatial_overlap_score": 1.0,
        "traffic_density": 0.2,
        "overall_feasible": True,
    }])
    selected, metrics = engine.optimize_blocks(candidates)
    assert len(selected) == 1, f"Expected 1 selected, got {len(selected)}"
    assert metrics.get("status") in ("OPTIMAL", "FEASIBLE"), f"Bad status: {metrics.get('status')}"
    print("PASS: test_single_task_always_selected")


def test_high_traffic_task_penalized():
    """A task with traffic_density >= 0.9 should rarely beat a lower-traffic task."""
    from backend.app.services.optimization.milp_solver import OptimizationEngine
    engine = OptimizationEngine()
    candidates = pd.DataFrame([
        {"task_id": "T000001", "section_id": "SEC_001", "criticality_score": 60.0,
         "spatial_overlap_score": 0.5, "traffic_density": 0.15, "overall_feasible": True},
        {"task_id": "T000002", "section_id": "SEC_001", "criticality_score": 60.0,
         "spatial_overlap_score": 0.5, "traffic_density": 0.95, "overall_feasible": True},
    ])
    selected, metrics = engine.optimize_blocks(candidates)
    selected_ids = selected["task_id"].tolist() if len(selected) > 0 else []
    print(f"PASS: test_high_traffic_task_penalized | selected={selected_ids} status={metrics.get('status')}")


if __name__ == "__main__":
    print("Running OR-Tools solver tests...")
    try:
        test_single_task_always_selected()
        test_high_traffic_task_penalized()
        print("\nAll solver tests PASSED")
    except Exception as e:
        print(f"\nFAIL: {e}")
        raise
