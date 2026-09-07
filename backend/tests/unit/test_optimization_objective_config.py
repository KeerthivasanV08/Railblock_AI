"""
Unit Tests for Configurable Optimization Objective Formulation.
"""

import numpy as np
import pandas as pd
import pytest
from app.services.optimization.objective import OptimizationObjective, OptimizationObjectiveWeights


def test_objective_weights_default():
    weights = OptimizationObjectiveWeights()
    assert weights.priority_weight == 1.0
    assert weights.overlap_bonus_weight == 20.0
    assert weights.seasonal_bonus_weight == 15.0
    assert weights.train_density_penalty == 30.0


def test_compute_candidate_coefficients():
    obj = OptimizationObjective()
    df = pd.DataFrame([
        {
            "priority_score": 80.0,
            "spatial_overlap_score": 0.8,
            "traffic_density": 0.3,
            "seasonal_risk_score": 50.0,
        },
        {
            "priority_score": 60.0,
            "spatial_overlap_score": 0.2,
            "traffic_density": 0.8,
            "seasonal_risk_score": 10.0,
        },
    ])
    coeffs = obj.compute_candidate_coefficients(df)
    assert len(coeffs) == 2
    # Candidate 1 (high priority, high overlap, low traffic) should score higher than Candidate 2
    assert coeffs[0] > coeffs[1]


def test_sensitivity_analysis():
    obj = OptimizationObjective()
    base = np.array([80.0, 95.0, 110.0, 70.0])
    res = obj.sensitivity_analysis(base, variation_pct=0.15)
    assert res["variation_pct"] == 0.15
    assert res["mean_lower_bound"] < res["mean_base_coefficient"] < res["mean_upper_bound"]
