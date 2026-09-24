"""
Execution API Router for RailBlock AI closed-loop execution tracking,
field outcome recording, KPIs, and analytics.
"""

from typing import Optional, List
from fastapi import APIRouter, Path, HTTPException, Query, Body

from app.services.execution.execution_service import ExecutionService
from app.services.execution.feedback_engine import ExecutionFeedbackEngine
from app.models.execution_models import (
    ExecutionRecordCreateRequest,
    ExecutionRecordUpdateRequest,
    ExecutionKPIs,
    ExecutionAnalyticsResponse,
)
from app.utils.csv_utils import sanitize_for_json

router = APIRouter(prefix="/execution", tags=["Execution"])
execution_service = ExecutionService()
feedback_engine = ExecutionFeedbackEngine()


@router.get("", summary="Get all execution records")
def get_execution_records(status: Optional[str] = Query(None, description="Filter by status (SCHEDULED, ACTIVE, COMPLETED, PARTIAL, ABANDONED)")):
    """Returns list of execution records from the CSV dataset."""
    records = execution_service.get_all_records(status=status)
    return sanitize_for_json({"status": "SUCCESS", "records": records, "count": len(records)})


@router.get("/active", summary="Active block executions")
def get_active_executions():
    """Returns currently active field possession blocks."""
    active_records = execution_service.get_active_executions()
    return sanitize_for_json({"active_executions": active_records})


@router.get("/kpis", summary="Field Execution KPI Metrics")
def get_execution_kpis():
    """
    Returns exact closed-loop execution KPIs:
    total_executions, avg_variance, overrun_rate, block_wastage
    """
    kpis = execution_service.compute_kpis()
    return sanitize_for_json(kpis)


@router.get("/metrics", summary="Closed-Loop Feedback Metrics (Legacy/Detailed)")
def get_closed_loop_metrics():
    """Returns detailed closed-loop feedback metrics including buffer calibration."""
    metrics = feedback_engine.analyze_execution_feedback()
    return sanitize_for_json({
        "status": "SUCCESS",
        "metrics": metrics.to_dict(),
    })


@router.get("/analytics", summary="Execution Analytics Chart Data")
def get_execution_analytics():
    """
    Returns aggregated chart data for:
    1. Planned vs Actual Duration
    2. Execution Status Distribution
    3. Variance Trend
    4. Top Deviation Reasons
    """
    return sanitize_for_json(execution_service.get_analytics())


@router.get("/section-modifier/{section_id}", summary="Learned Section Buffer Modifier")
def get_section_buffer_modifier(section_id: str = Path(..., description="Corridor section ID")):
    """Returns learned possession duration buffer (in minutes) for a given corridor section."""
    extra_min = feedback_engine.get_section_duration_modifier(section_id)
    return sanitize_for_json({
        "section_id": section_id,
        "recommended_buffer_minutes": extra_min,
    })


@router.get("/{id}", summary="Get single execution record by ID")
def get_execution_by_id(id: str = Path(..., description="Execution ID or Block ID")):
    """Returns a specific execution record by execution_id or block_id."""
    record = execution_service.get_record_by_id(id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Execution record '{id}' not found.")
    return sanitize_for_json(record)


@router.post("", summary="Record outcome or create execution record")
def create_execution_record(request: ExecutionRecordCreateRequest):
    """Creates a new field outcome record or logs field execution progress."""
    data = request.model_dump()
    record = execution_service.create_or_update_record(data)
    return sanitize_for_json({"status": "SUCCESS", "message": "Execution outcome recorded successfully.", "record": record})


@router.put("/{id}", summary="Update execution outcome record")
def update_execution_record(id: str = Path(..., description="Execution ID or Block ID"), request: ExecutionRecordUpdateRequest = Body(...)):
    """Updates an existing execution record with actual times, status, tasks, deviation reason, etc."""
    existing = execution_service.get_record_by_id(id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Execution record '{id}' not found.")
        
    data = existing.copy()
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    data.update(updates)
    
    updated_record = execution_service.create_or_update_record(data)
    return sanitize_for_json({"status": "SUCCESS", "message": f"Execution record '{id}' updated.", "record": updated_record})
