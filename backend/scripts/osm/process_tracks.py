"""
OSM Track Processing and Section Geometry Generation for RailBlock AI.

Processes extracted corridor track ways and constructs continuous,
ordered track geometry for each station-to-station block section
along the Chennai Egmore (MS) -> Thoothukudi (TN) corridor.

Input:
    data/processed/network/corridor_tracks.geojson
    data/processed/network/stations_normalized.geojson

Output:
    data/processed/network/tracks_normalized.geojson
"""

import json
import math
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
NETWORK_PROCESSED_DIR = REPO_ROOT / "data" / "processed" / "network"
CORRIDOR_TRACKS_FILE = NETWORK_PROCESSED_DIR / "corridor_tracks.geojson"
STATIONS_FILE = NETWORK_PROCESSED_DIR / "stations_normalized.geojson"
OUTPUT_TRACKS_FILE = NETWORK_PROCESSED_DIR / "tracks_normalized.geojson"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometers between two lat/lon pairs."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def project_point_on_segment(
    p: tuple[float, float], a: tuple[float, float], b: tuple[float, float]
) -> tuple[float, float]:
    """
    Project point p(lat, lon) onto segment a(lat, lon) -> b(lat, lon).
    Returns (t, perp_dist_km), where t in [0, 1] is the fractional distance along ab.
    """
    ax, ay = a[1], a[0]  # lon, lat
    bx, by = b[1], b[0]
    px, py = p[1], p[0]
    dx, dy = bx - ax, by - ay
    line_len_sq = dx * dx + dy * dy
    if line_len_sq == 0:
        return 0.0, haversine_km(p[0], p[1], a[0], a[1])

    t = ((px - ax) * dx + (py - ay) * dy) / line_len_sq
    t_clamped = max(0.0, min(1.0, t))
    proj_lat = ay + t_clamped * dy
    proj_lon = ax + t_clamped * dx
    perp_dist = haversine_km(p[0], p[1], proj_lat, proj_lon)
    return t, perp_dist


def build_section_geometries(
    stations: list[dict[str, Any]],
    corridor_tracks: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Build ordered geometry coordinates for each station-to-station block section.
    """
    # Extract all vertices from candidate track ways
    track_vertices: list[tuple[float, float]] = []
    for feat in corridor_tracks.get("features", []):
        coords = feat.get("geometry", {}).get("coordinates", [])
        for c in coords:
            track_vertices.append((c[1], c[0]))  # (lat, lon)

    sections = []
    cum_km = 0.0

    for i in range(len(stations) - 1):
        st1 = stations[i]
        st2 = stations[i + 1]
        p1 = (st1["latitude"], st1["longitude"])
        p2 = (st2["latitude"], st2["longitude"])
        sec_id = f"SEC_{i + 1:03d}"

        # Bounding box for candidates between st1 and st2
        min_lat = min(p1[0], p2[0]) - 0.015
        max_lat = max(p1[0], p2[0]) + 0.015
        min_lon = min(p1[1], p2[1]) - 0.015
        max_lon = max(p1[1], p2[1]) + 0.015

        # Find track vertices along this section
        candidates = []
        for lat, lon in track_vertices:
            if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
                t, perp_dist = project_point_on_segment((lat, lon), p1, p2)
                if 0.02 < t < 0.98 and perp_dist < 0.8:  # within 800m of line
                    candidates.append((t, lat, lon))

        # Sort along direction from st1 to st2
        candidates.sort(key=lambda x: x[0])

        # Filter out points that are too close together (< 200 m) to avoid redundant vertices
        filtered_points = [p1]
        last_pt = p1
        for _, lat, lon in candidates:
            pt = (lat, lon)
            if haversine_km(last_pt[0], last_pt[1], lat, lon) >= 0.2:
                filtered_points.append(pt)
                last_pt = pt

        filtered_points.append(p2)

        # If section only has endpoints, insert a 50% midpoint to ensure at least 2 segments
        if len(filtered_points) == 2:
            mid_lat = (p1[0] + p2[0]) / 2.0
            mid_lon = (p1[1] + p2[1]) / 2.0
            filtered_points.insert(1, (mid_lat, mid_lon))

        # Calculate cumulative distances along this section's polyline
        seg_lengths = []
        for j in range(len(filtered_points) - 1):
            d = haversine_km(
                filtered_points[j][0],
                filtered_points[j][1],
                filtered_points[j + 1][0],
                filtered_points[j + 1][1],
            )
            # Ensure non-zero length
            seg_lengths.append(max(0.01, d))

        sec_total_length = sum(seg_lengths)
        start_km = round(cum_km, 3)
        end_km = round(cum_km + sec_total_length, 3)
        cum_km = end_km

        sections.append({
            "section_id": sec_id,
            "from_station": st1["station_code"],
            "to_station": st2["station_code"],
            "start_km": start_km,
            "end_km": end_km,
            "length_km": round(sec_total_length, 3),
            "points": filtered_points,
            "seg_lengths": seg_lengths,
        })

    return sections


def save_tracks_geojson(
    sections: list[dict[str, Any]], output_path: Path = OUTPUT_TRACKS_FILE
) -> Path:
    """Save the section track polylines as GeoJSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    features = []
    for sec in sections:
        coords = [[pt[1], pt[0]] for pt in sec["points"]]  # [lon, lat]
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": coords,
            },
            "properties": {
                "section_id": sec["section_id"],
                "from_station": sec["from_station"],
                "to_station": sec["to_station"],
                "start_km": sec["start_km"],
                "end_km": sec["end_km"],
                "length_km": sec["length_km"],
            },
        })

    fc = {
        "type": "FeatureCollection",
        "name": "chennai_thoothukudi_sections_geometry",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": features,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(fc, f, indent=2)
    return output_path


def main():
    from scripts.osm.process_stations import get_corridor_stations

    print("Loading corridor stations and track features...")
    stations = get_corridor_stations()
    with open(CORRIDOR_TRACKS_FILE, encoding="utf-8") as f:
        corridor_tracks = json.load(f)

    sections = build_section_geometries(stations, corridor_tracks)
    out_file = save_tracks_geojson(sections)

    total_len = sections[-1]["end_km"]
    total_pts = sum(len(s["points"]) for s in sections)
    print(f"Generated {len(sections)} block sections with {total_pts} track vertices.")
    print(f"Total corridor length: {total_len:.2f} km.")
    print(f"Saved to: {out_file}")


if __name__ == "__main__":
    main()
