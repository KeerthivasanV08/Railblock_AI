"""
Temporal window clustering helper service for grouping maintenance tasks by time availability.
"""

from typing import List, Dict, Any
import pandas as pd


class TemporalClusteringService:
    def cluster_by_time_window(self, tasks_df: pd.DataFrame, max_gap_hours: float = 4.0) -> pd.DataFrame:
        # Pass-through or time-window grouping helper
        return tasks_df
