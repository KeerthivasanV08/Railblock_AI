"""
Pydantic Models for Weekly, Monthly, and Rolling Block Plans.
"""

from typing import List, Optional
from pydantic import BaseModel


class PlanningRequestModel(BaseModel):
    start_date: Optional[str] = None
    division: Optional[str] = "Prayagraj (ALD)"
    section_id: Optional[str] = None


class BlockPlanRecordModel(BaseModel):
    block_id: str
    plan_date: str
    section_id: str
    start_time: str
    end_time: str
    duration_minutes: int
    task_ids: str
    departments: str
    priority: float
    resources: str
    crew: str
    train_impact: str
    utilization: float
    optimization_score: float
    status: str
    xai_reason: str
