"""
Pydantic Models for Candidate Blocks, Optimization, and Human Approvals.
"""

from typing import List, Optional
from pydantic import BaseModel


class BlockCandidateModel(BaseModel):
    block_id: str
    section_id: str
    window_start: str
    window_end: str
    duration_minutes: int
    task_ids: List[str]
    departments: List[str]
    priority_score: float
    resource_ids: List[str]
    crew_ids: List[str]
    traffic_density: float
    train_impact: str
    feasibility_status: str
    constraint_summary: dict


class BlockApprovalRequest(BaseModel):
    actor_name: str = "Chief Power Controller"
    actor_role: str = "CPRC"
    notes: Optional[str] = "Approved after traffic gap verification"
    approved_by: Optional[str] = None
    role: Optional[str] = None


class BlockModificationRequest(BaseModel):
    new_start_time: Optional[str] = None
    new_end_time: Optional[str] = None
    reason: str = "Shifted window"
    actor_name: str = "Section Controller"
    actor_role: str = "SCR"
    modified_by: Optional[str] = None
    role: Optional[str] = None
    start_min: Optional[int] = None
    duration_min: Optional[int] = None
    duration_minutes: Optional[int] = None


class BlockRejectionRequest(BaseModel):
    reason: str = "Rejected by Controller"
    actor_name: str = "Senior Divisional Operations Manager"
    actor_role: str = "SrDOM"
    rejected_by: Optional[str] = None
    role: Optional[str] = None


class BlockExecutionOutcomeRequest(BaseModel):
    outcome: str
    actual_start_time: Optional[str] = None
    actual_end_time: Optional[str] = None
    actual_duration_minutes: Optional[int] = None
    notes: Optional[str] = ""
    actor_name: str = "Execution Controller"
    actor_role: str = "Controller"


class ManualBlockCreateRequest(BaseModel):
    week_number: int
    department: str
    block_type: str = "CORRIDOR_BLOCK"
    title: Optional[str] = None
    section_id: str
    corridor: Optional[str] = None
    from_km: Optional[float] = None
    to_km: Optional[float] = None
    start_date: str
    end_date: Optional[str] = None
    start_time: str
    end_time: str
    duration_minutes: Optional[int] = None
    priority: Optional[float] = None
    task_ids: Optional[str] = None
    resources: Optional[List[str]] = None
    remarks: Optional[str] = None
    required_resources: Optional[str] = None
    crew: Optional[str] = None
    operational_reason: Optional[str] = None
    description: Optional[str] = None
    controller_remarks: Optional[str] = None


class ManualBlockCreateResponse(BaseModel):
    success: bool = True
    status: str
    message: str
    block_id: Optional[str] = None
    block: Optional[dict] = None
    evaluation: Optional[dict] = None
    errors: Optional[List[str]] = None

