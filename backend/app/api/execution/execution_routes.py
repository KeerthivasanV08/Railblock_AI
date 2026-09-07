"""
Execution API Router for tracking active maintenance possession blocks
and closed-loop execution feedback.
"""

from fastapi import APIRouter, Path
from app.services.execution.execution_monitor import ExecutionMonitor
from app.services.execution.feedback_engine import ExecutionFeedbackEngine

router = APIRouter(prefix="/execution", tags=["Execution"])
monitor = ExecutionMonitor()
feedback_engine = ExecutionFeedbackEngine()


@router.get("/active", summary="Active block executions")
def get_active_executions():
    return {"active_executions": monitor.get_active_executions()}


@router.get("/metrics", summary="Closed-Loop Execution Feedback Metrics")
def get_closed_loop_metrics():
    """Returns real closed-loop execution feedback: duration variance, overrun rate, wastage, and buffer calibration."""
    metrics = feedback_engine.analyze_execution_feedback()
    return {
        "status": "SUCCESS",
        "metrics": metrics.to_dict(),
    }


@router.get("/section-modifier/{section_id}", summary="Learned Section Buffer Modifier")
def get_section_buffer_modifier(section_id: str = Path(..., description="Corridor section ID")):
    """Returns learned possession duration buffer (in minutes) for a given corridor section."""
    extra_min = feedback_engine.get_section_duration_modifier(section_id)
    return {
        "section_id": section_id,
        "recommended_buffer_minutes": extra_min,
    }
