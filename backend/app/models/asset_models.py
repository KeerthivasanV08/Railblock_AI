"""
Pydantic Models for Railway Infrastructure Assets.
"""

from typing import Optional
from pydantic import BaseModel


class StationModel(BaseModel):
    station_code: str
    station_name: str
    chainage_km: float
    division: str
    latitude: float
    longitude: float


class BlockSectionModel(BaseModel):
    section_id: str
    from_station: str
    to_station: str
    start_km: float
    end_km: float
    line_type: str
    num_lines: int
    max_speed_kmph: int


class TrackGeometryModel(BaseModel):
    segment_id: str
    section_id: str
    start_km: float
    end_km: float
    latitude_start: float
    longitude_start: float
    latitude_end: float
    longitude_end: float


class OHEMastModel(BaseModel):
    mast_number: str
    section_id: str
    equivalent_km: float


class SignalModel(BaseModel):
    signal_id: str
    signal_type: str
    section_id: str
    equivalent_km: float
