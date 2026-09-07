"""
OSM Raw Data Inspector for RailBlock AI.

Reads the raw OSM GeoJSON files (immutable source data) and prints a
comprehensive summary of their content: feature counts, available tags,
coordinate extents, and notable stations.

Usage:
    python scripts/osm/inspect_osm.py

Source data (READ-ONLY):
    data/raw/network/osm/chennai_thoothukudi/stations_raw.geojson
    data/raw/network/osm/chennai_thoothukudi/tracks_raw.geojson
"""

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
OSM_DIR = REPO_ROOT / "data" / "raw" / "network" / "osm" / "chennai_thoothukudi"
STATIONS_FILE = OSM_DIR / "stations_raw.geojson"
TRACKS_FILE = OSM_DIR / "tracks_raw.geojson"


def _load_geojson(path: Path) -> dict[str, Any]:
    """Load a GeoJSON file."""
    if not path.exists():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _coord_bounds(features: list[dict]) -> dict[str, float]:
    """Compute min/max lat/lon across all features."""
    lons, lats = [], []
    for feat in features:
        geom = feat.get("geometry", {})
        if not geom:
            continue
        coords = geom.get("coordinates", [])
        gtype = geom.get("type", "")
        if gtype == "Point":
            lons.append(coords[0])
            lats.append(coords[1])
        elif gtype == "LineString":
            for pt in coords:
                lons.append(pt[0])
                lats.append(pt[1])
    if not lons:
        return {}
    return {
        "min_lon": min(lons),
        "max_lon": max(lons),
        "min_lat": min(lats),
        "max_lat": max(lats),
    }


def inspect_stations(data: dict[str, Any]) -> None:
    """Print summary of station features."""
    features = data.get("features", [])
    print(f"\n{'='*70}")
    print(f"  STATIONS — {STATIONS_FILE.name}")
    print(f"{'='*70}")
    print(f"  Total features : {len(features)}")

    geom_types = Counter(f["geometry"]["type"] for f in features if f.get("geometry"))
    print(f"  Geometry types : {dict(geom_types)}")

    bounds = _coord_bounds(features)
    if bounds:
        print(f"  Lat range      : {bounds['min_lat']:.4f} → {bounds['max_lat']:.4f}")
        print(f"  Lon range      : {bounds['min_lon']:.4f} → {bounds['max_lon']:.4f}")

    # Tag frequency
    tag_counter: Counter = Counter()
    operator_counter: Counter = Counter()
    ref_counter: Counter = Counter()

    target_stations = []
    all_stations = []

    for feat in features:
        props = feat.get("properties", {}) or {}
        for k in props:
            tag_counter[k] += 1
        op = props.get("operator", "")
        if op:
            operator_counter[op] += 1
        ref = props.get("ref", "")
        name = props.get("name", "")
        geom = feat.get("geometry", {}) or {}
        coords = geom.get("coordinates", [0, 0])
        lat = coords[1] if len(coords) >= 2 else 0
        lon = coords[0] if len(coords) >= 2 else 0

        if ref:
            ref_counter[ref] += 1

        station_entry = {
            "name": name,
            "ref": ref,
            "operator": op,
            "lat": lat,
            "lon": lon,
            "osm_id": props.get("@id", ""),
        }
        all_stations.append(station_entry)

        # Flag corridor endpoints
        name_lower = name.lower()
        ref_upper = ref.upper()
        if any(k in name_lower for k in ["egmore", "chennai egmore"]) or ref_upper in ("MS", "MAS"):
            station_entry["_match"] = "EGMORE_CANDIDATE"
            target_stations.append(station_entry)
        if any(k in name_lower for k in ["thoothukudi", "tuticorin"]) or ref_upper in ("TEN",):
            station_entry["_match"] = "THOOTHUKUDI_CANDIDATE"
            target_stations.append(station_entry)

    print(f"\n  Top tag keys   : {', '.join(k for k, _ in tag_counter.most_common(12))}")
    print(f"  Unique refs    : {len(ref_counter)}")
    print(f"  Unique operators: {dict(operator_counter.most_common(5))}")

    print(f"\n  --- Corridor endpoint candidates ---")
    if target_stations:
        for s in target_stations:
            print(f"    [{s.get('_match','')}] name={s['name']!r:40s} ref={s['ref']!r:8s} lat={s['lat']:.5f} lon={s['lon']:.5f}  osm_id={s['osm_id']}")
    else:
        print("    (none found by name/ref — will need geo-proximity matching)")

    print(f"\n  --- All stations with ref codes (SR operator) ---")
    sr_stations = [s for s in all_stations if s["operator"] in ("SR", "Southern Railway")]
    sr_stations.sort(key=lambda x: x["lat"])
    for s in sr_stations[:60]:
        print(f"    name={s['name']!r:45s} ref={s['ref']!r:8s} lat={s['lat']:.5f} lon={s['lon']:.5f}")
    if len(sr_stations) > 60:
        print(f"    ... and {len(sr_stations) - 60} more SR stations")

    print(f"\n  --- All stations with ref codes (any operator, lat 8–14) ---")
    corridor_area = [s for s in all_stations if 8.0 <= s["lat"] <= 14.0 and 77.0 <= s["lon"] <= 81.0]
    corridor_area.sort(key=lambda x: x["lat"])
    for s in corridor_area:
        print(f"    name={s['name']!r:45s} ref={s['ref']!r:8s} lat={s['lat']:.5f} lon={s['lon']:.5f}  op={s['operator']!r}")


