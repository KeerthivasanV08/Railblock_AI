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


class BlockModificationRequest(BaseModel):
    new_start_time: str
    new_end_time: str
    reason: str
    actor_name: str = "Section Controller"
    actor_role: str = "SCR"


class BlockRejectionRequest(BaseModel):
    reason: str
    actor_name: str = "Senior Divisional Operations Manager"
    actor_role: str = "SrDOM"


class BlockExecutionOutcomeRequest(BaseModel):
    outcome: str
    actual_start_time: Optional[str] = None
    actual_end_time: Optional[str] = None
    actual_duration_minutes: Optional[int] = None
    notes: Optional[str] = ""
    actor_name: str = "Execution Controller"
    actor_role: str = "Controller"
