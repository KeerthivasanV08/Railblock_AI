"""
Disruptions & Rescheduling API Router.

Route: /api/disruptions/*  and  /api/ai/reschedule

Rescheduler pipeline enforces:
  1. Generate typed candidates (delay / shift / reallocate)
  2. Validate each against ConstraintEngine
  3. Reject infeasible candidates
  4. Score + rank feasible candidates
  5. Require human approval before plan update
"""

import time
import uuid
from typing import Optional, Any

from fastapi import APIRouter, Query, Body
from app.services.rescheduler.disruption_detector import DisruptionService
from app.services.rescheduler.rescheduler_service import ReschedulingService
from app.repositories.disruption_repository import DisruptionRepository

router = APIRouter(tags=["Disruptions & Rescheduling"])
disruption_service = DisruptionService()
resched_service = ReschedulingService()
disruption_repo = DisruptionRepository()


@router.get("/disruptions", summary="Get Logged Disruption Events")
def get_disruptions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    event_type: Optional[str] = None,
):
    """Returns logged disruption events with pagination."""
    filters = {"event_type": event_type} if event_type else {}
    return disruption_repo.disruptions_repo.filter_rows(filters, page=page, page_size=page_size)


@router.post("/disruptions/detect", summary="Detect Live Operational Disruptions")
def detect_disruptions():
    """Analyzes live train delays, emergency defects, and machine breakdowns affecting blocks."""
    detected = disruption_service.detect_disruptions()
    return {
        "status": "SUCCESS",
        "disruptions_detected_count": len(detected),
        "disruptions": detected[:50],
    }


@router.post("/ai/reschedule", summary="Generate Constraint-Validated Rescheduling Options")
@router.post("/disruptions/reschedule", summary="Generate Rescheduling Options (Disruptions)")
def reschedule_block(
    event_id: str = Query(..., description="Disruption event ID"),
    affected_block_id: str = Query(..., description="Block ID that cannot proceed"),
    block_metadata: Optional[dict[str, Any]] = Body(
        default=None,
        description="Optional block operational context (criticality_score, duration_minutes, etc.)",
    ),
):
    """
    Generates constraint-validated rescheduling alternatives for a disrupted block.

    Every candidate is validated against the ConstraintEngine before being returned.
    Infeasible candidates are included in the response with feasible=False and
    explicit rejection_reason and failed_constraints fields.

    Only feasible candidates should be presented to the human controller for approval.
    No plan modification occurs without explicit human approval via /disruptions/approve.
    """
    t0 = time.perf_counter()
    request_id = uuid.uuid4().hex[:12]

    result = resched_service.generate_reschedule_options(
        event_id=event_id,
        affected_block_id=affected_block_id,
        affected_block_metadata=block_metadata,
    )

    timing_ms = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "status": "SUCCESS",
        "request_id": request_id,
        "engine_version": result["engine_version"],
        "scoring_mode": result["scoring_mode"],
        "timing_ms": timing_ms,
        "event_id": event_id,
        "affected_block_id": affected_block_id,
        "impact_assessment": result.get("impact_assessment"),
        "rl_metadata": result.get("rl_metadata"),
        "constraint_validation_summary": result["constraint_validation_summary"],
        "approval_required": result["approval_required"],
        "approval_note": result["approval_note"],
        "options": result["options"],
    }


@router.post("/disruptions/approve", summary="Human Approval of Rescheduling Option")
def approve_reschedule(
    option_id: str = Query(..., description="Option ID to approve"),
    actor: str = Query("Controller", description="Actor approving the rescheduling"),
    confirmed_feasible: bool = Query(
        ...,
        description="Confirm the selected option passed constraint validation (feasible=True)",
    ),
):
    """
    Records human approval of a rescheduling candidate and commits the plan update.

    Enforces:
      - confirmed_feasible must be True — prevents approval of infeasible candidates.
      - Actively transitions the operational block status to RESCHEDULED in the plan.
    """
    result = resched_service.accept_reschedule_option(
        option_id=option_id,
        actor=actor,
        confirmed_feasible=confirmed_feasible,
    )
    plan_updated = result.get("plan_updated", False)
    return {
        "status": "APPROVED" if result.get("status") == "ACCEPTED" else "REJECTED",
        "reschedule_record": result,
        "plan_update_note": (
            "Approval committed to operational plan (weekly_block_plan.csv) and versioned."
            if plan_updated
            else "Approval recorded in audit log."
        ),
    }
