"""
Spatial Linear Referencing API Routes.
"""

from fastapi import APIRouter
from app.services.spatial.linear_reference_service import SpatialService

router = APIRouter(tags=["Spatial"])
spatial_service = SpatialService()


@router.post("/ai/spatial-map", summary="Trigger Universal Geo-Spatial Linear Referencing Engine")
@router.post("/spatial/map", summary="Trigger Universal Geo-Spatial Linear Referencing Engine (Spatial)")
def run_spatial_map():
    """Converts TMS chainage, SMMS signals, and TDMS masts into unified GPS Lat/Lon coordinates."""
    mapped_df = spatial_service.run_spatial_mapping()
    return {"status": "SUCCESS", "tasks_mapped": len(mapped_df)}
