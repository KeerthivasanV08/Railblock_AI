"""
Spatial cluster boundary helper service.
"""

from typing import List, Dict, Any
import pandas as pd


class SpatialClusterService:
    def __init__(self, proximity_threshold_km: float = 2.0):
        self.proximity_threshold_km = proximity_threshold_km

    def calculate_corridor_density(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty or "mapped_chainage_km" not in df.columns:
            return {"task_count": len(df), "mean_density": 0.0}
        return {
            "task_count": len(df),
            "chainage_span_km": float(df["mapped_chainage_km"].max() - df["mapped_chainage_km"].min()),
        }
