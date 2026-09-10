"""
Optimization Objective Formulation for RailBlock AI MILP Solver.

Defines the mathematical multi-objective trade-offs between:
  1. Maintenance Risk Reduction (MDPS Criticality Coverage)
  2. Multi-Department Mega-Block Integration (Shadow-Block Spatial Overlap)
  3. Proactive Seasonal Urgency (Seasonal Risk Score — SRS)
  4. Passenger Timetable Disruption Minimization (Traffic Corridor Density & Delay)
  5. Machine & Fleet Repositioning Friction
  6. Unused Possession Buffer Minimization (Wastage Prevention)
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional
import numpy as np
import pandas as pd


@dataclass
class OptimizationObjectiveWeights:
    """
    Calibrated multi-objective weights for RailBlock AI integer programming solver.

    Mathematical formulation:
      Maximize:
        w_priority * MDPS_i
        + w_overlap * SpatialOverlap_i
        + w_seasonal * ProactiveSRS_i
        - w_density * TrafficDensity_i
        - w_delay * EstimatedDelay_i
        - w_wastage * UnusedMinutes_i
    """
    priority_weight: float = 1.0               # lambda_priority: MDPS score (0-100)
    overlap_bonus_weight: float = 20.0         # lambda_overlap: spatial-temporal consolidation bonus
    seasonal_bonus_weight: float = 15.0        # lambda_seasonal: proactive pre-monsoon/hazard urgency
    train_density_penalty: float = 30.0        # lambda_density: traffic density friction
    train_delay_penalty: float = 0.5           # lambda_delay: per-minute expected train delay penalty
    resource_movement_penalty: float = 5.0     # lambda_resource: repositioning distance penalty
    possession_wastage_penalty: float = 0.15   # lambda_wastage: penalty for excessive unused possession buffer

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


class OptimizationObjective:
    """Compatibility shim and objective calculation engine."""
    # Preserved class attributes for backward compatibility
    PRIORITY_WEIGHT = 1.0
    OVERLAP_BONUS_WEIGHT = 20.0
    TRAIN_DENSITY_PENALTY_WEIGHT = 30.0

    def __init__(self, weights: Optional[OptimizationObjectiveWeights] = None):
        self.weights = weights or OptimizationObjectiveWeights()

    def compute_candidate_coefficients(self, candidates_df: pd.DataFrame) -> np.ndarray:
        """
        Computes composite objective coefficients for each candidate block in candidates_df.
        """
        score_column = "priority_score" if "priority_score" in candidates_df.columns else "criticality_score"
        priority_scores = candidates_df.get(score_column, pd.Series(50.0, index=candidates_df.index)).fillna(50.0).values

        overlap = candidates_df.get("spatial_overlap_score", pd.Series(0.5, index=candidates_df.index)).fillna(0.5).values
        train_density = candidates_df.get("traffic_density", pd.Series(0.5, index=candidates_df.index)).fillna(0.5).values

        # Seasonal Urgency: Proactive prioritization for sections with moderate vulnerability (30 <= SRS < 75)
        if "srs" in candidates_df.columns:
            srs_raw = pd.to_numeric(candidates_df["srs"], errors="coerce").fillna(35.0).values
        elif "seasonal_risk_score" in candidates_df.columns:
            srs_val = pd.to_numeric(candidates_df["seasonal_risk_score"], errors="coerce").fillna(0.35).values
            srs_raw = np.where(srs_val <= 1.0, srs_val * 100.0, srs_val)
        else:
            srs_raw = np.full(len(candidates_df), 35.0)

        seasonal_bonus = np.where(
            (srs_raw >= 30.0) & (srs_raw < 75.0),
            (srs_raw / 75.0) * self.weights.seasonal_bonus_weight,
            0.0
        )

        coeffs = (
            (priority_scores * self.weights.priority_weight) +
            (overlap * self.weights.overlap_bonus_weight) +
            seasonal_bonus -
            (train_density * self.weights.train_density_penalty)
        )
        return coeffs.astype(float)

    def sensitivity_analysis(
        self,
        base_coefficients: np.ndarray,
        variation_pct: float = 0.20
    ) -> Dict[str, Any]:
        """
        Performs sensitivity analysis on objective coefficients under parameter variation.
        """
        lower = base_coefficients * (1.0 - variation_pct)
        upper = base_coefficients * (1.0 + variation_pct)
        return {
            "variation_pct": variation_pct,
            "mean_base_coefficient": round(float(np.mean(base_coefficients)), 2),
            "mean_lower_bound": round(float(np.mean(lower)), 2),
            "mean_upper_bound": round(float(np.mean(upper)), 2),
            "stability_ratio": round(float(np.std(base_coefficients) / max(1.0, np.mean(base_coefficients))), 4),
        }
