"""Canonical MDPS feature construction used by training and inference."""

from __future__ import annotations

import numpy as np
import pandas as pd


SEVERITY_MAP = {"A": 3, "B": 2, "C": 1}
TRAFFIC_MAP = {"Low": 1, "Medium": 2, "High": 3, "Critical Peak": 4}
FEATURE_COLUMNS = ["sev_num", "overdue_days", "traffic_num", "deferred_count"]


def build_mdps_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Build the four persisted MDPS features without using target-derived fields."""
    required = {"severity_class", "overdue_days", "deferred_count"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Missing MDPS feature columns: {', '.join(missing)}")

    features = pd.DataFrame(index=frame.index)
    features["sev_num"] = frame["severity_class"].astype("string").str.upper().map(SEVERITY_MAP).fillna(1)
    features["overdue_days"] = pd.to_numeric(frame["overdue_days"], errors="coerce").fillna(0)
    if "traffic_density_class" in frame:
        features["traffic_num"] = frame["traffic_density_class"].astype("string").map(TRAFFIC_MAP).fillna(2)
    elif "traffic_density" in frame:
        traffic = pd.to_numeric(frame["traffic_density"], errors="coerce").fillna(0.5)
        features["traffic_num"] = np.select(
            [traffic < 0.5, traffic < 0.75, traffic < 0.9], [1, 2, 3], default=4
        )
    else:
        features["traffic_num"] = 2
    features["deferred_count"] = pd.to_numeric(frame["deferred_count"], errors="coerce").fillna(0)
    return features[FEATURE_COLUMNS].replace([np.inf, -np.inf], np.nan).fillna(0)


def validate_training_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Return valid training rows and reject missing/non-finite targets."""
    required = {"task_id", "severity_class", "traffic_density_class", "overdue_days", "deferred_count", "actual_priority_rank"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Missing MDPS training columns: {', '.join(missing)}")
    clean = frame.copy()
    clean["actual_priority_rank"] = pd.to_numeric(clean["actual_priority_rank"], errors="coerce")
    clean = clean[np.isfinite(clean["actual_priority_rank"])].copy()
    if clean.empty:
        raise ValueError("MDPS training data contains no valid target rows")
    return clean
