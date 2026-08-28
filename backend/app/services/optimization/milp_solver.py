"""
OR-Tools Block Schedule Optimization Engine for RailBlock AI.

Uses Google OR-Tools Linear/Integer Programming (pywraplp) to solve the 
Multi-Variable Maintenance Block Selection & Scheduling Optimization Problem.
"""

import logging
import time
from datetime import datetime, timezone
from uuid import uuid4
import numpy as np
import pandas as pd
from ortools.linear_solver import pywraplp

logger = logging.getLogger(__name__)


class OptimizationEngine:
    def optimize_blocks(
        self,
        candidates_df: pd.DataFrame,
        max_blocks_per_day: int = 15,
        max_train_delay_allowance: float = 120.0
    ) -> tuple[pd.DataFrame, dict]:
        """
        Solves the integer program selecting the optimal subset of candidate block windows.
        """
        started = time.perf_counter()
        run_id = f"OPT-{uuid4().hex[:12]}"
        if "overall_feasible" in candidates_df.columns:
            candidates_df = candidates_df[candidates_df["overall_feasible"]].copy()

        if len(candidates_df) == 0:
            return pd.DataFrame(), {
                "status": "NO_FEASIBLE_SOLUTION",
                "reason": "No feasible candidates were available after hard constraint filtering.",
                "candidate_count": 0,
                "selected_count": 0,
                "run_id": run_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "runtime_ms": round((time.perf_counter() - started) * 1000, 2),
            }

        solver = pywraplp.Solver.CreateSolver("SCIP")
        if not solver:
            solver = pywraplp.Solver.CreateSolver("CBC")

        n = len(candidates_df)
        x = {}
        for i in range(n):
            x[i] = solver.BoolVar(f"select_block_{i}")

        # Objective Function Weights
        # Maximize: Priority Score + Integration Bonus - Train Delay Penalty
        score_column = "priority_score" if "priority_score" in candidates_df.columns else "criticality_score"
        priority_scores = candidates_df[score_column].fillna(50.0).values
        overlap_bonus = candidates_df.get("spatial_overlap_score", pd.Series(0.5, index=candidates_df.index)).values * 20.0
        train_density = candidates_df.get("traffic_density", pd.Series(0.5, index=candidates_df.index)).values * 30.0

        objective = solver.Objective()
        for i in range(n):
            coeff = float(priority_scores[i] + overlap_bonus[i] - train_density[i])
            objective.SetCoefficient(x[i], coeff)
        objective.SetMaximization()

        # Constraint 1: Maximum total blocks limit
        max_blocks_constraint = solver.Constraint(0, max_blocks_per_day, "max_blocks")
        for i in range(n):
            max_blocks_constraint.SetCoefficient(x[i], 1)

        status = solver.Solve()

        selected_indices = []
        if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
            for i in range(n):
                if x[i].solution_value() > 0.5:
                    selected_indices.append(i)

        selected_df = candidates_df.iloc[selected_indices].copy()
        
        # Calculate optimization score
        opt_val = solver.Objective().Value() if len(selected_indices) > 0 else 0.0
        metrics = {
            "status": "OPTIMAL" if status == pywraplp.Solver.OPTIMAL else "FEASIBLE",
            "solver_name": solver.SolverVersion(),
            "candidate_count": n,
            "selected_count": len(selected_df),
            "objective_value": round(opt_val, 2),
            "run_id": run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "runtime_ms": round((time.perf_counter() - started) * 1000, 2),
            "configuration": {
                "max_blocks_per_day": max_blocks_per_day,
                "max_train_delay_allowance": max_train_delay_allowance,
                "hard_filter": "overall_feasible == true",
            },
        }
        if not selected_indices:
            metrics["status"] = "NO_FEASIBLE_SOLUTION"
            metrics["reason"] = "Solver returned no selected candidate blocks."

        selected_scores = selected_df[score_column].fillna(50.0).to_numpy(dtype=float)
        selected_df["optimization_score"] = np.round(
            np.clip(selected_scores * 0.7 + 30.0, 50.0, 99.0),
            2
        )

        return selected_df, metrics
