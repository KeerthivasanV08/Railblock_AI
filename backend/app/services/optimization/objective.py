"""
Optimization objective formulation helper.
"""

from typing import Dict, Any


class OptimizationObjective:
    """Defines coefficient weights for MILP optimization objective function."""
    PRIORITY_WEIGHT = 1.0
    OVERLAP_BONUS_WEIGHT = 20.0
    TRAIN_DENSITY_PENALTY_WEIGHT = 30.0
