"""
RL Environment State Definition — RailBlock AI.

Encodes the operational context of a disrupted maintenance block possession into
a normalized 12-dimensional continuous feature vector for PPO neural inference.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np


@dataclass
class BlockPlanState:
    """
    Normalized operational context for a railway maintenance block under disruption.
    """
    traffic_density: float = 0.5
    remaining_window_min: float = 120.0
    delay_magnitude_min: float = 0.0
    overdue_tasks_count: int = 1
    machine_available: bool = True
    crew_available: bool = True
    weather_risk_score: float = 30.0
    section_vulnerability: float = 0.5
    asset_type_code: float = 0.0  # 0.0 = Track, 0.5 = Signal, 1.0 = OHE
    priority_score: float = 75.0
    hour_of_day: int = 12
    days_deferred: int = 0

    def to_vector(self) -> np.ndarray:
        """
        Flattens operational state to a normalized 12-dimensional float32 vector.
        Each feature is scaled roughly to [0.0, 1.0].
        """
        vec = np.array([
            float(np.clip(self.traffic_density, 0.0, 1.0)),
            float(np.clip(self.remaining_window_min / 240.0, 0.0, 1.5)),
            float(np.clip(self.delay_magnitude_min / 120.0, 0.0, 2.0)),
            float(np.clip(self.overdue_tasks_count / 10.0, 0.0, 2.0)),
            1.0 if self.machine_available else 0.0,
            1.0 if self.crew_available else 0.0,
            float(np.clip(self.weather_risk_score / 100.0, 0.0, 1.0)),
            float(np.clip(self.section_vulnerability, 0.0, 1.0)),
            float(np.clip(self.asset_type_code, 0.0, 1.0)),
            float(np.clip(self.priority_score / 100.0, 0.0, 1.0)),
            float(np.clip(self.hour_of_day / 24.0, 0.0, 1.0)),
            float(np.clip(self.days_deferred / 5.0, 0.0, 2.0)),
        ], dtype=np.float32)
        return vec

    @staticmethod
    def dim() -> int:
        """Number of continuous state features."""
        return 12
