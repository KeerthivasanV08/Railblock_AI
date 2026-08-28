"""
Disruption Rescheduling Service for RailBlock AI.

Orchestrates the full rescheduler pipeline:
  1. Accept disruption event + affected block metadata
  2. Delegate to ReschedulerEngine (generates + validates candidates)
  3. Return ranked candidates â€” feasible ones are safe to present to human
  4. Enforce human approval before any plan modification

Human approval is mandatory. This service never modifies plans directly.
"""

import logging
import pandas as pd
from typing import Any

from app.config.settings import settings
from app.services.rescheduler.policy_engine import ReschedulerEngine
from app.repositories.csv_repository import CSVRepository
from app.repositories.disruption_repository import DisruptionRepository
from app.services.analytics.audit_service import AuditService

logger = logging.getLogger(__name__)


class ReschedulingService:
    def __init__(self):
        self.engine = ReschedulerEngine()
        self.log_repo = CSVRepository(settings.OUTPUT_DATA_ROOT / "disruption_reschedule_log.csv")
        self.audit_service = AuditService()
        self.disruption_repo = DisruptionRepository()

    def generate_reschedule_options(
        self,
        event_id: str,
        affected_block_id: str,
        affected_block_metadata: dict | None = None,
    ) -> dict[str, Any]:
        """
        Generate, validate, and rank rescheduling candidates for a disrupted block.

        Args:
            event_id: Disruption event identifier
            affected_block_id: ID of the block that cannot proceed as planned
            affected_block_metadata: Optional dict with block operational context
                (criticality_score, duration_minutes, traffic_density, section_id,
                 spatial_mapping_status, mapped_chainage_km, etc.)

        Returns:
            dict with:
                event_id, affected_block_id,
                engine_version, scoring_mode,
                total_candidates (int),
                feasible_count (int),
                infeasible_count (int),
                options (list) â€” ranked feasible-first,
                constraint_validation_summary (dict),
                approval_required (bool â€” always True)
        """
        # Resolve disruption event context
        disruption_event = {"event_id": event_id, "section_id": "SEC_001"}
        try:
            disruptions_df = self.disruption_repo.get_disruptions()
            if len(disruptions_df) > 0:
                matching = disruptions_df[disruptions_df.get("event_id", pd.Series()) == event_id]
                if len(matching) > 0:
                    row = matching.iloc[0]
                    disruption_event["section_id"] = row.get("section_id", "SEC_001")
                    disruption_event["event_type"] = row.get("event_type", "Disruption")
                    disruption_event["severity"] = row.get("severity", "Medium")
        except Exception as exc:
            logger.debug("Could not resolve disruption event from repo: %s", exc)

        # Build affected block context
        affected_block: dict[str, Any] = {
            "block_id": affected_block_id,
            "section_id": disruption_event.get("section_id", "SEC_001"),
        }
        if affected_block_metadata:
            affected_block.update(affected_block_metadata)

        # Run the engine pipeline (generate â†’ validate â†’ score â†’ rank)
        options = self.engine.generate_reschedule_options(disruption_event, affected_block)

        feasible = [o for o in options if o.get("feasible")]
        infeasible = [o for o in options if not o.get("feasible")]

        constraint_summary = {
            "total_candidates": len(options),
            "feasible_count": len(feasible),
            "infeasible_count": len(infeasible),
            "rejected_candidates": [
                {
                    "option_id": o["option_id"],
                    "action_type": o["action_type"],
                    "rejection_reason": o["rejection_reason"],
                    "failed_constraints": o["failed_constraints"],
                }
                for o in infeasible
            ],
        }

        self.audit_service.log_event(
            entity="DISRUPTION_RESCHEDULE",
            entity_id=affected_block_id,
            action="GENERATE_OPTIONS",
            actor="system",
            new_value=f"feasible={len(feasible)}, infeasible={len(infeasible)}",
        )

        return {
            "event_id": event_id,
            "affected_block_id": affected_block_id,
            "engine_version": self.engine.ENGINE_VERSION,
            "scoring_mode": self.engine.SCORING_MODE,
            "options": options,
            "constraint_validation_summary": constraint_summary,
            "approval_required": True,
            "approval_note": (
                "All candidates have been constraint-validated. "
                "A human controller must approve before any plan modification."
            ),
        }

    def accept_reschedule_option(
        self,
        option_id: str,
        actor: str = "Controller",
        confirmed_feasible: bool = False,
    ) -> dict:
        """
        Record human approval of a rescheduling candidate and log the plan update.

        IMPORTANT: This method does NOT directly modify the operational plan.
        It records the approval decision in the audit log and reschedule log.
        The operational plan update must be performed separately by the planning service.

        Args:
            option_id: The option_id from the candidate
            actor: Controller/user who approved
            confirmed_feasible: Caller must confirm the selected option passed constraint validation

        Returns:
            dict with reschedule_id, status, audit trail reference
        """
        if not confirmed_feasible:
            return {
                "reschedule_id": option_id,
                "status": "REJECTED_PENDING_VALIDATION",
                "error": (
                    "Cannot accept a rescheduling option without confirmed constraint validation. "
                    "Ensure feasible=True before calling accept_reschedule_option."
                ),
            }

        log_entry = {
            "reschedule_id": option_id,
            "disruption_event_id": option_id.split("-")[0] if "-" in option_id else option_id,
            "original_block_id": option_id.split("-")[0] if "-" in option_id else option_id,
            "new_block_id": option_id,
            "status": "ACCEPTED",
            "accepted_by": actor,
        }
        try:
            self.log_repo.append_rows([log_entry])
        except Exception as exc:
            logger.warning("Could not append reschedule log: %s", exc)

        self.audit_service.log_event(
            entity="DISRUPTION_RESCHEDULE",
            entity_id=option_id,
            action="ACCEPT_RESCHEDULE",
            actor=actor,
            new_value="ACCEPTED",
        )
        return log_entry


# Backward compatibility alias
ReschedulerService = ReschedulingService
