"""
Data Normalization Service for RailBlock AI.
"""

import pandas as pd


class NormalizationService:
    def normalize_task_categories(self, df: pd.DataFrame) -> pd.DataFrame:
        norm_df = df.copy()
        if "severity_class" in norm_df.columns:
            norm_df["severity_class"] = norm_df["severity_class"].astype(str).str.upper()
        if "status" in norm_df.columns:
            norm_df["status"] = norm_df["status"].astype(str).str.title()
        if "department" in norm_df.columns:
            norm_df["department"] = norm_df["department"].astype(str).str.strip()
        return norm_df
