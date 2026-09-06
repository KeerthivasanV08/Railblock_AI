"""
Seasonal Intelligence & Weather Risk Routes.
"""

from typing import List, Optional
from fastapi import APIRouter, Query

from app.models.seasonal import (
    LiveWeatherReport,
    SectionSeasonalRisk,
    SeasonalContextResponse,
)
from app.services.seasonal_service import seasonal_service

router = APIRouter(prefix="/seasonal", tags=["Seasonal Intelligence"])


@router.get(
    "/context/{section_id}",
    response_model=SeasonalContextResponse,
    summary="Get Section Seasonal Context & Risk",
)
def get_section_seasonal_context(section_id: str):
    """
    Returns climatological seasonal context, live weather telemetry,
    risk score (SRS), and domain recommendations for a given section.
    """
    return seasonal_service.get_section_context(section_id)


@router.get(
    "/sections",
    response_model=List[SectionSeasonalRisk],
    summary="Get Seasonal Risk Scores for All Corridor Sections",
)
def get_all_section_risks(
    asset_type: str = Query("TRACK", description="Asset type: TRACK, OHE, or SIGNAL")
):
    """
    Returns calculated task-aware SRS scores for all 68 corridor sections along Chennai-Thoothukudi.
    """
    return seasonal_service.get_all_corridor_risks(asset_type=asset_type)


@router.get(
    "/live/{section_id}",
    response_model=LiveWeatherReport,
    summary="Get Section Live Weather Telemetry",
)
def get_live_weather(section_id: str):
    """
    Returns current live weather telemetry. If unavailable, returns UNKNOWN / UNAVAILABLE / None.
    """
    return seasonal_service.get_live_weather_report(section_id)
