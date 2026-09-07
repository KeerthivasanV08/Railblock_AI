"""
OSM Corridor Extraction for RailBlock AI.

Identifies and extracts the Chennai Egmore (MS) -> Thoothukudi (TN) railway
corridor from the raw OSM track data using spatial spine filtering and
mainline attribute selection.

Input:
    data/raw/network/osm/chennai_thoothukudi/tracks_raw.geojson
    data/raw/network/osm/chennai_thoothukudi/stations_raw.geojson

Output:
    data/processed/network/corridor_tracks.geojson
"""

import json
import math
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
OSM_DIR = REPO_ROOT / "data" / "raw" / "network" / "osm" / "chennai_thoothukudi"
STATIONS_FILE = OSM_DIR / "stations_raw.geojson"
TRACKS_FILE = OSM_DIR / "tracks_raw.geojson"
OUTPUT_DIR = REPO_ROOT / "data" / "processed" / "network"
OUTPUT_GEOJSON = OUTPUT_DIR / "corridor_tracks.geojson"

# Key corridor waypoints along Chennai Egmore -> Tuticorin route
CORRIDOR_WAYPOINTS = [
    (13.0777, 80.2613),  # Chennai Egmore (MS)
    (13.0381, 80.2278),  # Mambalam (MBM)
    (12.9258, 80.1179),  # Tambaram (TBM)
    (12.6935, 79.9805),  # Chengalpattu (CGL)
    (12.5047, 79.8933),  # Madurantakam (MMK)
    (12.4287, 79.8329),  # Melmaruvattur (MLMR)
    (12.2292, 79.6515),  # Tindivanam (TMV)
    (11.9417, 79.4991),  # Viluppuram (VM)
    (11.5333, 79.3165),  # Vriddhachalam (VRI)
    (11.1489, 79.0686),  # Ariyalur (ALU)
    (10.8754, 78.8153),  # Lalgudi (LLI)
    (10.8577, 78.6960),  # Srirangam (SRGM)
    (10.7943, 78.6853),  # Tiruchchirappalli (TPJ)
    (10.6073, 78.4181),  # Manapparai (MPA)
    (10.5434, 78.3086),  # Vaiyampatti (VPJ)
    (10.4368, 78.1026),  # Vadamadurai (VDM)
    (9.9196, 78.1102),   # Madurai (MDU)
    (9.8791, 78.0652),   # Tiruparankundram (TDN)
    (9.5246, 78.1029),   # Aruppukkottai (APK)
    (8.9160, 78.1247),   # Thoothukudi line north approach
    (8.8278, 78.0232),   # Tattapparai (TIP)
    (8.8116, 78.0877),   # Milavittan (MVN)
    (8.8060, 78.1553),   # Tuticorin (TN)
]

CORRIDOR_LINE_NAMES = {
    "Line 1: Nagercoil - Chennai Egmore",
    "Line 2: Chennai Egmore - Nagercoil",
    "Madurai - Aruppukottai - Thoothukudi Line",
}


def _point_to_segment_distance(
    p: tuple[float, float], a: tuple[float, float], b: tuple[float, float]
) -> float:
    """Euclidean distance in degrees from point p to line segment ab."""
    px, py = p[1], p[0]  # lon, lat
    ax, ay = a[1], a[0]
    bx, by = b[1], b[0]
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    projx = ax + t * dx
    projy = ay + t * dy
    return math.hypot(px - projx, py - projy)


def _min_distance_to_corridor(
    lat: float, lon: float, waypoints: list[tuple[float, float]]
) -> float:
    """Find minimum distance from (lat, lon) to the corridor polyline."""
    p = (lat, lon)
    return min(
        _point_to_segment_distance(p, waypoints[i], waypoints[i + 1])
        for i in range(len(waypoints) - 1)
    )


def extract_corridor(
    tracks_data: dict[str, Any],
    max_dist_deg: float = 0.045,  # ~5 km buffer
    verbose: bool = True,
) -> list[dict[str, Any]]:
    """
    Extract all mainline track features belonging to the MS -> TN corridor.
    """
    features = tracks_data.get("features", [])
    if verbose:
        print(f"  Total raw track ways: {len(features):,}")

    corridor_features = []
    for feat in features:
        props = feat.get("properties") or {}
        geom = feat.get("geometry") or {}
        coords = geom.get("coordinates") or []
        if not coords or len(coords) < 2:
            continue

        # Basic railway filter
        railway = props.get("railway", "")
        if railway != "rail":
            continue

        # Exclude yards, spurs, and sidings unless named part of corridor line
        service = props.get("service")
        name = props.get("name") or ""
        if service in {"yard", "spur", "siding"} and name not in CORRIDOR_LINE_NAMES:
            continue

        # Exclude industrial usage
        usage = props.get("usage", "")
        if usage == "industrial" and name not in CORRIDOR_LINE_NAMES:
            continue

        # Filter out Sri Lanka features: lat < 9.8 and lon > 79.5
        lats = [c[1] for c in coords]
        lons = [c[0] for c in coords]
        if any(lat < 9.8 and lon > 79.5 for lon, lat in coords):
            continue

        # Bounds check: Corridor is within Tamil Nadu
        if max(lats) > 13.25 or min(lats) < 8.6 or min(lons) < 77.5 or max(lons) > 80.4:
            continue

        # Check distance of midpoint and endpoints to corridor polyline
        mid_idx = len(coords) // 2
        test_points = [
            (coords[0][1], coords[0][0]),
            (coords[mid_idx][1], coords[mid_idx][0]),
            (coords[-1][1], coords[-1][0]),
        ]

        min_d = min(_min_distance_to_corridor(lat, lon, CORRIDOR_WAYPOINTS) for lat, lon in test_points)
        if min_d <= max_dist_deg:
            corridor_features.append(feat)

    if verbose:
        print(f"  Extracted corridor track ways: {len(corridor_features):,}")

    return corridor_features


def save_corridor_geojson(
    features: list[dict[str, Any]], output_path: Path = OUTPUT_GEOJSON
) -> Path:
    """Save extracted features as a FeatureCollection GeoJSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fc = {
        "type": "FeatureCollection",
        "name": "chennai_thoothukudi_corridor_tracks",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": features,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(fc, f, indent=2)
    return output_path


def main():
    print("Loading tracks data...")
    with open(TRACKS_FILE, encoding="utf-8") as f:
        tracks_data = json.load(f)

    corridor_ways = extract_corridor(tracks_data, verbose=True)
    out_file = save_corridor_geojson(corridor_ways)
    print(f"Saved {len(corridor_ways)} corridor ways to {out_file}")


if __name__ == "__main__":
    main()
