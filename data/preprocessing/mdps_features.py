"""Canonical MDPS feature construction used by training and inference."""

from __future__ import annotations

import numpy as np
import pandas as pd


SEVERITY_MAP = {"A": 3, "B": 2, "C": 1}
TRAFFIC_MAP = {"Low": 1, "Medium": 2, "High": 3, "Critical Peak": 4}
BASE_FEATURE_COLUMNS = ["sev_num", "overdue_days", "traffic_num", "deferred_count"]
WEATHER_FEATURE_COLUMNS = [
    "seasonal_risk_score",
    "live_weather_risk_score",
    "weather_maintenance_suitability",
    "task_weather_sensitivity",
]
FEATURE_COLUMNS = BASE_FEATURE_COLUMNS + WEATHER_FEATURE_COLUMNS


def build_mdps_features(frame: pd.DataFrame, include_weather: bool = True) -> pd.DataFrame:
    """Build canonical MDPS features including normalized task-aware weather risk features."""
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

    # Seasonal Risk Score (Normalized 0.0 - 1.0)
    if "srs" in frame.columns:
        srs_raw = pd.to_numeric(frame["srs"], errors="coerce").fillna(35.0)
    elif "seasonal_risk_score" in frame.columns:
        srs_raw = pd.to_numeric(frame["seasonal_risk_score"], errors="coerce").fillna(35.0)
    else:
        srs_raw = pd.Series(35.0, index=frame.index)
    features["seasonal_risk_score"] = np.clip(srs_raw / 100.0, 0.0, 1.0)

    # Live Weather Risk Score (Normalized 0.0 - 1.0)
    if "live_weather_severity" in frame.columns:
        lwr_raw = pd.to_numeric(frame["live_weather_severity"], errors="coerce").fillna(20.0)
    elif "live_weather_risk_score" in frame.columns:
        lwr_raw = pd.to_numeric(frame["live_weather_risk_score"], errors="coerce").fillna(20.0)
    else:
        lwr_raw = pd.Series(20.0, index=frame.index)
    features["live_weather_risk_score"] = np.clip(lwr_raw / 100.0, 0.0, 1.0)

    # Weather Maintenance Suitability (1.0 - combined risk)
    combined_risk = (features["seasonal_risk_score"] * 0.4) + (features["live_weather_risk_score"] * 0.6)
    features["weather_maintenance_suitability"] = np.clip(1.0 - combined_risk, 0.0, 1.0)

    # Task / Asset Weather Sensitivity
    if "department" in frame.columns or "asset_type" in frame.columns:
        dept = frame.get("department", frame.get("asset_type", pd.Series("", index=frame.index))).astype("string").str.upper()
        sensitivity = np.select(
            [dept.str.contains("OHE|TRD|ELECTRICAL"), dept.str.contains("SIGNAL|S&T|TELECOM")],
            [1.3, 1.1],
            default=1.0,
        )
    else:
        sensitivity = np.full(len(frame), 1.0)
    features["task_weather_sensitivity"] = sensitivity

    cols = FEATURE_COLUMNS if include_weather else BASE_FEATURE_COLUMNS
    return features[cols].replace([np.inf, -np.inf], np.nan).fillna(0)


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

