"""
Human-in-the-Loop Block Plan Approval Service for RailBlock AI.
"""

from datetime import datetime
from typing import Dict, Any
from app.config.settings import settings
from app.core.exceptions import InfeasibleBlockException, InvalidApprovalActionException
from app.core.constants import BLOCK_STATE_TRANSITIONS
from app.repositories.csv_repository import CSVRepository
from app.services.analytics.audit_service import AuditService


class ApprovalService:
    def __init__(self):
        self.weekly_repo = CSVRepository(settings.OUTPUT_DATA_ROOT / "weekly_block_plan.csv")
        self.rejected_repo = CSVRepository(settings.OUTPUT_DATA_ROOT / "rejected_block_requests.csv")
        self.version_repo = CSVRepository(settings.OUTPUT_DATA_ROOT / "plan_versions.csv")
        self.execution_repo = CSVRepository(settings.OUTPUT_DATA_ROOT / "execution_outcomes.csv")
        self.audit_service = AuditService()

    def _validate_transition(self, current_status: str, new_status: str, action: str) -> None:
        allowed = BLOCK_STATE_TRANSITIONS.get(current_status, set())
        if new_status not in allowed:
            raise InvalidApprovalActionException(action, f"Cannot transition from '{current_status}' to '{new_status}'.")

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
        matches = df[df["block_id"] == block_id]
        if len(matches) == 0:
            raise InfeasibleBlockException(block_id, "Block ID not found in current plan.")

        current_status = str(matches.iloc[0].get("status", "PROPOSED"))
        self._validate_transition(current_status, "APPROVED", "APPROVE")

        actor_name = request_data.get("actor_name", "Chief Power Controller")
        actor_role = request_data.get("actor_role", "CPRC")
        notes = request_data.get("notes", "Approved")

        next_version = self._record_version(matches.iloc[0].to_dict(), "APPROVED", notes)
        df.loc[df["block_id"] == block_id, "status"] = "APPROVED"
        df.loc[df["block_id"] == block_id, "plan_version"] = next_version
        self.weekly_repo.write_csv(df)

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
        matches = df[df["block_id"] == block_id]
        if len(matches) == 0:
            raise InfeasibleBlockException(block_id, "Block ID not found.")

        current_status = str(matches.iloc[0].get("status", "PROPOSED"))
        self._validate_transition(current_status, "MODIFIED", "MODIFY")

        new_start = request_data.get("new_start_time")
        new_end = request_data.get("new_end_time")
        reason = request_data.get("reason", "Shifted window")
        actor_name = request_data.get("actor_name", "Section Controller")
        actor_role = request_data.get("actor_role", "SCR")

        if not new_start or not new_end:
            raise InvalidApprovalActionException("MODIFY", "Missing new start or end time.")

        try:
            start_dt = datetime.fromisoformat(new_start)
            end_dt = datetime.fromisoformat(new_end)
        except ValueError as exc:
            raise InvalidApprovalActionException("MODIFY", "Start and end times must be ISO-8601 values.") from exc
        if end_dt <= start_dt:
            raise InvalidApprovalActionException("MODIFY", "End time must be after start time.")
        requested_minutes = int((end_dt - start_dt).total_seconds() // 60)
        required_minutes = int(float(matches.iloc[0].get("duration_minutes", 0) or 0))
        if required_minutes and requested_minutes < required_minutes:
            raise InfeasibleBlockException(block_id, "Modified window is shorter than the planned block duration.")

        old_start = matches.iloc[0]["start_time"]
        next_version = self._record_version(matches.iloc[0].to_dict(), "MODIFIED", reason)
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
        matches = df[df["block_id"] == block_id]
        if len(matches) == 0:
            raise InfeasibleBlockException(block_id, "Block ID not found.")

        current_status = str(matches.iloc[0].get("status", "PROPOSED"))
        self._validate_transition(current_status, "REJECTED", "REJECT")

        reason = request_data.get("reason")
        if not reason:
            raise InvalidApprovalActionException("REJECT", "Rejection reason is required.")

        actor_name = request_data.get("actor_name", "SrDOM")
        actor_role = request_data.get("actor_role", "SrDOM")

        next_version = self._record_version(matches.iloc[0].to_dict(), "REJECTED", reason)
        rejected_row = matches.iloc[0].to_dict()
        rejected_row["rejection_reason"] = reason
        rejected_row["status"] = "REJECTED"
        rejected_row["plan_version"] = next_version

        self.rejected_repo.append_rows([rejected_row])

        df.loc[df["block_id"] == block_id, "status"] = "REJECTED"
        df.loc[df["block_id"] == block_id, "rejection_reason"] = reason
        df.loc[df["block_id"] == block_id, "plan_version"] = next_version
        self.weekly_repo.write_csv(df)

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
        matches = df[df["block_id"] == block_id]
        if len(matches) == 0:
            raise InfeasibleBlockException(block_id, "Block ID not found.")

        current_status = str(matches.iloc[0].get("status", "PROPOSED"))
        self._validate_transition(current_status, "EXECUTED", "EXECUTE")

        actual_duration = request_data.get("actual_duration_minutes")
        if actual_duration is None and request_data.get("actual_start_time") and request_data.get("actual_end_time"):
            start_dt = datetime.fromisoformat(request_data["actual_start_time"])
            end_dt = datetime.fromisoformat(request_data["actual_end_time"])
            actual_duration = int((end_dt - start_dt).total_seconds() // 60)

        outcome = {
            "block_id": block_id,
            "plan_version": int(float(matches.iloc[0].get("plan_version", 1) or 1)),
            "planned_duration_minutes": int(float(matches.iloc[0].get("duration_minutes", 0) or 0)),
            "actual_duration_minutes": actual_duration,
            "outcome": request_data.get("outcome"),
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
