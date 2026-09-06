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
        # Maximize: Priority Score + Integration Bonus + Seasonal Urgency Bonus - Train Delay Penalty
        score_column = "priority_score" if "priority_score" in candidates_df.columns else "criticality_score"
        priority_scores = candidates_df[score_column].fillna(50.0).values
        overlap_bonus = candidates_df.get("spatial_overlap_score", pd.Series(0.5, index=candidates_df.index)).values * 20.0
        train_density = candidates_df.get("traffic_density", pd.Series(0.5, index=candidates_df.index)).values * 30.0
        
        # Seasonal Urgency Bonus: Proactive prioritization for sections with moderate vulnerability (30-74)
        srs_values = candidates_df.get("seasonal_risk_score", pd.Series(0.0, index=candidates_df.index)).fillna(0.0).values
        seasonal_bonus = np.where((srs_values >= 30.0) & (srs_values < 75.0), (srs_values / 75.0) * 15.0, 0.0)

        objective = solver.Objective()
        for i in range(n):
            coeff = float(priority_scores[i] + overlap_bonus[i] + seasonal_bonus[i] - train_density[i])
            objective.SetCoefficient(x[i], coeff)
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

        delay_constraint = solver.Constraint(0, float(max_train_delay_allowance), "max_train_delay")
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

        selected_df = candidates_df.iloc[selected_indices].copy()
        
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
