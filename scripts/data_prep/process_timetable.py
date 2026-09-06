"""
process_timetable.py
====================
RailBlock AI — Data Preprocessing Phase
Timetable Pipeline (Step 2 of Implementation Plan)

Inputs:
  data/raw/Train_details_22122017.csv

Outputs:
  data/processed/timetable/train_timetable.csv           — Canonical normalized timetable
  data/processed/timetable/corridor_trains.csv           — Trains serving Chennai→Thoothukudi corridor
  data/processed/timetable/train_section_occupancy.csv   — Per-section traversal windows for corridor trains
  data/defects/timetable_defects.csv                     — Logged defects (shifted rows, bad times, seq anomalies)
  data/metadata/timetable_profile.json                   — Dataset profile statistics

Constraints:
  - No ML/AI model training.
  - No optimization.
  - No fabrication of real railway operational data.
  - Raw source file is never modified.
"""

import os
import re
import json
import logging
import pandas as pd
from datetime import datetime

# ── Configuration ────────────────────────────────────────────────────────────

CANONICAL_TIMETABLE = "data/raw/timetable/ogd/railway_train_details_original.csv"
FALLBACK_TIMETABLE  = "data/raw/Train_details_22122017.csv"
RAW_TIMETABLE = CANONICAL_TIMETABLE if os.path.exists(CANONICAL_TIMETABLE) else FALLBACK_TIMETABLE

OUT_TIMETABLE  = "data/processed/timetable/train_timetable.csv"
OUT_CORRIDOR   = "data/processed/timetable/corridor_trains.csv"
OUT_OCCUPANCY  = "data/processed/timetable/train_section_occupancy.csv"
OUT_DEFECTS    = "data/defects/timetable_defects.csv"
OUT_PROFILE    = "data/metadata/timetable_profile.json"

# Corridor anchor stations (OGD station codes)
CORRIDOR_ANCHORS = {
    "origin":      {"MS", "MSB", "MAS"},
    "destination": {"TEN", "TUC", "TPJ", "MDU"},
}

SOURCE_URL = "https://data.gov.in/resource/train-details"

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────

TIME_RE = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?$")


def normalize_time(val):
    """Return HH:MM:SS string, or None if unparseable."""
    if pd.isna(val):
        return None
    s = str(val).strip()
    if not TIME_RE.match(s):
        return None
    parts = s.split(":")
    try:
        hh, mm = int(parts[0]), int(parts[1])
        ss = int(parts[2]) if len(parts) == 3 else 0
        if 0 <= hh <= 47 and 0 <= mm <= 59 and 0 <= ss <= 59:
            return "{:02d}:{:02d}:{:02d}".format(hh, mm, ss)
    except (ValueError, IndexError):
        pass
    return None


def make_defect(row_idx, train_no, station_code, field, severity, description, raw_value=None):
    return {
        "row_index":    row_idx,
        "train_number": train_no,
        "station_code": station_code,
        "field":        field,
        "severity":     severity,
        "description":  description,
        "raw_value":    str(raw_value) if raw_value is not None else None,
        "detected_at":  datetime.utcnow().isoformat(),
    }


