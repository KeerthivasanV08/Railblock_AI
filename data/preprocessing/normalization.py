"""
Data Normalization Module for RailBlock AI Preprocessing.
"""

import logging
import pandas as pd

logger = logging.getLogger(__name__)


def normalize_categories(df: pd.DataFrame, col_mappings: dict = None) -> pd.DataFrame:
    """
    Normalizes categorical columns using standardized vocabulary.
    """
    norm_df = df.copy()

    # Standard uppercase for severity
    if "severity_class" in norm_df.columns:
        norm_df["severity_class"] = norm_df["severity_class"].astype(str).str.upper()

    # Standard title case for status and department
    if "status" in norm_df.columns:
        norm_df["status"] = norm_df["status"].astype(str).str.title()

    if "department" in norm_df.columns:
        norm_df["department"] = norm_df["department"].astype(str).str.title()

    if col_mappings:
        for col, mapping in col_mappings.items():
            if col in norm_df.columns:
                norm_df[col] = norm_df[col].map(mapping).fillna(norm_df[col])

    return norm_df

