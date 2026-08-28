"""
Execution API Router for tracking active maintenance possession blocks.
"""

from fastapi import APIRouter
from app.services.execution.execution_monitor import ExecutionMonitor

router = APIRouter(prefix="/execution", tags=["Execution"])
monitor = ExecutionMonitor()


@router.get("/active", summary="Active block executions")
def get_active_executions():
    return {"active_executions": monitor.get_active_executions()}
