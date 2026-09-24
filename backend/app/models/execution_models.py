"""
Pydantic Models for Field Execution, Outcome Recording, KPIs, and Analytics.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ExecutionRecord(BaseModel):
    execution_id: str = Field(..., description="Unique execution outcome record ID")
    block_id: str = Field(..., description="Associated block plan ID")
    section_id: str = Field(..., description="Railway corridor section ID")
    department: str = Field(..., description="Department(s) involved (e.g. Engineering+TRD)")
    planned_start: str = Field(..., description="Scheduled/Planned start time (ISO or formatted)")
    planned_end: str = Field(..., description="Scheduled/Planned end time (ISO or formatted)")
    actual_start: Optional[str] = Field(None, description="Actual field possession start time")
    actual_end: Optional[str] = Field(None, description="Actual field possession end time")
    planned_duration: int = Field(..., description="Planned duration in minutes")
    actual_duration: Optional[int] = Field(None, description="Actual duration in minutes")
    variance_minutes: Optional[int] = Field(None, description="Variance in minutes (actual - planned)")
    completed_tasks: int = Field(0, description="Count of tasks completed")
    total_tasks: int = Field(1, description="Total planned tasks")
    completion_percentage: float = Field(0.0, description="Task completion percentage")
    machine_id: Optional[str] = Field("", description="Primary heavy machinery ID (e.g. BCM-02)")
    crew_id: Optional[str] = Field("", description="Assigned gang/crew ID (e.g. Crew-17)")
    status: str = Field("COMPLETED", description="SCHEDULED, ACTIVE, COMPLETED, PARTIAL, ABANDONED")
    deviation_reason: Optional[str] = Field(None, description="Reason for variance or disruption")
    notes: Optional[str] = Field("", description="Field operator notes")
    created_at: str = Field(..., description="Record creation timestamp")
    recorded_by: str = Field("controller", description="Actor recording outcome")


class ExecutionRecordCreateRequest(BaseModel):
    block_id: str
    section_id: Optional[str] = "SEC_001"
    department: Optional[str] = "Engineering"
    planned_start: Optional[str] = None
    planned_end: Optional[str] = None
    actual_start: Optional[str] = None
    actual_end: Optional[str] = None
    planned_duration: Optional[int] = 120
    actual_duration: Optional[int] = None
    completed_tasks: Optional[int] = 0
    total_tasks: Optional[int] = 1
    machine_id: Optional[str] = ""
    crew_id: Optional[str] = ""
    status: Optional[str] = "COMPLETED"
    deviation_reason: Optional[str] = None
    notes: Optional[str] = ""
    recorded_by: Optional[str] = "controller"


class ExecutionRecordUpdateRequest(BaseModel):
    status: Optional[str] = None
    actual_start: Optional[str] = None
    actual_end: Optional[str] = None
    planned_duration: Optional[int] = None
    actual_duration: Optional[int] = None
    completed_tasks: Optional[int] = None
    total_tasks: Optional[int] = None
    machine_id: Optional[str] = None
    crew_id: Optional[str] = None
    deviation_reason: Optional[str] = None
    notes: Optional[str] = None
    recorded_by: Optional[str] = None


class ExecutionKPIs(BaseModel):
    total_executions: int
    avg_variance: float
    overrun_rate: float
    block_wastage: Optional[float] = None
    block_wastage_formatted: Optional[str] = "N/A"
    note: Optional[str] = ""


class DurationSeriesPoint(BaseModel):
    block_id: str
    section_id: str
    planned_duration: int
    actual_duration: int
    variance: int


class StatusDistribution(BaseModel):
    status: str
    count: int
    percentage: float


class VarianceTrendPoint(BaseModel):
    date: str
    avg_variance: float
    overrun_count: int


class DeviationReasonCount(BaseModel):
    reason: str
    count: int
    percentage: float


class ExecutionAnalyticsResponse(BaseModel):
    planned_vs_actual: List[DurationSeriesPoint]
    status_distribution: List[StatusDistribution]
    variance_trend: List[VarianceTrendPoint]
    top_deviation_reasons: List[DeviationReasonCount]
