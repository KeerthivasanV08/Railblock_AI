"""
CSV Storage & Manipulation Utility Functions for RailBlock AI.
"""

import math
import os
from pathlib import Path
from typing import Any
import pandas as pd
from backend.app.core.exceptions import DataFileNotFoundException, InvalidCSVSchemaException


def _resolve_csv_path(file_path: Path) -> Path:
    """Resolve repository-relative CSV paths without allowing path traversal."""
    path = Path(file_path)
    if not path.is_absolute():
        from backend.app.core.config import settings

        path = settings.BASE_DIR / path
    return path.resolve()


def safe_read_csv(file_path: Path, expected_columns: list = None) -> pd.DataFrame:
    """
    Safely reads CSV file, validating existence and schema.
    """
    resolved_path = _resolve_csv_path(file_path)
    if not resolved_path.exists():
        raise DataFileNotFoundException(str(resolved_path))

    try:
        df = pd.read_csv(resolved_path, encoding="utf-8")
    except Exception as exc:
        raise DataFileNotFoundException(str(resolved_path)) from exc

    if expected_columns:
        missing = [col for col in expected_columns if col not in df.columns]
        if missing:
            raise InvalidCSVSchemaException(str(resolved_path), missing)

    return df


def atomic_write_csv(df: pd.DataFrame, file_path: Path):
    """
    Writes DataFrame to CSV atomically using a temporary file.
    """
    file_path = _resolve_csv_path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = file_path.with_suffix(file_path.suffix + ".tmp")
    df.to_csv(temp_path, index=False)
    os.replace(temp_path, file_path)


def append_row_csv(row_dict: dict, file_path: Path, expected_columns: list = None):
    """
    Appends a single row dictionary to a CSV file safely.
    """
    if file_path.exists():
        df = pd.read_csv(file_path)
        new_df = pd.concat([df, pd.DataFrame([row_dict])], ignore_index=True)
    else:
        new_df = pd.DataFrame([row_dict])

    atomic_write_csv(new_df, file_path)


def sanitize_for_json(value: Any) -> Any:
    """Convert pandas/numpy scalar leakage and non-finite values into JSON-safe data."""
    if isinstance(value, dict):
        return {str(k): sanitize_for_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_for_json(v) for v in value]
    if isinstance(value, tuple):
        return [sanitize_for_json(v) for v in value]
    if pd.isna(value) if not isinstance(value, (list, tuple, dict)) else False:
        return None
    if hasattr(value, "item"):
        try:
            value = value.item()
        except Exception:
            pass
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value
