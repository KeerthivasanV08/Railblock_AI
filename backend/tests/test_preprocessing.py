"""
Tests for Preprocessing Pipeline Components.
"""

import pytest
import pandas as pd
from data.preprocessing.config import PROCESSED_DIR, MODELS_DIR


def test_processed_files_exist():
    unified = pd.read_csv(PROCESSED_DIR / "unified_maintenance_tasks.csv")
    mapped = pd.read_csv(PROCESSED_DIR / "spatially_mapped_tasks.csv")
    scored = pd.read_csv(PROCESSED_DIR / "scored_tasks.csv")
    clustered = pd.read_csv(PROCESSED_DIR / "clustered_tasks.csv")
    feasibility = pd.read_csv(PROCESSED_DIR / "feasibility_checked_tasks.csv")

    assert len(unified) >= 80000
    assert set(["Engineering", "S&T", "TRD"]).issubset(set(unified["department"]))
    assert "criticality_score" in scored.columns
    assert "cluster_id" in clustered.columns
    assert "overall_feasible" in feasibility.columns


def test_mdps_model_artifacts_exist():
    assert (MODELS_DIR / "mdps_model.pkl").exists()
    assert (MODELS_DIR / "mdps_scaler.pkl").exists()
    assert (MODELS_DIR / "model_metrics.json").exists()

