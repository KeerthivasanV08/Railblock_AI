"""
Data Ingestion Service for RailBlock AI.

Orchestrates raw data ingestion, task unification (TMS, SMMS, TDMS), and file contract verification.
"""

from datetime import datetime
import pandas as pd
from app.config.settings import settings
from app.repositories.csv_repository import CSVRepository
from app.core.constants import DEFECT_RESOURCE_MAPPING


class IngestionService:
    def __init__(self):
        self.raw_dir = settings.RAW_DATA_ROOT
        self.processed_dir = settings.PROCESSED_DATA_ROOT

    def unify_maintenance_tasks(self, planning_date: str = None) -> pd.DataFrame:
        """
        Merges TMS, SMMS, and TDMS defects into unified_maintenance_tasks.csv.
        """
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        tms_df = CSVRepository(self.raw_dir / "defects/tms_defects.csv").read_csv()
        smms_df = CSVRepository(self.raw_dir / "defects/smms_defects.csv").read_csv()
        tdms_df = CSVRepository(self.raw_dir / "defects/tdms_defects.csv").read_csv()

        tms_df["department"] = "Engineering"
        tms_df["location_reference_type"] = "CHAINAGE"
        tms_df["location_reference_id"] = tms_df["task_id"]

        smms_df["department"] = "S&T"
        smms_df["location_reference_type"] = "SIGNAL"
        smms_df["location_reference_id"] = smms_df["signal_id"]
        smms_df["start_km"] = None
        smms_df["end_km"] = None

        tdms_df["department"] = "TRD"
        tdms_df["location_reference_type"] = "MAST"
        tdms_df["location_reference_id"] = tdms_df["mast_number"]
        tdms_df["start_km"] = None
        tdms_df["end_km"] = None

        cols = [
            "task_id", "department", "section_id", "location_reference_type", "location_reference_id",
            "start_km", "end_km", "defect_type", "severity_class", "logged_date", "target_completion_date",
            "deferred_count", "status"
        ]

        unified_df = pd.concat([tms_df[cols], smms_df[cols], tdms_df[cols]], ignore_index=True)

        # Overdue calculation
        p_dt = datetime.fromisoformat(planning_date) if planning_date else datetime(2024, 12, 31)
        target_dts = pd.to_datetime(unified_df["target_completion_date"])
        unified_df["overdue_days"] = (p_dt - target_dts).dt.days.clip(lower=0)

        # Resource type & duration
        unified_df["required_resource_type"] = unified_df["defect_type"].map(DEFECT_RESOURCE_MAPPING).fillna("Engineering crew")
        unified_df["estimated_duration_minutes"] = 120

        out_path = self.processed_dir / "unified_maintenance_tasks.csv"
        CSVRepository(out_path).write_csv(unified_df)
        return unified_df