def inspect_tracks(data: dict[str, Any]) -> None:
    """Print summary of track features."""
    features = data.get("features", [])
    print(f"\n{'='*70}")
    print(f"  TRACKS — {TRACKS_FILE.name}")
    print(f"{'='*70}")
    print(f"  Total features : {len(features)}")

    geom_types = Counter(f["geometry"]["type"] for f in features if f.get("geometry"))
    print(f"  Geometry types : {dict(geom_types)}")

    bounds = _coord_bounds(features)
    if bounds:
        print(f"  Lat range      : {bounds['min_lat']:.4f} → {bounds['max_lat']:.4f}")
        print(f"  Lon range      : {bounds['min_lon']:.4f} → {bounds['max_lon']:.4f}")

    usage_counter: Counter = Counter()
    gauge_counter: Counter = Counter()
    electrified_counter: Counter = Counter()
    name_counter: Counter = Counter()
    railway_counter: Counter = Counter()

    total_coord_pts = 0

    for feat in features:
        props = feat.get("properties", {}) or {}
        usage_counter[props.get("usage", "(none)")] += 1
        gauge_counter[props.get("gauge", "(none)")] += 1
        electrified_counter[props.get("electrified", "(none)")] += 1
        railway_counter[props.get("railway", "(none)")] += 1
        name = props.get("name", "")
        if name:
            name_counter[name] += 1
        geom = feat.get("geometry", {}) or {}
        coords = geom.get("coordinates", [])
        total_coord_pts += len(coords)

    print(f"\n  Usage values   : {dict(usage_counter.most_common(8))}")
    print(f"  Railway values : {dict(railway_counter.most_common(8))}")
    print(f"  Gauge values   : {dict(gauge_counter.most_common(5))}")
    print(f"  Electrified    : {dict(electrified_counter.most_common(5))}")
    print(f"  Total coord pts: {total_coord_pts:,}")
    print(f"\n  Top 20 named lines:")
    for name, count in name_counter.most_common(20):
        print(f"    {count:4d}x  {name!r}")

    print(f"\n  --- 'main' usage tracks (sample first 8) ---")
    main_tracks = [f for f in features if (f.get("properties") or {}).get("usage") == "main"]
    print(f"  Count of 'main' usage tracks: {len(main_tracks)}")
    for feat in main_tracks[:8]:
        props = feat.get("properties", {}) or {}
        coords = feat["geometry"]["coordinates"]
        start = coords[0]
        end = coords[-1]
        print(
            f"    osm_id={props.get('@id',''):<18s} name={props.get('name','')!r:<40s} "
            f"gauge={props.get('gauge','?'):6s} pts={len(coords):4d} "
            f"start=({start[1]:.4f},{start[0]:.4f}) end=({end[1]:.4f},{end[0]:.4f})"
        )

    print(f"\n  --- Tracks in corridor lat band (8.7–13.2, lon 77-81) ---")
    corridor_tracks = []
    for feat in features:
        geom = feat.get("geometry", {}) or {}
        coords = geom.get("coordinates", [])
        if not coords:
            continue
        mid_idx = len(coords) // 2
        mid_lon, mid_lat = coords[mid_idx][0], coords[mid_idx][1]
        if 8.7 <= mid_lat <= 13.2 and 77.0 <= mid_lon <= 81.0:
            corridor_tracks.append(feat)
    print(f"  Tracks in geographic band: {len(corridor_tracks)}")


def main() -> None:
    print("RailBlock AI — OSM Raw Data Inspector")
    print(f"Source directory: {OSM_DIR}")

    stations_data = _load_geojson(STATIONS_FILE)
    tracks_data = _load_geojson(TRACKS_FILE)

    inspect_stations(stations_data)
    inspect_tracks(tracks_data)

    print(f"\n{'='*70}")
    print("  Inspection complete. No files were modified.")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
