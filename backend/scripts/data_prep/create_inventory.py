"""
Data Inventory Generator for RailBlock AI.

Discovers, inspects, and catalogs all datasets in the repository into
data/metadata/data_inventory.csv.
"""

import os
import sys
import json
from pathlib import Path
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
OUTPUT_FILE = DATA_DIR / "metadata" / "data_inventory.csv"


def inspect_file(file_path: Path) -> dict:
    rel_path = file_path.relative_to(REPO_ROOT)
    ext = file_path.suffix.lower()
    sz = file_path.stat().st_size
    dataset_name = file_path.stem

    row_count = None
    column_count = None
    source = "Unknown"
    source_type = "Unknown"
    date_range = "N/A"
    geo_scope = "National"
    status = "Raw"
    notes = ""

    # Classify by path & name
    p_str = str(rel_path).replace("\\", "/")

    if "Train_details" in file_path.name:
        source = "Indian Railways published timetable (OGD)"
        source_type = "Official Government"
        geo_scope = "National (India)"
        date_range = "December 2017"
        notes = "National train timetable schedule with 186k+ station stops"
    elif "68_Railway_Key_Statistics" in file_path.name:
        source = "Ministry of Railways / OGD India"
        source_type = "Official Government"
        geo_scope = "National (India)"
        date_range = "1950-51 to 2013-14"
        notes = "Annual operating metrics: Train-km per running track km per day, Passenger-km, Net Tonne-km"
    elif "Report" in file_path.name and ext == ".pdf":
        source = "Comptroller and Auditor General (CAG) of India"
        source_type = "Official Audit Report"
        geo_scope = "National (India)"
        notes = "Audit on track maintenance and traffic performance"
    elif "osm" in p_str:
        source = "OpenStreetMap (OSM)"
        source_type = "Geospatial Vector"
        geo_scope = "Chennai -> Thoothukudi Corridor (Tamil Nadu)"
        notes = "Extracted railway track and station nodes/ways"
    elif "synthetic" in p_str or "backup" in p_str:
        source = "RailBlock Synthetic Generator (Legacy NDLS-CNB)"
        source_type = "Synthetic"
        geo_scope = "New Delhi - Kanpur"
        notes = "Legacy synthetic baseline files"
    elif "processed" in p_str:
        source = "RailBlock Processed Pipeline"
        source_type = "Processed"
        geo_scope = "Chennai -> Thoothukudi Corridor"
        status = "Processed"
    elif "defects" in p_str:
        source = "Departmental Defect Systems (TMS / SMMS / TDMS)"
        source_type = "Operational Defects"
        geo_scope = "Corridor"
        notes = "P-Way, OHE, and S&T maintenance defect logs"
    elif "traffic" in p_str:
        source = "RailBlock Traffic Subsystem"
        source_type = "Operational Traffic"
        geo_scope = "Corridor"

    # Count rows/columns for tabular files
    if ext == ".csv":
        try:
            # fast read sample for column count
            sample_df = pd.read_csv(file_path, nrows=5)
            column_count = len(sample_df.columns)
            # count lines
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                row_count = sum(1 for _ in f) - 1  # exclude header
                if row_count < 0:
                    row_count = 0
        except Exception as e:
            notes += f" Read error: {e}"
    elif ext == ".geojson" or ext == ".json":
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                d = json.load(f)
                if isinstance(d, dict) and "features" in d:
                    row_count = len(d["features"])
                    column_count = "GeoJSON Feature"
                elif isinstance(d, list):
                    row_count = len(d)
                elif isinstance(d, dict):
                    row_count = len(d.keys())
        except Exception as e:
            notes += f" JSON read error: {e}"

    return {
        "dataset_name": dataset_name,
        "file_path": p_str,
        "file_type": ext,
        "file_size_bytes": sz,
        "row_count": row_count,
        "column_count": column_count,
        "source": source,
        "source_type": source_type,
        "date_range": date_range,
        "geographic_scope": geo_scope,
        "status": status,
        "notes": notes.strip(),
    }


def main():
    print("Scanning repository data files...")
    records = []
    for root, _, files in os.walk(DATA_DIR):
        for f in sorted(files):
            # Ignore pycache
            if "__pycache__" in root:
                continue
            p = Path(root) / f
            records.append(inspect_file(p))

    df = pd.DataFrame(records)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Cataloged {len(df)} files into {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
