"""
Tests for Data Referential Integrity and Numeric Bounds.
"""

import pytest
import pandas as pd
from data.generators.config import RAW_DIR


def test_foreign_key_integrity():
    sections = pd.read_csv(RAW_DIR / "network/block_sections.csv")
    valid_secs = set(sections["section_id"].unique())

    tms = pd.read_csv(RAW_DIR / "defects/tms_defects.csv")
    smms = pd.read_csv(RAW_DIR / "defects/smms_defects.csv")
    tdms = pd.read_csv(RAW_DIR / "defects/tdms_defects.csv")

    assert set(tms["section_id"]).issubset(valid_secs)
    assert set(smms["section_id"]).issubset(valid_secs)
    assert set(tdms["section_id"]).issubset(valid_secs)


def test_asset_references():
    signals = pd.read_csv(RAW_DIR / "network/signal_reference.csv")
    masts = pd.read_csv(RAW_DIR / "network/ohe_mast_reference.csv")

    smms = pd.read_csv(RAW_DIR / "defects/smms_defects.csv")
    tdms = pd.read_csv(RAW_DIR / "defects/tdms_defects.csv")

    assert set(smms["signal_id"]).issubset(set(signals["signal_id"]))
    assert set(tdms["mast_number"]).issubset(set(masts["mast_number"]))


def test_demanded_vs_granted_discrepancy():
    hist = pd.read_csv(RAW_DIR / "historical/historical_block_records.csv")
    assert (hist["granted_window_minutes"] <= hist["requested_window_minutes"]).all()


def test_delays_and_temporal_consistency():
    delays = pd.read_csv(RAW_DIR / "traffic/live_train_delays.csv")
    assert (delays["delay_minutes"] >= 0).all()
    # Ensure delay matches non-negative offset
    assert (delays["delay_reason"].isin(["Congestion", "Technical", "Weather", "Other"])).all()
