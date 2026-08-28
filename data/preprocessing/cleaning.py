"""
Data Cleaning Module for RailBlock AI Preprocessing.
"""

import logging
import pandas as pd

logger = logging.getLogger(__name__)


def clean_dataframe(df: pd.DataFrame, drop_duplicates: bool = True) -> pd.DataFrame:
    """
    Cleans DataFrame by removing duplicates, stripping whitespace, and handling missing values.
    """
    cleaned_df = df.copy()

    # Strip whitespace from string columns
    str_cols = cleaned_df.select_dtypes(include=["object", "string"]).columns
    for col in str_cols:
        cleaned_df[col] = cleaned_df[col].astype(str).str.strip()

    if drop_duplicates:
        cleaned_df = cleaned_df.drop_duplicates()

    return cleaned_df

