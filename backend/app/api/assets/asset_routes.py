"""
Assets API Router for Stations, Sections, Masts, and Signals.
"""

from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from app.repositories.network_repository import NetworkRepository
from app.repositories.csv_repository import CSVRepository
from app.config.settings import settings

router = APIRouter(tags=["Assets"])
network_repo = NetworkRepository()


@router.get("/assets", summary="Get Network Infrastructure Assets")
def get_assets(asset_type: str = Query("stations", enum=["stations", "sections", "geometry", "masts", "signals"]), page: int = 1, page_size: int = 50):
    """Returns paginated infrastructure assets."""
    mapping = {
        "stations": network_repo.stations_repo,
        "sections": network_repo.sections_repo,
        "geometry": network_repo.geometry_repo,
        "masts": network_repo.masts_repo,
        "signals": network_repo.signals_repo
    }
    repo = mapping[asset_type]
    return repo.filter_rows({}, page=page, page_size=page_size)


@router.get("/assets/locations", summary="Get All Geo-Spatial Asset & Task Locations for Map Visualization")
def get_asset_locations():
    """Returns geospatial location coordinates for interactive map visualization."""
    stations = network_repo.get_all_stations().to_dict("records")
    sections = network_repo.get_all_sections().to_dict("records")
    return {"stations": stations, "sections": sections}


@router.get("/assets/{asset_id}", summary="Get Single Asset Details")
def get_asset_by_id(asset_id: str):
    """Searches across infrastructure reference datasets for asset details."""
    for repo in (network_repo.stations_repo, network_repo.sections_repo, network_repo.masts_repo, network_repo.signals_repo):
        col = "station_code" if "station" in repo.file_path.name else ("section_id" if "section" in repo.file_path.name else ("mast_number" if "mast" in repo.file_path.name else "signal_id"))
        item = repo.get_by_id(col, asset_id)
        if item:
            return item
    raise HTTPException(status_code=404, detail=f"Asset '{asset_id}' not found.")
