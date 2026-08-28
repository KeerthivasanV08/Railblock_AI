"""
Pydantic Models for Disruption Events and Rescheduling.
"""

from typing import List, Optional
from pydantic import BaseModel


class DisruptionEventModel(BaseModel):
    event_id: str
    event_type: str
    section_id: str
    detected_at: str
    affected_block_id: Optional[str] = ""
    impact_description: str
    severity: str


class RescheduleOptionModel(BaseModel):
    option_id: str
    new_start_time: str
    new_end_time: str
    train_impact: str
    priority_preservation: float
    resource_feasibility: bool
    crew_feasibility: bool
    optimization_score: float
    reason: str


class RescheduleRequestModel(BaseModel):
    event_id: str
    affected_block_id: str
