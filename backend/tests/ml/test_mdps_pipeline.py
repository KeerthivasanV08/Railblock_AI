import numpy as np
import pandas as pd

from backend.app.engines.mdps_engine import MDPSEngine
from data.preprocessing.mdps_features import FEATURE_COLUMNS, build_mdps_features


def test_mdps_feature_builder_is_schema_stable_and_handles_missing_values():
    frame = pd.DataFrame([{
        "severity_class": "A",
        "overdue_days": np.nan,
        "deferred_count": 2,
        "traffic_density": np.inf,
    }])
    features = build_mdps_features(frame)
    assert features.columns.tolist() == FEATURE_COLUMNS
    assert np.isfinite(features.to_numpy()).all()
    assert features.iloc[0]["sev_num"] == 3


def test_mdps_inference_is_deterministic_and_bounded():
    engine = MDPSEngine()
    task = {
        "severity_class": "A",
        "overdue_days": 18,
        "deferred_count": 3,
        "traffic_density": 0.94,
        "defect_type": "Weld Failure",
    }
    first = engine.calculate_priority(task)
    second = engine.calculate_priority(task)
    assert first["criticality_score"] == second["criticality_score"]
    assert 0 <= first["criticality_score"] <= 100
    assert first["priority_band"] in {"Critical", "High", "Medium", "Low"}
    assert first["priority_reason"]
