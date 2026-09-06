from fastapi import APIRouter
from app.services.spatial.linear_reference_service import SpatialService
from app.services.spatial.corridor_service import CorridorService

router = APIRouter(tags=["Spatial"])
spatial_service = SpatialService()
corridor_service = CorridorService()


@router.post("/ai/spatial-map", summary="Trigger Universal Geo-Spatial Linear Referencing Engine")
@router.post("/spatial/map", summary="Trigger Universal Geo-Spatial Linear Referencing Engine (Spatial)")
def run_spatial_map():
    """Converts TMS chainage, SMMS signals, and TDMS masts into unified GPS Lat/Lon coordinates."""
    mapped_df = spatial_service.run_spatial_mapping()
    return {"status": "SUCCESS", "tasks_mapped": len(mapped_df)}


@router.get("/spatial/corridor", summary="Get Corridor Overview & Geographic Bounds")
def get_corridor_info():
    """Returns corridor metadata, endpoints, station/section counts, and bounding box."""
    return corridor_service.get_corridor_info()


@router.get("/spatial/stations", summary="Get All Corridor Stations")
def get_stations():
    """Returns all 69 stations along the Chennai Egmore -> Tuticorin corridor."""
    return {"stations": corridor_service.get_corridor_stations()}


@router.get("/spatial/sections", summary="Get All Block Sections")
def get_sections():
    """Returns all 68 block sections with operational parameters."""
    return {"sections": corridor_service.get_corridor_sections()}


@router.get("/spatial/geometry", summary="Get Track Geometry Segments")
def get_geometry():
    """Returns piecewise curved track geometry segments with GPS coordinates."""
    return {"geometry": corridor_service.get_corridor_geometry()}


@router.get("/spatial/tracks-geojson", summary="Get Track GeoJSON Polyline Features")
def get_tracks_geojson():
    """Returns the full GeoJSON FeatureCollection of the corridor tracks."""
    return corridor_service.get_tracks_geojson()

