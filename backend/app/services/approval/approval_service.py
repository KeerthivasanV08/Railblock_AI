"""
Human-in-the-Loop Block Plan Approval Service for RailBlock AI.
"""

from datetime import datetime, timedelta
from typing import Dict, Any
import pandas as pd
from app.config.settings import settings
from app.core.exceptions import InfeasibleBlockException, InvalidApprovalActionException
from app.core.constants import BLOCK_STATE_TRANSITIONS
from app.repositories.csv_repository import CSVRepository
from app.services.analytics.audit_service import AuditService


class ApprovalService:
    def __init__(self):
        self.weekly_repo = CSVRepository(settings.OUTPUT_DATA_ROOT / "weekly_block_plan.csv")
        self.rolling_repo = CSVRepository(settings.OUTPUT_DATA_ROOT / "rolling_26week_block_plan.csv")
        self.rejected_repo = CSVRepository(settings.OUTPUT_DATA_ROOT / "rejected_block_requests.csv")
        self.version_repo = CSVRepository(settings.OUTPUT_DATA_ROOT / "plan_versions.csv")
        self.execution_repo = CSVRepository(settings.OUTPUT_DATA_ROOT / "execution_outcomes.csv")
        self.audit_service = AuditService()

    def _validate_transition(self, current_status: str, new_status: str, action: str) -> None:
        allowed = BLOCK_STATE_TRANSITIONS.get(current_status, set())
        # Also permit AI RECOMMENDED, PENDING APPROVAL, etc.
        normalized_current = current_status.upper().replace(" ", "_")
        if normalized_current in ("AI_RECOMMENDED", "PENDING_APPROVAL", "PENDING"):
            normalized_current = "PROPOSED"
        if normalized_current in BLOCK_STATE_TRANSITIONS:
            allowed = allowed | BLOCK_STATE_TRANSITIONS[normalized_current]
        if new_status not in allowed and current_status != new_status:
            raise InvalidApprovalActionException(action, f"Cannot transition from '{current_status}' to '{new_status}'.")

    def _ensure_block_row(self, df: pd.DataFrame, block_id: str, request_data: dict) -> tuple[pd.DataFrame, dict]:
        if "block_id" not in df.columns:
            df = pd.DataFrame(columns=[
                "block_id", "plan_run_id", "plan_version", "generated_at", "plan_date",
                "section_id", "start_time", "end_time", "duration_minutes", "task_ids",
                "departments", "priority", "resources", "crew", "train_impact",
                "utilization", "optimization_score", "status", "xai_reason", "source",
                "source_record_id", "dataset_name", "optimizer_status"
            ])
        matches = df[df["block_id"] == block_id]
        if len(matches) > 0:
            return df, matches.iloc[0].to_dict()

        # Check rolling 26-week repo if present
        if self.rolling_repo.file_path.exists():
            rdf = self.rolling_repo.read_csv()
            if "block_id" in rdf.columns:
                rmatches = rdf[rdf["block_id"] == block_id]
                if len(rmatches) > 0:
                    rdict = rmatches.iloc[0].to_dict()
                    # Also append to weekly df for tracking
                    df = pd.concat([df, pd.DataFrame([rdict])], ignore_index=True)
                    return df, rdict

        now_dt = datetime.now()
        start_time = request_data.get("start_time") or request_data.get("new_start_time") or now_dt.strftime("%Y-%m-%d %H:%M:%S")
        duration = int(request_data.get("duration_minutes") or request_data.get("duration_min") or 120)
        end_time = request_data.get("end_time") or request_data.get("new_end_time") or (now_dt + timedelta(minutes=duration)).strftime("%Y-%m-%d %H:%M:%S")

        new_row = {
            "block_id": block_id,
            "plan_run_id": f"RUN-{now_dt.strftime('%Y%m%d%H%M%S')}",
            "plan_version": 1,
            "generated_at": now_dt.isoformat(),
            "plan_date": now_dt.strftime("%Y-%m-%d"),
            "section_id": request_data.get("section_id", "SEC_001"),
            "start_time": start_time,
            "end_time": end_time,
            "duration_minutes": duration,
            "task_ids": request_data.get("task_ids", f"TASK_{block_id}"),
            "departments": request_data.get("departments", "Engineering;TRD;S&T"),
            "priority": float(request_data.get("priority", 85.0)),
            "resources": request_data.get("resources", "Engineering crew"),
            "crew": request_data.get("crew", "CREW_01"),
            "train_impact": request_data.get("train_impact", "LOW"),
            "utilization": float(request_data.get("utilization", 0.85)),
            "optimization_score": float(request_data.get("optimization_score", 90.0)),
            "status": "PROPOSED",
            "xai_reason": f"Block recommendation {block_id} registered for corridor operations.",
            "source": "api",
            "source_record_id": block_id,
            "dataset_name": "weekly_block_plan.csv",
            "optimizer_status": "FEASIBLE",
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        return df, new_row

    def _record_version(self, row: dict, new_status: str, reason: str = "") -> int:
        current_version = int(float(row.get("plan_version", 1) or 1))
        next_version = current_version + 1
        self.version_repo.append_rows([{
            "plan_run_id": row.get("plan_run_id", ""),
            "block_id": row.get("block_id", ""),
            "plan_version": next_version,
            "horizon": row.get("horizon", "WEEKLY"),
            "status": new_status,
            "start_time": row.get("start_time", ""),
            "end_time": row.get("end_time", ""),
            "created_at": datetime.now().isoformat(),
            "source": row.get("source", "csv"),
            "source_record_id": row.get("source_record_id", row.get("task_ids", "")),
            "reason": reason,
        }])
        return next_version

    def approve_block(self, block_id: str, request_data: dict) -> dict:
        df = self.weekly_repo.read_csv()
        df, block_row = self._ensure_block_row(df, block_id, request_data)

        current_status = str(block_row.get("status", "PROPOSED"))
        self._validate_transition(current_status, "APPROVED", "APPROVE")

        actor_name = request_data.get("approved_by") or request_data.get("actor_name") or "Chief Power Controller"
        actor_role = request_data.get("role") or request_data.get("actor_role") or "CPRC"
        notes = request_data.get("notes") or "Approved after traffic gap verification"

        next_version = self._record_version(block_row, "APPROVED", notes)
        df.loc[df["block_id"] == block_id, "status"] = "APPROVED"
        df.loc[df["block_id"] == block_id, "plan_version"] = next_version
        self.weekly_repo.write_csv(df)

        if self.rolling_repo.file_path.exists():
            rdf = self.rolling_repo.read_csv()
            if "block_id" in rdf.columns and (rdf["block_id"] == block_id).any():
                rdf.loc[rdf["block_id"] == block_id, "status"] = "APPROVED"
                rdf.loc[rdf["block_id"] == block_id, "plan_version"] = next_version
                self.rolling_repo.write_csv(rdf)

        self.audit_service.log_event(
            entity="BLOCK_PLAN",
            entity_id=block_id,
            action="APPROVE",
            actor=f"{actor_name} ({actor_role})",
            old_value=current_status,
            new_value="APPROVED",
            reason=notes
        )

        return {"block_id": block_id, "status": "APPROVED", "plan_version": next_version, "notes": notes}

    def modify_block(self, block_id: str, request_data: dict) -> dict:
        df = self.weekly_repo.read_csv()
        df, block_row = self._ensure_block_row(df, block_id, request_data)

        current_status = str(block_row.get("status", "PROPOSED"))
        self._validate_transition(current_status, "MODIFIED", "MODIFY")

        new_start = request_data.get("new_start_time") or request_data.get("start_time")
        new_end = request_data.get("new_end_time") or request_data.get("end_time")

        if not new_start and request_data.get("start_min") is not None:
            start_min = int(request_data["start_min"])
            dur_min = int(request_data.get("duration_min") or request_data.get("duration_minutes") or 120)
            base_date = datetime.now().date()
            start_dt = datetime.combine(base_date, datetime.min.time()) + timedelta(minutes=start_min)
            end_dt = start_dt + timedelta(minutes=dur_min)
            new_start = start_dt.strftime("%Y-%m-%d %H:%M:%S")
            new_end = end_dt.strftime("%Y-%m-%d %H:%M:%S")

        reason = request_data.get("reason", "Shifted window")
        actor_name = request_data.get("modified_by") or request_data.get("actor_name") or "Section Controller"
        actor_role = request_data.get("role") or request_data.get("actor_role") or "SCR"

        if not new_start or not new_end:
            now_dt = datetime.now()
            new_start = now_dt.strftime("%Y-%m-%d %H:%M:%S")
            new_end = (now_dt + timedelta(minutes=120)).strftime("%Y-%m-%d %H:%M:%S")

        old_start = block_row.get("start_time", "")
        next_version = self._record_version(block_row, "MODIFIED", reason)
        df.loc[df["block_id"] == block_id, "start_time"] = new_start
        df.loc[df["block_id"] == block_id, "end_time"] = new_end
        df.loc[df["block_id"] == block_id, "status"] = "MODIFIED"
        df.loc[df["block_id"] == block_id, "plan_version"] = next_version
        self.weekly_repo.write_csv(df)

        self.audit_service.log_event(
            entity="BLOCK_PLAN",
            entity_id=block_id,
            action="MODIFY",
            actor=f"{actor_name} ({actor_role})",
            old_value=str(old_start),
            new_value=f"{new_start} to {new_end}",
            reason=reason
        )

        return {"block_id": block_id, "status": "MODIFIED", "plan_version": next_version, "new_start_time": new_start, "new_end_time": new_end}

    def reject_block(self, block_id: str, request_data: dict) -> dict:
        df = self.weekly_repo.read_csv()
        df, block_row = self._ensure_block_row(df, block_id, request_data)

        current_status = str(block_row.get("status", "PROPOSED"))
        self._validate_transition(current_status, "REJECTED", "REJECT")

        reason = request_data.get("reason") or "Rejected by Controller"
        actor_name = request_data.get("rejected_by") or request_data.get("actor_name") or "Senior Divisional Operations Manager"
        actor_role = request_data.get("role") or request_data.get("actor_role") or "SrDOM"

        next_version = self._record_version(block_row, "REJECTED", reason)
        rejected_row = block_row.copy()
        rejected_row["rejection_reason"] = reason
        rejected_row["status"] = "REJECTED"
        rejected_row["plan_version"] = next_version

        self.rejected_repo.append_rows([rejected_row])

        df.loc[df["block_id"] == block_id, "status"] = "REJECTED"
        df.loc[df["block_id"] == block_id, "rejection_reason"] = reason
        df.loc[df["block_id"] == block_id, "plan_version"] = next_version
        self.weekly_repo.write_csv(df)

        if self.rolling_repo.file_path.exists():
            rdf = self.rolling_repo.read_csv()
            if "block_id" in rdf.columns and (rdf["block_id"] == block_id).any():
                rdf.loc[rdf["block_id"] == block_id, "status"] = "REJECTED"
                rdf.loc[rdf["block_id"] == block_id, "rejection_reason"] = reason
                rdf.loc[rdf["block_id"] == block_id, "plan_version"] = next_version
                self.rolling_repo.write_csv(rdf)

        self.audit_service.log_event(
            entity="BLOCK_PLAN",
            entity_id=block_id,
            action="REJECT",
            actor=f"{actor_name} ({actor_role})",
            old_value=current_status,
            new_value="REJECTED",
            reason=reason
        )

        return {"block_id": block_id, "status": "REJECTED", "plan_version": next_version, "reason": reason}

    def record_execution_outcome(self, block_id: str, request_data: dict) -> dict:
        df = self.weekly_repo.read_csv()
        df, block_row = self._ensure_block_row(df, block_id, request_data)

        current_status = str(block_row.get("status", "PROPOSED"))
        self._validate_transition(current_status, "EXECUTED", "EXECUTE")

        actual_duration = request_data.get("actual_duration_minutes")
        if actual_duration is None and request_data.get("actual_start_time") and request_data.get("actual_end_time"):
            try:
                start_dt = datetime.fromisoformat(request_data["actual_start_time"])
                end_dt = datetime.fromisoformat(request_data["actual_end_time"])
                actual_duration = int((end_dt - start_dt).total_seconds() // 60)
            except Exception:
                actual_duration = 120

        outcome = {
            "block_id": block_id,
            "plan_version": int(float(block_row.get("plan_version", 1) or 1)),
            "planned_duration_minutes": int(float(block_row.get("duration_minutes", 0) or 0)),
            "actual_duration_minutes": actual_duration,
            "outcome": request_data.get("outcome", "COMPLETED"),
            "actual_start_time": request_data.get("actual_start_time", ""),
            "actual_end_time": request_data.get("actual_end_time", ""),
            "notes": request_data.get("notes", ""),
            "recorded_at": datetime.now().isoformat(),
            "actor": f"{request_data.get('actor_name', 'Execution Controller')} ({request_data.get('actor_role', 'Controller')})",
        }
        self.execution_repo.append_rows([outcome])

        df.loc[df["block_id"] == block_id, "status"] = "EXECUTED"
        self.weekly_repo.write_csv(df)
        self.audit_service.log_event(
            entity="BLOCK_EXECUTION",
            entity_id=block_id,
            action="EXECUTE",
            actor=outcome["actor"],
            old_value=current_status,
            new_value="EXECUTED",
            reason=outcome["notes"],
        )
        return outcome
