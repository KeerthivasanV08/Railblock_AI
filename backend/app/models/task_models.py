"""
Pydantic Models for Maintenance Tasks and Priority Scoring.
"""

from typing import Optional, List
from pydantic import BaseModel


class MaintenanceTaskModel(BaseModel):
    task_id: str
    department: str
    section_id: str
    location_reference_type: str
    location_reference_id: str
    start_km: Optional[float] = None
    end_km: Optional[float] = None
    defect_type: str
    severity_class: str
    logged_date: str
    target_completion_date: str
    deferred_count: int
    status: str
    overdue_days: Optional[int] = 0
    required_resource_type: Optional[str] = None
    estimated_duration_minutes: Optional[int] = 120
    criticality_score: Optional[float] = None
    priority_rank: Optional[int] = None
    priority_band: Optional[str] = None


class PriorityBreakdownModel(BaseModel):
    task_id: str
    criticality_score: float
    priority_band: str
    priority_rank: int
    components: dict
    priority_reason: str
