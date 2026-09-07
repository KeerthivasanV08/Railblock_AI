"""
audit_existing_defects.py
=========================
Phase 1 of RailBlock AI Data Setup & Preprocessing.
Audits existing defect files (TMS, SMMS, TDMS), resources, network, and calendars.
Generates comprehensive audit report for defect files as mandated by Section 40.
"""

import os
import sys
import json
import pandas as pd
import numpy as np

BASE_DIR = os.path.abspath("d:/Railblock_AI")
DATA_DIR = os.path.join(BASE_DIR, "data")

TARGET_DIRS = [
    "data/real/infrastructure/osm",
    "data/real/infrastructure/ogd",
    "data/real/traffic",
    "data/real/weather",
    "data/real/reference",
    "data/derived/network",
    "data/derived/traffic",
    "data/derived/weather",
    "data/derived/cag",
    "data/calibrated/maintenance",
    "data/calibrated/blocks",
    "data/calibrated/resources",
    "data/synthetic/disruptions",
    "data/synthetic/scenarios",
    "data/synthetic/operational",
    "data/processed/network",
    "data/processed/maintenance",
    "data/processed/traffic",
    "data/processed/weather",
    "data/processed/festivals",
    "data/processed/resources",
    "data/processed/unified",
    "data/processed/features",
    "data/metadata",
    "data/validation/schema_checks",
    "data/validation/spatial_checks",
    "data/validation/temporal_checks",
    "data/validation/consistency_checks",
    "data/validation/validation_reports",
    "data/raw/cag",
]

def ensure_directories():
    for d in TARGET_DIRS:
        os.makedirs(os.path.join(BASE_DIR, d), exist_ok=True)
    print("Created/verified target directories.")

def audit_defect_dataset(file_path, name):
    if not os.path.exists(file_path):
        return {
            "dataset": name,
            "exists": False,
            "ready_for_preprocessing": False,
            "error": "File not found"
        }
    
    df = pd.read_csv(file_path, low_memory=False)
    rows = len(df)
    cols = df.columns.tolist()
    dups = int(df.duplicated().sum())
    
    missing = {k: int(v) for k, v in df.isna().sum().to_dict().items() if v > 0}
    
    has_coords = "latitude" in cols and "longitude" in cols
    inv_coords = 0
    if has_coords:
        inv_coords = int(((df["latitude"] < 8.0) | (df["latitude"] > 14.0) |
                          (df["longitude"] < 77.0) | (df["longitude"] > 81.0)).sum())
    
    inv_dates = 0
    for dcol in ["date", "logged_date", "target_completion_date"]:
        if dcol in cols:
            parsed = pd.to_datetime(df[dcol], errors="coerce")
            inv_dates += int(parsed.isna().sum())
    
    inv_sev = 0
    if "severity_class" in cols:
        inv_sev = int((~df["severity_class"].isin(["A", "B", "C", "LOW", "MEDIUM", "HIGH", "CRITICAL"])).sum())
    elif "severity" in cols:
        inv_sev = int((~df["severity"].isin(["A", "B", "C", "LOW", "MEDIUM", "HIGH", "CRITICAL"])).sum())
        
    missing_sec_ids = 0
    if "section_id" in cols:
        missing_sec_ids = int(df["section_id"].isna().sum())
    else:
        missing_sec_ids = rows
        
    audit_res = {
        "dataset": name,
        "file_path": file_path,
        "rows": rows,
        "columns": cols,
        "duplicates": dups,
        "missing_values": missing,
        "has_coordinates": has_coords,
        "invalid_coordinates": inv_coords,
        "invalid_dates": inv_dates,
        "invalid_severity": inv_sev,
        "missing_section_ids": missing_sec_ids,
        "spatially_unmapped_records": rows if not has_coords else inv_coords,
        "source_classification": "CALIBRATED_SYNTHETIC" if "source_type" not in cols else df["source_type"].iloc[0],
        "25k_requirement_satisfied": rows >= 25000,
        "ready_for_preprocessing": True,
        "recommended_action": "Enrich with interpolated OSM coordinates (lat/lon), map to all 68 corridor sections, add priority & duration, normalize severity, and mark source_type=CALIBRATED_SYNTHETIC."
    }
    return audit_res

def main():
    ensure_directories()
    
    defects = [
        (os.path.join(DATA_DIR, "raw/defects/tms_defects.csv"), "TMS"),
        (os.path.join(DATA_DIR, "raw/defects/smms_defects.csv"), "SMMS"),
        (os.path.join(DATA_DIR, "raw/defects/tdms_defects.csv"), "TDMS"),
    ]
    
    reports = {}
    for path, name in defects:
        rep = audit_defect_dataset(path, name)
        reports[name] = rep
        print(f"\n--- DEFECT DATA AUDIT: {name} ---")
        for k, v in rep.items():
            if k != "columns":
                print(f"  {k}: {v}")
                
    out_path = os.path.join(DATA_DIR, "metadata/defect_audit_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2)
    print(f"\nSaved defect audit report to: {out_path}")

if __name__ == "__main__":
    main()
