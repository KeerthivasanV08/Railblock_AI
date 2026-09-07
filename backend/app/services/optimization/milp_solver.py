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

from app.services.optimization.objective import OptimizationObjective, OptimizationObjectiveWeights

logger = logging.getLogger(__name__)


class OptimizationEngine:
    def optimize_blocks(
        self,
        candidates_df: pd.DataFrame,
        max_blocks_per_day: int = 15,
        max_train_delay_allowance: float = 120.0,
        objective_weights: OptimizationObjectiveWeights | None = None,
    ) -> tuple[pd.DataFrame, dict]:
        """
        Solves the integer program selecting the optimal subset of candidate block windows.
        """
        started = time.perf_counter()
        run_id = f"OPT-{uuid4().hex[:12]}"
        if "overall_feasible" in candidates_df.columns:
            candidates_df = pd.DataFrame(candidates_df.loc[candidates_df["overall_feasible"]].copy())

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

        score_column = "priority_score" if "priority_score" in candidates_df.columns else "criticality_score"

        # Multi-Objective Function
        obj_helper = OptimizationObjective(objective_weights)
        coeffs = obj_helper.compute_candidate_coefficients(candidates_df)

        objective = solver.Objective()
        for i in range(n):
            objective.SetCoefficient(x[i], float(coeffs[i]))
        objective.SetMaximization()

        # Constraint 1: Maximum total blocks limit
        max_blocks_constraint = solver.Constraint(0, max_blocks_per_day, "max_blocks")
        for i in range(n):
            max_blocks_constraint.SetCoefficient(x[i], 1)

        # Constraint 2: Maximum total train delay allowance
        if "estimated_train_delay_min" in candidates_df.columns:
            delay_coeffs = candidates_df["estimated_train_delay_min"].fillna(0.0).values
        else:
            dens = candidates_df.get("traffic_density", pd.Series(0.4, index=candidates_df.index)).fillna(0.4).values
            delay_coeffs = np.clip(dens * 25.0, 5.0, 45.0)

        delay_constraint = solver.Constraint(0.0, max_train_delay_allowance, "max_train_delay")
        for i in range(n):
            delay_constraint.SetCoefficient(x[i], float(delay_coeffs[i]))

        # Constraint 3: Machine / Fleet resource availability limits
        resource_fleet_limits = {
            "Ballast Cleaning Machine": 3,
            "Tamping Machine": 4,
            "Tower Wagon": 6,
        }
        if "required_resource_type" in candidates_df.columns:
            for res_type, max_limit in resource_fleet_limits.items():
                res_indices = [i for i, val in enumerate(candidates_df["required_resource_type"].values) if str(val) == res_type]
                if res_indices:
                    res_constraint = solver.Constraint(0, max_limit, f"res_limit_{res_type[:10]}")
                    for idx in res_indices:
                        res_constraint.SetCoefficient(x[idx], 1)

        # Constraint 4: Section concurrency conflict
        if "section_id" in candidates_df.columns:
            sec_map = {}
            for i, sec in enumerate(candidates_df["section_id"].values):
                if pd.notna(sec):
                    sec_map.setdefault(str(sec), []).append(i)

            for sec, indices in sec_map.items():
                if len(indices) > 2:
                    sec_constraint = solver.Constraint(0, 3, f"sec_concurrency_{sec[:12]}")
                    for idx in indices:
                        sec_constraint.SetCoefficient(x[idx], 1)

        status = solver.Solve()

        selected_indices = []
        if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
            for i in range(n):
                if x[i].solution_value() > 0.5:
                    selected_indices.append(i)

        selected_df = pd.DataFrame(candidates_df.iloc[selected_indices].copy())
        
        # Calculate optimization score and summary statistics
        opt_val = solver.Objective().Value() if len(selected_indices) > 0 else 0.0
        selected_delays = float(np.sum([delay_coeffs[i] for i in selected_indices])) if selected_indices else 0.0
        
        resource_usage = {}
        if "required_resource_type" in selected_df.columns and len(selected_df) > 0:
            resource_usage = selected_df["required_resource_type"].value_counts().to_dict()

        integrated_count = 0
        if "integrated_block_candidate" in selected_df.columns and len(selected_df) > 0:
            integrated_count = int(selected_df["integrated_block_candidate"].sum())

        metrics = {
            "status": "OPTIMAL" if status == pywraplp.Solver.OPTIMAL else "FEASIBLE",
            "solver_name": solver.SolverVersion(),
            "candidate_count": n,
            "selected_count": len(selected_df),
            "objective_value": round(opt_val, 2),
            "total_estimated_delay_min": round(selected_delays, 1),
            "integrated_blocks_selected": integrated_count,
            "resource_allocation": resource_usage,
            "run_id": run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "runtime_ms": round((time.perf_counter() - started) * 1000, 2),
            "configuration": {
                "max_blocks_per_day": max_blocks_per_day,
                "max_train_delay_allowance": max_train_delay_allowance,
                "fleet_limits": resource_fleet_limits,
                "hard_filter": "overall_feasible == true",
                "objective_weights": obj_helper.weights.to_dict(),
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
