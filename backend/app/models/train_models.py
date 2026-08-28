"""
Pydantic Models for Train Timetable, Delays, and Goods Forecast.
"""

from typing import Optional
from pydantic import BaseModel


class TrainTimetableModel(BaseModel):
    train_number: str
    train_type: str
    section_id: str
    scheduled_departure: str
    scheduled_arrival: str
    priority_class: str
    day_of_week: str


class LiveTrainDelayModel(BaseModel):
    train_number: str
    date: str
    scheduled_time: str
    actual_time: str
    delay_minutes: float
    delay_reason: str
    status: Optional[str] = "ON_TIME"
    location: Optional[str] = None


class GoodsForecastModel(BaseModel):
    section_id: str
    forecast_date: str
    expected_rakes: int
    commodity_type: str
    seasonal_factor: float
