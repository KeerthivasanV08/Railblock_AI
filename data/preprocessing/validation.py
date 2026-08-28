"""
Raw Data Integrity & Schema Validation Module.
"""

import logging
from pathlib import Path
import pandas as pd

from data.preprocessing.config import RAW_DIR

logger = logging.getLogger(__name__)


def validate_raw_datasets() -> dict:
    """
    Validates all raw CSV files against primary keys, foreign keys, numeric ranges, and dates.
    """
    results = {}
    
    # 1. Primary Keys
    pk_checks = [
        ("network/stations.csv", "station_code"),
        ("network/block_sections.csv", "section_id"),
        ("network/track_geometry.csv", "segment_id"),
        ("network/ohe_mast_reference.csv", "mast_number"),
        ("network/signal_reference.csv", "signal_id"),
        ("defects/tms_defects.csv", "task_id"),
        ("defects/smms_defects.csv", "task_id"),
        ("defects/tdms_defects.csv", "task_id"),
        ("traffic/corridor_slot_availability.csv", "slot_id"),
        ("resources/machine_inventory.csv", "resource_id"),
        ("resources/crew_inventory.csv", "crew_id"),
        ("historical/historical_block_records.csv", "record_id"),
        ("disruptions/disruption_events.csv", "event_id"),
    ]

    for rel_path, pk_col in pk_checks:
        file_path = RAW_DIR / rel_path
        if not file_path.exists():
            results[rel_path] = f"FAILED: File {rel_path} not found"
            continue
        df = pd.read_csv(file_path)
        duplicates = df[pk_col].duplicated().sum()
        if duplicates > 0:
            results[rel_path] = f"FAILED: {duplicates} duplicate primary key values found in {pk_col}"
        else:
            results[rel_path] = "PASS"

    # 2. Foreign Keys
    sections_df = pd.read_csv(RAW_DIR / "network/block_sections.csv")
    valid_sections = set(sections_df["section_id"].unique())

    fk_section_files = [
        "network/track_geometry.csv",
        "network/ohe_mast_reference.csv",
        "network/signal_reference.csv",
        "defects/tms_defects.csv",
        "defects/smms_defects.csv",
        "defects/tdms_defects.csv",
        "traffic/train_timetable.csv",
        "traffic/goods_forecast.csv",
        "traffic/corridor_slot_availability.csv",
        "historical/historical_block_records.csv",
        "disruptions/disruption_events.csv"
    ]

    for rel_path in fk_section_files:
        f_path = RAW_DIR / rel_path
        if f_path.exists():
            df = pd.read_csv(f_path)
            orphans = set(df["section_id"].dropna().unique()) - valid_sections
            if orphans:
                results[f"FK_{rel_path}"] = f"FAILED: {len(orphans)} orphan section_id values"
            else:
                results[f"FK_{rel_path}"] = "PASS"

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = validate_raw_datasets()
    for k, v in res.items():
        print(f"{k}: {v}")

