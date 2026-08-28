"""
Departmental Task Unification Engine for RailBlock AI.

Combines TMS (Track), SMMS (Signal), and TDMS (TRD) defects into unified_maintenance_tasks.csv.
"""

import logging
from datetime import datetime
import pandas as pd

from data.preprocessing.config import RAW_DIR, PROCESSED_DIR, DEFECT_DURATION_MAP
from data.generators.config import DEFECT_RESOURCE_MAPPING

logger = logging.getLogger(__name__)


def unify_maintenance_tasks() -> pd.DataFrame:
    """
    Reads TMS, SMMS, and TDMS defects and unifies them into a single schema.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    tms_path = RAW_DIR / "defects/tms_defects.csv"
    smms_path = RAW_DIR / "defects/smms_defects.csv"
    tdms_path = RAW_DIR / "defects/tdms_defects.csv"

    tms_df = pd.read_csv(tms_path)
    smms_df = pd.read_csv(smms_path)
    tdms_df = pd.read_csv(tdms_path)

    # 1. Process TMS
    tms_df["department"] = "Engineering"
    tms_df["location_reference_type"] = "CHAINAGE"
    tms_df["location_reference_id"] = tms_df["task_id"]

    # 2. Process SMMS
    smms_df["department"] = "S&T"
    smms_df["location_reference_type"] = "SIGNAL"
    smms_df["location_reference_id"] = smms_df["signal_id"]
    smms_df["start_km"] = float("nan")
    smms_df["end_km"] = float("nan")

    # 3. Process TDMS
    tdms_df["department"] = "TRD"
    tdms_df["location_reference_type"] = "MAST"
    tdms_df["location_reference_id"] = tdms_df["mast_number"]
    tdms_df["start_km"] = float("nan")
    tdms_df["end_km"] = float("nan")

    common_cols = [
        "task_id", "department", "section_id", "location_reference_type", "location_reference_id",
        "start_km", "end_km", "defect_type", "severity_class", "logged_date", "target_completion_date",
        "deferred_count", "status"
    ]

    unified_df = pd.concat([tms_df[common_cols], smms_df[common_cols], tdms_df[common_cols]], ignore_index=True)

    # Compute overdue_days based on target_completion_date vs reference time
    ref_date = datetime(2024, 12, 31)
    target_dates = pd.to_datetime(unified_df["target_completion_date"])
    unified_df["overdue_days"] = (ref_date - target_dates).dt.days.clip(lower=0)

    # Infer required resource type and estimated duration
    unified_df["required_resource_type"] = unified_df["defect_type"].map(DEFECT_RESOURCE_MAPPING).fillna("Engineering crew")
    unified_df["estimated_duration_minutes"] = unified_df["defect_type"].map(DEFECT_DURATION_MAP).fillna(120)

    # Sort deterministically
    unified_df = unified_df.sort_values("task_id").reset_index(drop=True)

    out_path = PROCESSED_DIR / "unified_maintenance_tasks.csv"
    unified_df.to_csv(out_path, index=False)
    logger.info(f"Generated {len(unified_df)} unified maintenance tasks at {out_path}")

    return unified_df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unify_maintenance_tasks()

