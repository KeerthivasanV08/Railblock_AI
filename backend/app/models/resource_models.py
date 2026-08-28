"""
Pydantic Models for Heavy Machinery and Crew Inventories.
"""

from typing import Optional
from pydantic import BaseModel


class MachineInventoryModel(BaseModel):
    resource_id: str
    resource_type: str
    home_depot: str
    current_latitude: float
    current_longitude: float
    is_available: bool
    last_updated: str


class CrewInventoryModel(BaseModel):
    crew_id: str
    department: str
    home_depot: str
    shift_start: str
    shift_end: str
    headcount: int
    is_available: bool
