"""
Master OSM Network Processing Pipeline for RailBlock AI.

Executes the end-to-end migration pipeline from raw OpenStreetMap GeoJSON
to production network CSV and GeoJSON datasets for Module 1.

Usage:
    python scripts/osm/run_pipeline.py
"""

import sys
import time
from pathlib import Path
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.osm.extract_corridor import extract_corridor, save_corridor_geojson, TRACKS_FILE
from scripts.osm.process_stations import get_corridor_stations, save_stations_geojson
from scripts.osm.process_tracks import build_section_geometries, save_tracks_geojson
from scripts.osm.build_network import (
    build_network_tables,
    save_network_tables,
    PROCESSED_NETWORK_DIR,
    RAW_NETWORK_DIR,
)


def validate_network() -> bool:
    """
    Validates that the generated network tables meet all architectural
    and database integrity requirements.
    """
    print("\n--- Validating Generated Network Tables ---")
    stations = pd.read_csv(RAW_NETWORK_DIR / "stations.csv")
    sections = pd.read_csv(RAW_NETWORK_DIR / "block_sections.csv")
    geometry = pd.read_csv(RAW_NETWORK_DIR / "track_geometry.csv")
    masts = pd.read_csv(RAW_NETWORK_DIR / "ohe_mast_reference.csv")
    signals = pd.read_csv(RAW_NETWORK_DIR / "signal_reference.csv")

    errors = []

    # 1. Row count constraints
    if len(stations) < 40:
        errors.append(f"Expected >= 40 stations, found {len(stations)}")
    if len(sections) < 30:
        errors.append(f"Expected >= 30 sections, found {len(sections)}")
    if len(geometry) < 100:
        errors.append(f"Expected >= 100 geometry segments, found {len(geometry)}")

    # 2. Key uniqueness
    if not stations["station_code"].is_unique:
        errors.append("Duplicate station_code found in stations.csv")
    if not sections["section_id"].is_unique:
        errors.append("Duplicate section_id found in block_sections.csv")
    if not geometry["segment_id"].is_unique:
        errors.append("Duplicate segment_id found in track_geometry.csv")
    if not masts["mast_number"].is_unique:
        errors.append("Duplicate mast_number found in ohe_mast_reference.csv")
    if not signals["signal_id"].is_unique:
        errors.append("Duplicate signal_id found in signal_reference.csv")

    # 3. Monotonic section chainage
    if not (sections["start_km"] < sections["end_km"]).all():
        errors.append("Found block section where start_km >= end_km")

    # 4. Station foreign keys in sections
    st_codes = set(stations["station_code"])
    for _, row in sections.iterrows():
        if row["from_station"] not in st_codes:
            errors.append(f"Unknown from_station {row['from_station']} in section {row['section_id']}")
        if row["to_station"] not in st_codes:
            errors.append(f"Unknown to_station {row['to_station']} in section {row['section_id']}")

    # 5. Section foreign keys in geometry, masts, signals
    sec_ids = set(sections["section_id"])
    if not set(geometry["section_id"]).issubset(sec_ids):
        errors.append("Invalid section_id found in track_geometry.csv")
    if not set(masts["section_id"]).issubset(sec_ids):
        errors.append("Invalid section_id found in ohe_mast_reference.csv")
    if not set(signals["section_id"]).issubset(sec_ids):
        errors.append("Invalid section_id found in signal_reference.csv")

    # 6. Check Tamil Nadu bounding box for coordinates
    if not (
        (8.5 <= stations["latitude"]) & (stations["latitude"] <= 13.5)
    ).all() or not (
        (77.5 <= stations["longitude"]) & (stations["longitude"] <= 80.5)
    ).all():
        errors.append("Station coordinates out of Tamil Nadu bounds (lat 8.5-13.5, lon 77.5-80.5)")

    if errors:
        print("[FAIL] Validation failed with the following errors:")
        for err in errors:
            print(f"  - {err}")
        return False

    print("[PASS] All validation checks passed successfully!")
    print(f"  Stations:       {len(stations)} ({stations.iloc[0]['station_code']} -> {stations.iloc[-1]['station_code']})")
    print(f"  Block Sections: {len(sections)} ({sections.iloc[0]['start_km']} -> {sections.iloc[-1]['end_km']} km)")
    print(f"  Geometry:       {len(geometry)} segments")
    print(f"  OHE Masts:      {len(masts)}")
    print(f"  Signals:        {len(signals)}")
    return True


def run_pipeline():
    start_time = time.time()
    print("=================================================================")
    print("RailBlock AI — Module 1 OSM Pipeline Runner")
    print("Corridor: Chennai Egmore (MS) -> Thoothukudi (TN)")
    print("=================================================================\n")

    # Step 1: Extract Corridor
    print("[Step 1/5] Extracting corridor track ways from OSM raw data...")
    import json
    with open(TRACKS_FILE, encoding="utf-8") as f:
        tracks_data = json.load(f)
    corridor_ways = extract_corridor(tracks_data, verbose=True)
    corridor_geojson_path = save_corridor_geojson(corridor_ways)
    print(f"  -> Saved {len(corridor_ways)} corridor ways to {corridor_geojson_path.name}")

    # Step 2: Normalize Stations
    print("\n[Step 2/5] Normalizing corridor stations...")
    stations = get_corridor_stations()
    stations_geojson_path = save_stations_geojson(stations)
    print(f"  -> Saved {len(stations)} stations to {stations_geojson_path.name}")

    # Step 3: Process Track Geometry
    print("\n[Step 3/5] Building section track geometries...")
    with open(corridor_geojson_path, encoding="utf-8") as f:
        loaded_corridor_tracks = json.load(f)
    section_geoms = build_section_geometries(stations, loaded_corridor_tracks)
    tracks_geojson_path = save_tracks_geojson(section_geoms)
    print(f"  -> Saved {len(section_geoms)} section tracks to {tracks_geojson_path.name}")

    # Step 4: Build Production Network Tables
    print("\n[Step 4/5] Generating production network tables...")
    stations_df, sections_df, geometry_df, masts_df, signals_df = build_network_tables(verbose=False)
    save_network_tables(stations_df, sections_df, geometry_df, masts_df, signals_df, PROCESSED_NETWORK_DIR)
    save_network_tables(stations_df, sections_df, geometry_df, masts_df, signals_df, RAW_NETWORK_DIR)
    print("  -> Updated production CSVs in data/processed/network/ and data/raw/network/")

    # Step 5: Validate
    print("\n[Step 5/5] Validating outputs...")
    success = validate_network()

    elapsed = time.time() - start_time
    print(f"\nPipeline finished in {elapsed:.2f} seconds.")
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    run_pipeline()
