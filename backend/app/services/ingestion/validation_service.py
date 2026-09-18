"""
Structured CSV data validation for RailBlock AI.

The CSV files remain the source of truth. Validation reports source quality and
processing-layer deduplication guidance without mutating supplied datasets.
"""

from datetime import datetime, timezone
from typing import Any, cast

import numpy as np
import pandas as pd

from app.config.settings import settings
from app.repositories.csv_repository import CSVRepository
from app.utils.csv_utils import sanitize_for_json


class ValidationService:
    def __init__(self):
        self.raw_dir = settings.RAW_DATA_ROOT
        self.schemas = self._build_schemas()

    def _build_schemas(self) -> dict[str, dict[str, Any]]:
        return {
            "network/stations.csv": {
                "key": ["station_code"],
                "required": ["station_code", "station_name", "chainage_km", "division", "latitude", "longitude"],
                "numeric": ["chainage_km", "latitude", "longitude"],
            },
            "network/block_sections.csv": {
                "key": ["section_id"],
                "required": ["section_id", "from_station", "to_station", "start_km", "end_km", "line_type", "num_lines", "max_speed_kmph"],
                "numeric": ["start_km", "end_km", "num_lines", "max_speed_kmph"],
            },
            "network/track_geometry.csv": {
                "key": ["segment_id"],
                "required": ["segment_id", "section_id", "start_km", "end_km", "latitude_start", "longitude_start", "latitude_end", "longitude_end"],
                "numeric": ["start_km", "end_km", "latitude_start", "longitude_start", "latitude_end", "longitude_end"],
                "foreign_keys": {"section_id": "network/block_sections.csv"},
            },
            "network/ohe_mast_reference.csv": {
                "key": ["mast_number"],
                "required": ["mast_number", "section_id", "equivalent_km"],
                "numeric": ["equivalent_km"],
                "foreign_keys": {"section_id": "network/block_sections.csv"},
            },
            "network/signal_reference.csv": {
                "key": ["signal_id"],
                "required": ["signal_id", "signal_type", "section_id", "equivalent_km"],
                "numeric": ["equivalent_km"],
                "foreign_keys": {"section_id": "network/block_sections.csv"},
            },
            "defects/tms_defects.csv": {
                "key": ["task_id"],
                "required": ["task_id", "section_id", "start_km", "end_km", "defect_type", "severity_class", "logged_date", "target_completion_date", "deferred_count", "status"],
                "numeric": ["start_km", "end_km", "deferred_count"],
                "timestamps": ["logged_date", "target_completion_date"],
                "enums": {"severity_class": ["A", "B", "C"]},
                "foreign_keys": {"section_id": "network/block_sections.csv"},
            },
            "defects/smms_defects.csv": {
                "key": ["task_id"],
                "required": ["task_id", "section_id", "signal_id", "defect_type", "severity_class", "logged_date", "target_completion_date", "deferred_count", "status"],
                "numeric": ["deferred_count"],
                "timestamps": ["logged_date", "target_completion_date"],
                "enums": {"severity_class": ["A", "B", "C"]},
                "foreign_keys": {"section_id": "network/block_sections.csv"},
            },
            "defects/tdms_defects.csv": {
                "key": ["task_id"],
                "required": ["task_id", "section_id", "mast_number", "defect_type", "severity_class", "logged_date", "target_completion_date", "deferred_count", "status"],
                "numeric": ["deferred_count"],
                "timestamps": ["logged_date", "target_completion_date"],
                "enums": {"severity_class": ["A", "B", "C"]},
                "foreign_keys": {"section_id": "network/block_sections.csv"},
            },
            "traffic/train_timetable.csv": {
                "key": ["train_number", "section_id", "scheduled_departure", "scheduled_arrival", "day_of_week"],
                "required": ["train_number", "train_type", "section_id", "scheduled_departure", "scheduled_arrival", "priority_class", "day_of_week"],
                "timestamps": ["scheduled_departure", "scheduled_arrival"],
                "enums": {"train_type": ["Passenger", "Express", "Freight"]},
                "foreign_keys": {"section_id": "network/block_sections.csv"},
            },
            "traffic/live_train_delays.csv": {
                "key": ["train_number", "date", "scheduled_time"],
                "required": ["train_number", "date", "scheduled_time", "actual_time", "delay_minutes", "delay_reason"],
                "numeric": ["delay_minutes"],
                "timestamps": ["date", "scheduled_time", "actual_time"],
                "enums": {"delay_reason": ["Congestion", "Technical", "Weather", "Other"]},
                "deduplication": "Processing layer keeps the latest/highest-delay conflicting event per train/date/scheduled_time and drops exact duplicate rows.",
            },
            "traffic/goods_forecast.csv": {
                "key": ["section_id", "forecast_date", "commodity_type"],
                "required": ["section_id", "forecast_date", "expected_rakes", "commodity_type", "seasonal_factor"],
                "numeric": ["expected_rakes", "seasonal_factor"],
                "timestamps": ["forecast_date"],
                "foreign_keys": {"section_id": "network/block_sections.csv"},
            },
            "traffic/corridor_slot_availability.csv": {
                "key": ["slot_id"],
                "required": ["slot_id", "section_id", "window_start", "window_end", "passenger_traffic_density", "is_blocked"],
                "numeric": ["passenger_traffic_density"],
                "timestamps": ["window_start", "window_end"],
                "foreign_keys": {"section_id": "network/block_sections.csv"},
            },
            "resources/machine_inventory.csv": {
                "key": ["resource_id"],
                "required": ["resource_id", "resource_type", "home_depot", "current_latitude", "current_longitude", "is_available", "last_updated"],
                "numeric": ["current_latitude", "current_longitude"],
                "timestamps": ["last_updated"],
            },
            "resources/crew_inventory.csv": {
                "key": ["crew_id"],
                "required": ["crew_id", "department", "home_depot", "shift_start", "shift_end", "headcount", "is_available"],
                "numeric": ["headcount"],
                "timestamps": ["shift_start", "shift_end"],
                "enums": {"department": ["Engineering", "S&T", "TRD"]},
            },
            "historical/historical_block_records.csv": {
                "key": ["record_id"],
                "required": ["record_id", "task_id", "department", "section_id", "requested_window_minutes", "granted_window_minutes", "outcome", "was_deferred"],
                "numeric": ["requested_window_minutes", "granted_window_minutes"],
                "foreign_keys": {"section_id": "network/block_sections.csv"},
            },
            "historical/mdps_training_labels.csv": {
                "key": ["task_id"],
                "required": ["task_id", "severity_class", "overdue_days", "traffic_density_class", "deferred_count", "actual_priority_rank"],
                "numeric": ["overdue_days", "deferred_count", "actual_priority_rank"],
                "enums": {"severity_class": ["A", "B", "C"], "traffic_density_class": ["Low", "Medium", "High", "Critical Peak"]},
            },
            "disruptions/disruption_events.csv": {
                "key": ["event_id"],
                "required": ["event_id", "event_type", "section_id", "detected_at", "affected_block_id", "impact_description", "severity"],
                "timestamps": ["detected_at"],
                "foreign_keys": {"section_id": "network/block_sections.csv"},
            },
            "calendars/seasonal_calendar.csv": {
                "key": ["date"],
                "required": ["date", "season", "risk_factor", "operational_speed_penalty"],
                "numeric": ["risk_factor", "operational_speed_penalty"],
                "timestamps": ["date"],
            },
            "calendars/festival_traffic_calendar.csv": {
                "key": ["festival_name", "start_date", "end_date"],
                "required": ["festival_name", "start_date", "end_date", "traffic_surge_factor"],
                "numeric": ["traffic_surge_factor"],
                "timestamps": ["start_date", "end_date"],
            },
        }

    def validate_all_datasets(self) -> dict[str, Any]:
        section_ids = self._reference_values("network/block_sections.csv", "section_id")
        station_ids = self._reference_values("network/stations.csv", "station_code")
        reports: list[dict[str, Any]] = []

        for rel_path, schema in self.schemas.items():
            reports.append(self._validate_dataset(rel_path, schema, section_ids, station_ids))

        status = "PASS"
        if any(report["errors"] for report in reports):
            status = "ERROR"
        elif any(report["warnings"] for report in reports):
            status = "WARNING"

        return sanitize_for_json({
            "status": status,
            "validation_timestamp": datetime.now(timezone.utc).isoformat(),
            "data_source": "csv",
            "source_of_truth": "repository_csv_files",
            "datasets_checked": len(reports),
            "datasets": reports,
            "summary": {
                "total_rows": sum(report["row_count"] for report in reports),
                "valid_rows": sum(report["valid_rows"] for report in reports),
                "invalid_rows": sum(report["invalid_rows"] for report in reports),
                "duplicate_records": sum(report["duplicate_count"] for report in reports),
                "warning_datasets": sum(1 for report in reports if report["warnings"]),
                "error_datasets": sum(1 for report in reports if report["errors"]),
            },
        })

    def _reference_values(self, rel_path: str, column: str) -> set[Any]:
        path = self.raw_dir / rel_path
        if not path.exists():
            return set()
        df = CSVRepository(path).read_csv()
        return set(df[column].dropna().astype(str)) if column in df.columns else set()

    def _validate_dataset(
        self,
        rel_path: str,
        schema: dict[str, Any],
        section_ids: set[Any],
        station_ids: set[Any],
    ) -> dict[str, Any]:
        path = self.raw_dir / rel_path

        # Typed local refs so Pyright can resolve list/dict methods on these fields.
        errors: list[str] = []
        warnings: list[str] = []
        schema_mismatches: list[str] = []
        suspicious_records: list[dict[str, Any]] = []
        missing_required_fields: dict[str, int] = {}
        invalid_timestamps: dict[str, int] = {}
        invalid_numeric_values: dict[str, int] = {}
        invalid_enum_values: dict[str, int] = {}
        nan_count: dict[str, int] = {}
        infinite_values: dict[str, int] = {}

        report: dict[str, Any] = {
            "dataset_name": rel_path,
            "file_path": str(path),
            "row_count": 0,
            "valid_rows": 0,
            "invalid_rows": 0,
            "duplicate_count": 0,
            "retained_records": 0,
            "discarded_duplicates": 0,
            "conflict_count": 0,
            "missing_required_fields": missing_required_fields,
            "invalid_timestamps": invalid_timestamps,
            "invalid_numeric_values": invalid_numeric_values,
            "invalid_enum_values": invalid_enum_values,
            "nan_count": nan_count,
            "infinite_values": infinite_values,
            "spatial_mapping_failures": 0,
            "schema_mismatches": schema_mismatches,
            "suspicious_records": suspicious_records,
            "warnings": warnings,
            "errors": errors,
            "validation_status": "PASS",
            "validation_timestamp": datetime.now(timezone.utc).isoformat(),
            "source_provenance": {"source": "csv", "dataset_name": rel_path},
        }

        if not path.exists():
            errors.append("File is missing.")
            report["validation_status"] = "ERROR"
            return report

        df = CSVRepository(path).read_csv()
        report["row_count"] = len(df)
        report["retained_records"] = len(df)
        invalid_mask = pd.Series(False, index=df.index)

        missing_cols = [column for column in schema["required"] if column not in df.columns]
        if missing_cols:
            schema_mismatches.extend(missing_cols)
            errors.append(f"Missing required columns: {missing_cols}")

        for column in schema["required"]:
            if column in df.columns:
                missing_mask = df[column].isna() | (df[column].astype(str).str.strip() == "")
                count = missing_mask.sum()
                if count:
                    missing_required_fields[column] = count
                    invalid_mask |= missing_mask

        for column in schema.get("numeric", []):
            if column in df.columns:
                parsed: pd.Series = pd.to_numeric(df[column], errors="coerce")  # type: ignore[assignment]
                invalid: pd.Series = parsed.isna() & df[column].notna()  # type: ignore[assignment]
                inf_arr = np.isinf(parsed.to_numpy(dtype=float, na_value=np.nan))
                infinite: pd.Series = pd.Series(inf_arr, index=df.index)  # type: ignore[assignment]
                if invalid.any():
                    invalid_numeric_values[column] = int(invalid.sum())
                    invalid_mask |= invalid
                if infinite.any():
                    infinite_values[column] = int(infinite.sum())
                    invalid_mask |= infinite

        for column in schema.get("timestamps", []):
            if column in df.columns:
                ts_parsed: pd.Series = pd.to_datetime(df[column], errors="coerce", format="mixed")  # type: ignore[assignment]
                ts_invalid: pd.Series = ts_parsed.isna() & df[column].notna() & (df[column].astype(str).str.strip() != "")  # type: ignore[assignment]
                if ts_invalid.any():
                    invalid_timestamps[column] = int(ts_invalid.sum())
                    invalid_mask |= ts_invalid

        for column, allowed in schema.get("enums", {}).items():
            if column in df.columns:
                enum_invalid: pd.Series = df[column].notna() & ~df[column].isin(allowed)  # type: ignore[assignment]
                if enum_invalid.any():
                    invalid_enum_values[column] = int(enum_invalid.sum())
                    invalid_mask |= enum_invalid

        for column in df.columns:
            count = df[column].isna().sum()
            if count:
                nan_count[column] = count

        key = schema.get("key", [])
        if key and all(column in df.columns for column in key):
            duplicate_mask = df.duplicated(key, keep=False)
            report["duplicate_count"] = int(duplicate_mask.sum())
            if report["duplicate_count"]:
                exact_count = int(df.duplicated(keep=False).sum())
                report["discarded_duplicates"] = int(df.duplicated(keep="first").sum())
                conflicts = max(0, report["duplicate_count"] - exact_count)
                report["conflict_count"] = conflicts
                message = f"Duplicate natural key rows detected for {key}."
                if schema.get("deduplication"):
                    warnings.append(message)
                    warnings.append(str(schema["deduplication"]))
                else:
                    errors.append(message)
                    invalid_mask |= duplicate_mask

        if "foreign_keys" in schema:
            for column, target in schema["foreign_keys"].items():
                if column not in df.columns:
                    continue
                allowed = section_ids if target == "network/block_sections.csv" else station_ids
                orphans = set(df[column].dropna().astype(str)) - allowed
                if orphans:
                    errors.append(f"{column} has {len(orphans)} orphan values against {target}.")

        if rel_path == "network/block_sections.csv" and {"start_km", "end_km"}.issubset(df.columns):
            bad: pd.Series = pd.to_numeric(df["start_km"], errors="coerce") >= pd.to_numeric(df["end_km"], errors="coerce")  # type: ignore[assignment]
            if bad.any():
                suspicious_records.append({"rule": "start_km_before_end_km", "count": int(bad.sum())})
                invalid_mask |= bad

        report["invalid_rows"] = int(invalid_mask.sum())
        report["valid_rows"] = max(0, len(df) - report["invalid_rows"])
        if report["errors"]:
            report["validation_status"] = "ERROR"
        elif report["warnings"]:
            report["validation_status"] = "WARNING"
        return report
