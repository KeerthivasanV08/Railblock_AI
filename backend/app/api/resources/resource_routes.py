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
    """Returns heavy machine inventory."""
    filters = {"resource_type": resource_type} if resource_type else {}
    return resource_repo.machines_repo.filter_rows(filters, page=page, page_size=page_size)


@router.get("/resources/live", summary="Get Live Resource Availability & Locations")
def get_live_resources():
    """Returns live availability status and locations for machinery and maintenance crews."""
    return resource_service.get_live_resources()


@router.get("/resources/crew", summary="Get Maintenance Crew Inventory")
def get_crew(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=500), department: Optional[str] = None):
    """Returns maintenance crew inventory by department."""
    filters = {"department": department} if department else {}
    return resource_repo.crews_repo.filter_rows(filters, page=page, page_size=page_size)
