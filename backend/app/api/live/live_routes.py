"""
Live Train Operations API Routes.

Provides real-time and near-real-time train position data derived from
the traffic dataset (train_delays.csv and timetable.csv).

Routes:
    GET  /live/trains   — Current train positions derived from delay records
    GET  /live/status   — Provider connection status
    POST /live/sync     — Force a data sync (idempotent)

Data provenance: DERIVED
    - Train positions are inferred from scheduled chainage + delay offsets.
    - No real GPS telemetry; values are operationally plausible estimates
      derived from the Chennai Egmore–Thoothukudi corridor timetable.
"""

from typing import Optional
from fastapi import APIRouter, Query
from app.repositories.traffic_repository import TrafficRepository

router = APIRouter(prefix="/live", tags=["Live Operations"])
traffic_repo = TrafficRepository()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _derive_km(section_id: str, from_km: float, to_km: float, progress: float = 0.5) -> float:
    """Estimate chainage position within a section (linear interpolation)."""
    return round(from_km + (to_km - from_km) * max(0.0, min(1.0, progress)), 1)


def _normalise_direction(train_type: Optional[str]) -> str:
    """Map train type string to UP/DOWN direction."""
    if not train_type:
        return "UP"
    t = train_type.upper()
    if "DOWN" in t or "TOWARDS" in t:
        return "DOWN"
    return "UP"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/trains", summary="Get Derived Train Positions for Corridor")
def get_live_trains(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
):
    """
    Returns derived train positions for the Chennai Egmore–Thoothukudi corridor.

    Position is estimated from the timetable chainage data and live delay records.
    Speed is set to 60 km/h when delay > 0 (cautious speed) else 80 km/h (scheduled).

    Response shape is compatible with the frontend LiveTrainPosition interface.
    """
    try:
        delay_res = traffic_repo.delays_repo.filter_rows({}, page=page, page_size=page_size)
        delay_items = delay_res.get("items", []) or delay_res.get("records", []) or []

        positions = []
        for rec in delay_items:
            train_number = str(rec.get("train_number", rec.get("train_id", "UNK")))
            section_id   = str(rec.get("section_id", "MS-PA"))
            delay_min    = float(rec.get("delay_minutes", rec.get("delay_min", 0)) or 0)
            from_km      = float(rec.get("from_km", 0) or 0)
            to_km        = float(rec.get("to_km", from_km + 15) or from_km + 15)
            direction    = _normalise_direction(rec.get("direction") or rec.get("train_type"))
            speed        = 60.0 if delay_min > 0 else 80.0

            positions.append({
                "train_id":      train_number,
                "train_number":  train_number,
                "name":          str(rec.get("train_name", f"Train {train_number}")),
                "category":      str(rec.get("train_type", "Express")),
                "direction":     direction,
                "section_id":    section_id,
                "current_km":    _derive_km(section_id, from_km, to_km, 0.5),
                "speed_kmph":    speed,
                "delay_minutes": delay_min,
                "origin":        str(rec.get("origin_station", "Chennai Egmore")),
                "destination":   str(rec.get("destination_station", "Thoothukudi")),
                "data_provenance": "DERIVED",
            })

        return {
            "provider_status": {"csv_delay_data": "AVAILABLE"},
            "source": "derived_from_csv",
            "total": len(positions),
            "items": positions,
        }

    except Exception as exc:  # noqa: BLE001
        return {
            "provider_status": {"csv_delay_data": "UNAVAILABLE", "error": str(exc)},
            "source": "error",
            "total": 0,
            "items": [],
        }


@router.get("/status", summary="Live Data Provider Connection Status")
def get_live_status():
    """Returns connection health for live data providers."""
    try:
        # Quick existence check for delay data
        sample = traffic_repo.delays_repo.filter_rows({}, page=1, page_size=1)
        has_data = len(sample.get("items", [])) > 0
        return {
            "status": "AVAILABLE" if has_data else "EMPTY",
            "providers": {
                "train_delay_csv": "AVAILABLE" if has_data else "NO_DATA",
                "gps_telemetry": "UNAVAILABLE",
                "ntes_api": "UNAVAILABLE",
            },
            "note": "Train positions are derived from delay CSV data. Real GPS/NTES integration not implemented.",
            "data_provenance": "DERIVED",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "ERROR",
            "providers": {"train_delay_csv": f"ERROR: {exc}"},
            "data_provenance": "UNAVAILABLE",
        }


@router.post("/sync", summary="Sync Live Train Data (Idempotent)")
def sync_live_data():
    """
    Idempotent sync endpoint.  For CSV-based providers there is no external
    push to perform; the data is read on demand.  Returns current record count.
    """
    try:
        sample = traffic_repo.delays_repo.filter_rows({}, page=1, page_size=1)
        total = sample.get("total", 0)
        return {
            "status": "SYNCED",
            "provider": "csv",
            "records_available": total,
            "message": "CSV delay data is read on-demand; no push sync required.",
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "ERROR", "message": str(exc)}
