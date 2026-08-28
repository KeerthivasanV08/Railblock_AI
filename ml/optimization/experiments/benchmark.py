"""
OR-Tools Solver Benchmark for RailBlock AI.

Benchmarks OptimizationEngine across varying candidate set sizes.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pandas as pd


def generate_candidates(n: int) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "task_id": [f"T{i:06d}" for i in range(n)],
        "section_id": [f"SEC_{i%5:03d}" for i in range(n)],
        "criticality_score": rng.uniform(40, 100, n),
        "spatial_overlap_score": rng.uniform(0.3, 1.0, n),
        "traffic_density": rng.uniform(0.1, 0.85, n),
        "overall_feasible": np.ones(n, dtype=bool),
    })


def run_benchmark():
    from backend.app.services.optimization.milp_solver import OptimizationEngine

    engine = OptimizationEngine()
    sizes = [50, 100, 500, 1000]
    results = []

    for n in sizes:
        candidates = generate_candidates(n)
        t0 = time.perf_counter()
        selected_df, metrics = engine.optimize_blocks(candidates)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        results.append({
            "candidate_count": n,
            "selected_count": len(selected_df),
            "status": metrics.get("status"),
            "objective_value": metrics.get("objective_value"),
            "runtime_ms": elapsed_ms,
        })
        print(f"n={n:5d}: status={metrics.get('status')}, selected={len(selected_df)}, time={elapsed_ms}ms")

    return results


if __name__ == "__main__":
    run_benchmark()