def ensure_dirs():
    for d in [
        "data/processed/timetable",
        "data/defects",
        "data/metadata",
    ]:
        os.makedirs(d, exist_ok=True)


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run():
    ensure_dirs()
    defects = []

    # 1. Load raw timetable
    log.info("Loading raw timetable: %s", RAW_TIMETABLE)
    raw = pd.read_csv(
        RAW_TIMETABLE,
        encoding="utf-8",
        on_bad_lines="skip",
        dtype={"Train No": str, "SEQ": str, "Distance": str},
    )
    log.info("Raw shape: %d rows x %d cols", *raw.shape)

    profile_raw_rows = len(raw)
    profile_raw_cols = raw.shape[1]

    # 2. Rename columns to canonical schema
    col_map = {
        "Train No":               "train_number",
        "Train Name":             "train_name",
        "SEQ":                    "sequence",
        "Station Code":           "station_code",
        "Station Name":           "station_name",
        "Arrival time":           "arrival_time",
        "Departure Time":         "departure_time",
        "Distance":               "distance_km",
        "Source Station":         "source_station_code",
        "Source Station Name":    "source_station_name",
        "Destination Station":    "destination_station_code",
        "Destination Station Name": "destination_station_name",
    }
    raw = raw.rename(columns=col_map)

    # 3. Basic type coercions
    raw["train_number"] = pd.to_numeric(raw["train_number"], errors="coerce")
    raw["sequence"]     = pd.to_numeric(raw["sequence"],     errors="coerce")
    raw["distance_km"]  = pd.to_numeric(raw["distance_km"],  errors="coerce")

    # 4. Detect & log shifted rows (arrival_time contains non-time value)
    shifted_mask = raw["arrival_time"].apply(
        lambda v: bool(str(v).strip()) and not bool(TIME_RE.match(str(v).strip()))
        if pd.notna(v) else False
    )
    shifted_idx = raw.index[shifted_mask].tolist()
    log.info("Detected %d shifted/malformed rows", len(shifted_idx))
    for idx in shifted_idx:
        r = raw.loc[idx]
        defects.append(make_defect(
            idx, r.get("train_number"), r.get("station_code"),
            "arrival_time", "HIGH",
            "Column shift detected: arrival_time contains non-time value; row excluded.",
            raw_value=r.get("arrival_time"),
        ))

    df = raw.loc[~shifted_mask].copy()
    log.info("Rows after shift exclusion: %d", len(df))

    # 5. Validate & normalize times
    for col in ("arrival_time", "departure_time"):
        bad_mask = df[col].apply(lambda v: pd.notna(v) and normalize_time(v) is None)
        for idx in df.index[bad_mask]:
            r = df.loc[idx]
            defects.append(make_defect(
                idx, r.get("train_number"), r.get("station_code"),
                col, "MEDIUM",
                "Unparseable time value; set to NULL.",
                raw_value=r[col],
            ))
        df[col] = df[col].apply(normalize_time)

    # 6. Drop rows missing primary keys
    missing_key_mask = df["train_number"].isna() | df["station_code"].isna()
    for idx in df.index[missing_key_mask]:
        r = df.loc[idx]
        defects.append(make_defect(
            idx, r.get("train_number"), r.get("station_code"),
            "train_number|station_code", "CRITICAL",
            "Missing primary key field; row excluded.",
        ))
    df = df.loc[~missing_key_mask].copy()

    # 7. Normalize string columns
    for col in ("station_code", "source_station_code", "destination_station_code"):
        df[col] = df[col].astype(str).str.strip().str.upper()
    for col in ("train_name", "station_name", "source_station_name", "destination_station_name"):
        df[col] = df[col].astype(str).str.strip().str.title()

    # 8. Sequence anomaly detection (sample first 500 trains to stay performant)
    seq_issues = 0
    train_nos = df["train_number"].unique()
    check_trains = train_nos[:500]
    for train_no in check_trains:
        grp = df[df["train_number"] == train_no].sort_values("sequence")
        seqs = grp["sequence"].dropna().astype(int).tolist()
        for i in range(1, len(seqs)):
            if seqs[i] <= seqs[i - 1]:
                idx = grp.index[i]
                defects.append(make_defect(
                    idx, train_no, grp.iloc[i]["station_code"],
                    "sequence", "LOW",
                    "Sequence non-monotonic: seq[{}]={} after seq[{}]={}.".format(
                        i, seqs[i], i - 1, seqs[i - 1]
                    ),
                    raw_value=seqs[i],
                ))
                seq_issues += 1
    log.info("Sequence anomalies logged: %d (from first 500 trains)", seq_issues)

    # 9. Negative distance jump detection (sample first 500 trains)
    dist_issues = 0
    for train_no in check_trains:
        grp = df[df["train_number"] == train_no].sort_values("sequence")
        dists = grp["distance_km"].tolist()
        for i in range(1, len(dists)):
            if pd.notna(dists[i]) and pd.notna(dists[i - 1]) and dists[i] < dists[i - 1]:
                idx = grp.index[i]
                defects.append(make_defect(
                    idx, train_no, grp.iloc[i]["station_code"],
                    "distance_km", "MEDIUM",
                    "Distance decreased from {} to {}.".format(dists[i - 1], dists[i]),
                    raw_value=dists[i],
                ))
                dist_issues += 1
    log.info("Distance anomalies logged: %d", dist_issues)

    # 10. Add metadata columns
    df["source"]     = "OGD_Train_details_22122017"
    df["source_url"] = SOURCE_URL
    df["day"]        = None  # Not present in raw source; NULL per constraint

    # 11. Final canonical schema
    CANONICAL_COLS = [
        "train_number", "train_name",
        "station_code", "station_name",
        "arrival_time", "departure_time",
        "day", "sequence", "distance_km",
        "source_station_code", "source_station_name",
        "destination_station_code", "destination_station_name",
        "source", "source_url",
    ]
    df = df[CANONICAL_COLS]

    log.info("Writing canonical timetable: %d rows -> %s", len(df), OUT_TIMETABLE)
    df.to_csv(OUT_TIMETABLE, index=False, encoding="utf-8")

    # 12. Corridor train extraction
    log.info("Extracting corridor trains ...")
    origin_codes = CORRIDOR_ANCHORS["origin"]
    dest_codes   = CORRIDOR_ANCHORS["destination"]
    corridor_train_nos = []

    for train_no in df["train_number"].unique():
        grp   = df[df["train_number"] == train_no]
        codes = set(grp["station_code"].str.upper().unique())
        if (codes & origin_codes) and (codes & dest_codes):
            corridor_train_nos.append(train_no)

    log.info("Corridor trains identified: %d", len(corridor_train_nos))
    corridor_df = df[df["train_number"].isin(corridor_train_nos)].copy()
    corridor_df.to_csv(OUT_CORRIDOR, index=False, encoding="utf-8")
    log.info("Corridor timetable written: %d rows", len(corridor_df))

    # 13. Section occupancy
    log.info("Computing per-section occupancy for corridor trains ...")
    occupancy_rows = []
    for train_no in corridor_train_nos:
        grp = corridor_df[corridor_df["train_number"] == train_no].sort_values("sequence").reset_index(drop=True)
        train_name = grp.iloc[0]["train_name"] if len(grp) > 0 else ""
        for i in range(len(grp) - 1):
            fr = grp.iloc[i]
            to = grp.iloc[i + 1]
            sec_dist = None
            if pd.notna(to["distance_km"]) and pd.notna(fr["distance_km"]):
                sec_dist = float(to["distance_km"]) - float(fr["distance_km"])
            occupancy_rows.append({
                "train_number":        train_no,
                "train_name":          train_name,
                "from_station_code":   fr["station_code"],
                "from_station_name":   fr["station_name"],
                "to_station_code":     to["station_code"],
                "to_station_name":     to["station_name"],
                "depart_from":         fr["departure_time"],
                "arrive_at":           to["arrival_time"],
                "from_seq":            fr["sequence"],
                "to_seq":              to["sequence"],
                "from_distance_km":    fr["distance_km"],
                "to_distance_km":      to["distance_km"],
                "section_distance_km": sec_dist,
                "source":              "derived_from_OGD_timetable",
            })

    occ_df = pd.DataFrame(occupancy_rows)
    occ_df.to_csv(OUT_OCCUPANCY, index=False, encoding="utf-8")
    log.info("Section occupancy written: %d rows -> %s", len(occ_df), OUT_OCCUPANCY)

    # 14. Write defect log
    defects_df = pd.DataFrame(defects)
    defects_df.to_csv(OUT_DEFECTS, index=False, encoding="utf-8")
    log.info("Defects logged: %d -> %s", len(defects_df), OUT_DEFECTS)

    # 15. Write profile JSON
    sev_counts = {}
    if len(defects) > 0:
        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            sev_counts[sev] = int((defects_df["severity"] == sev).sum())

    profile = {
        "generated_at":        datetime.utcnow().isoformat(),
        "source_file":         RAW_TIMETABLE,
        "raw_rows":            int(profile_raw_rows),
        "raw_columns":         int(profile_raw_cols),
        "rows_after_cleaning": int(len(df)),
        "unique_trains":       int(df["train_number"].nunique()),
        "unique_stations":     int(df["station_code"].nunique()),
        "corridor_trains":     int(len(corridor_train_nos)),
        "total_defects":       int(len(defects)),
        "defects_by_severity": sev_counts,
        "time_format":         "HH:MM:SS (24-hour, multi-day up to HH=47)",
        "corridor_anchors":    {
            "origin":      sorted(CORRIDOR_ANCHORS["origin"]),
            "destination": sorted(CORRIDOR_ANCHORS["destination"]),
        },
    }
    with open(OUT_PROFILE, "w", encoding="utf-8") as fh:
        json.dump(profile, fh, indent=2)
    log.info("Profile written: %s", OUT_PROFILE)
    log.info("=== Timetable pipeline complete ===")
    return profile


if __name__ == "__main__":
    run()
