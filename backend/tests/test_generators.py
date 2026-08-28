"""
Tests for RailBlock AI Synthetic Data Generators.
"""

import pytest
from pathlib import Path
import pandas as pd

from data.generators.config import (
    RAW_DIR,
    MIN_TMS_ROWS,
    MIN_SMMS_ROWS,
    MIN_TDMS_ROWS,
    MIN_TRAIN_ROWS,
    MIN_DELAY_ROWS,
    MIN_GOODS_ROWS,
    MIN_SLOT_ROWS,
    MIN_HISTORICAL_ROWS,
    MIN_MDPS_LABEL_ROWS,
    MIN_DISRUPTION_ROWS,
)


def test_network_files_exist_and_valid():
    stations = pd.read_csv(RAW_DIR / "network/stations.csv")
    sections = pd.read_csv(RAW_DIR / "network/block_sections.csv")
    geometry = pd.read_csv(RAW_DIR / "network/track_geometry.csv")
    masts = pd.read_csv(RAW_DIR / "network/ohe_mast_reference.csv")
    signals = pd.read_csv(RAW_DIR / "network/signal_reference.csv")

    assert len(stations) >= 40
    assert len(sections) >= 30
    assert stations["station_code"].is_unique
    assert sections["section_id"].is_unique
    assert (sections["start_km"] < sections["end_km"]).all()


def test_defect_files_row_counts():
    tms = pd.read_csv(RAW_DIR / "defects/tms_defects.csv")
    smms = pd.read_csv(RAW_DIR / "defects/smms_defects.csv")
    tdms = pd.read_csv(RAW_DIR / "defects/tdms_defects.csv")

    assert len(tms) >= MIN_TMS_ROWS
    assert len(smms) >= MIN_SMMS_ROWS
    assert len(tdms) >= MIN_TDMS_ROWS

    assert tms["task_id"].is_unique
    assert smms["task_id"].is_unique
    assert tdms["task_id"].is_unique


def test_traffic_files_row_counts():
    timetable = pd.read_csv(RAW_DIR / "traffic/train_timetable.csv")
    delays = pd.read_csv(RAW_DIR / "traffic/live_train_delays.csv")
    goods = pd.read_csv(RAW_DIR / "traffic/goods_forecast.csv")
    slots = pd.read_csv(RAW_DIR / "traffic/corridor_slot_availability.csv")

    assert len(timetable) >= MIN_TRAIN_ROWS
    assert len(delays) >= MIN_DELAY_ROWS
    assert len(goods) >= MIN_GOODS_ROWS
    assert len(slots) >= MIN_SLOT_ROWS

    assert slots["slot_id"].is_unique


def test_historical_and_disruptions():
    hist = pd.read_csv(RAW_DIR / "historical/historical_block_records.csv")
    mdps = pd.read_csv(RAW_DIR / "historical/mdps_training_labels.csv")
    disrupt = pd.read_csv(RAW_DIR / "disruptions/disruption_events.csv")

    assert len(hist) >= MIN_HISTORICAL_ROWS
    assert len(mdps) >= MIN_MDPS_LABEL_ROWS
    assert len(disrupt) >= MIN_DISRUPTION_ROWS

    assert hist["record_id"].is_unique
    assert disrupt["event_id"].is_unique
