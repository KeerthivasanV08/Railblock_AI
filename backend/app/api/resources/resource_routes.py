"""
Resources API Router for Heavy Machinery & Crew Inventories.
"""

from typing import Optional
from fastapi import APIRouter, Query
from app.services.resources.resource_service import ResourceService
from app.repositories.resource_repository import ResourceRepository

router = APIRouter(tags=["Resources"])
resource_service = ResourceService()
resource_repo = ResourceRepository()


@router.get("/resources", summary="Get Machine Inventory")
def get_resources(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=500), resource_type: Optional[str] = None):
    """Returns normalized heavy machine inventory with location, assignments, and utilization."""
    return resource_service.get_machines_paginated(page=page, page_size=page_size, resource_type=resource_type)


@router.get("/resources/live", summary="Get Live Resource Availability & Locations")
def get_live_resources():
    """Returns live availability status and locations for machinery and maintenance crews."""
    return resource_service.get_live_resources()


@router.get("/resources/crew", summary="Get Maintenance Crew Inventory")
def get_crew(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=500), department: Optional[str] = None):
    """Returns maintenance crew inventory by department with shift, availability, and assignments."""
    return resource_service.get_crews_paginated(page=page, page_size=page_size, department=department)


@router.get("/resources/calendar", summary="Get Resource Calendar Timeline Allocations")
def get_resource_calendar(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=500)):
    """Returns unified resource schedule allocations for machinery and crews across maintenance blocks."""
    return resource_service.get_resource_calendar(page=page, page_size=page_size)

