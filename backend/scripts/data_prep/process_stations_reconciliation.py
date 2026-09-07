"""
process_stations_reconciliation.py
===================================
RailBlock AI — Data Preprocessing Phase
Station Master & Reconciliation Pipeline (Step 3 of Implementation Plan)

Inputs:
  data/raw/Train_details_22122017.csv                                  — OGD timetable (station codes/names)
  data/raw/network/osm/chennai_thoothukudi/stations_raw.geojson        — OSM stations GeoJSON
  data/processed/timetable/corridor_trains.csv                         — Corridor train stops (from Step 2)

Outputs:
  data/processed/network/station_master.csv        — Unified station master with coordinates and source
  data/processed/network/corridor_stations.csv     — Sequenced corridor station list
  data/derived/network/station_reconciliation.csv  — OGD ↔ OSM cross-match with confidence scores
  data/defects/station_defects.csv                 — Naming mismatches, coord conflicts, unmapped codes
  data/metadata/station_profile.json               — Profile statistics

Constraints:
  - No ML/AI model training.
  - No optimization.
  - No fabrication of real railway operational data.
  - Raw source files are never modified.
"""

import os
import re
import json
import logging
import unicodedata
import pandas as pd
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────────────────────

CANONICAL_TIMETABLE = "data/raw/timetable/ogd/railway_train_details_original.csv"
FALLBACK_TIMETABLE  = "data/raw/Train_details_22122017.csv"
RAW_TIMETABLE   = CANONICAL_TIMETABLE if os.path.exists(CANONICAL_TIMETABLE) else FALLBACK_TIMETABLE
OSM_GEOJSON     = "data/raw/network/osm/chennai_thoothukudi/stations_raw.geojson"
CORRIDOR_TRAINS = "data/processed/timetable/corridor_trains.csv"

OUT_STATION_MASTER    = "data/processed/network/station_master.csv"
OUT_CORRIDOR_STATIONS = "data/processed/network/corridor_stations.csv"
OUT_RECONCILIATION    = "data/derived/network/station_reconciliation.csv"
OUT_DEFECTS           = "data/defects/station_defects.csv"
OUT_PROFILE           = "data/metadata/station_profile.json"

# Ordered corridor station codes from Chennai Egmore to Thoothukudi
# Source: publicly known IR route for 12161/12162 class trains on this corridor
CORRIDOR_SEQUENCE = [
    "MS",   # Chennai Egmore
    "TBM",  # Tambaram
    "CGL",  # Chengalpattu
    "VPT",  # Villupuram
    "VRI",  # Vridhachalam Jn
    "MLB",  # Melur / Mayiladuthurai
    "TRL",  # Tiruvarur Jn
    "TNJ",  # Thanjavur Jn
    "TPM",  # Tiruchirapalli / Trichy
    "MDU",  # Madurai Jn
    "TEN",  # Tirunelveli Jn
    "TUC",  # Thoothukudi (Tuticorin)
]

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────


def normalize_name(name: str) -> str:
    """Lowercase, strip accents, remove punctuation, collapse whitespace."""
    if not name:
        return ""
    name = str(name)
    # Normalize unicode (NFD → remove combining chars)
    name = unicodedata.normalize("NFD", name)
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    name = re.sub(r"[^a-zA-Z0-9 ]", " ", name)
    return re.sub(r"\s+", " ", name).strip().lower()


def make_defect(station_code, field, severity, description, raw_value=None):
    return {
        "station_code": station_code,
        "field":        field,
        "severity":     severity,
        "description":  description,
        "raw_value":    str(raw_value) if raw_value is not None else None,
        "detected_at":  datetime.utcnow().isoformat(),
    }


def ensure_dirs():
    for d in [
        "data/processed/network",
        "data/derived/network",
        "data/defects",
        "data/metadata",
    ]:
        os.makedirs(d, exist_ok=True)


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run():
    ensure_dirs()
    defects = []

    # ── 1. Extract OGD station records from timetable ─────────────────────────
    log.info("Loading OGD station records from timetable: %s", RAW_TIMETABLE)
    raw_tt = pd.read_csv(
        RAW_TIMETABLE,
        encoding="utf-8",
        on_bad_lines="skip",
        dtype={"Train No": str, "SEQ": str, "Distance": str},
        usecols=["Station Code", "Station Name"],
    )
    raw_tt = raw_tt.rename(columns={
        "Station Code": "station_code",
        "Station Name": "station_name",
    })
    raw_tt["station_code"] = raw_tt["station_code"].astype(str).str.strip().str.upper()
    raw_tt["station_name"] = raw_tt["station_name"].astype(str).str.strip().str.title()
    raw_tt = raw_tt.dropna(subset=["station_code"]).drop_duplicates(subset=["station_code"])
    raw_tt = raw_tt[raw_tt["station_code"] != "NAN"]
    log.info("OGD unique stations: %d", len(raw_tt))

    # ── 2. Load OSM GeoJSON ───────────────────────────────────────────────────
    log.info("Loading OSM GeoJSON: %s", OSM_GEOJSON)
    with open(OSM_GEOJSON, "r", encoding="utf-8") as fh:
        osm_gj = json.load(fh)

    osm_rows = []
    for feat in osm_gj.get("features", []):
        props = feat.get("properties", {})
        geom  = feat.get("geometry", {})
        coords = geom.get("coordinates", [None, None]) if geom else [None, None]
        lat = coords[1] if coords and len(coords) >= 2 else None
        lon = coords[0] if coords and len(coords) >= 2 else None
        osm_rows.append({
            "osm_id":        props.get("@id", ""),
            "osm_name":      props.get("name", ""),
            "osm_ref":       str(props.get("ref", "")).strip().upper() if props.get("ref") else None,
            "operator":      props.get("operator", ""),
            "network":       props.get("network", ""),
            "railway_type":  props.get("railway", ""),
            "wikidata":      props.get("wikidata", ""),
            "lat":           lat,
            "lon":           lon,
        })

    osm_df = pd.DataFrame(osm_rows)
    # Keep only Indian Railways stations (operator SR or network IR, or has ref)
    ir_mask = (
        osm_df["operator"].str.upper().isin(["SR", "SCR", "SER", "NR", "CR", "WR", "ER", "NER", "ECR", "IR"]) |
        osm_df["network"].str.upper().isin(["IR", "INDIAN RAILWAYS"]) |
        osm_df["osm_ref"].notna()
    )
    osm_df = osm_df[ir_mask].copy()
    osm_df = osm_df.dropna(subset=["osm_ref"]) if osm_df["osm_ref"].notna().any() else osm_df
    osm_df["osm_name_norm"] = osm_df["osm_name"].apply(normalize_name)
    log.info("OSM stations loaded (IR filter): %d", len(osm_df))

    # ── 3. Cross-match OGD ↔ OSM ──────────────────────────────────────────────
    # Strategy:
    #   Pass 1 — exact code match via dict lookup (O(1) per OGD station)
    #   Pass 2 — fuzzy name match for unmatched stations using vectorized pandas
    log.info("Performing OGD <-> OSM reconciliation (vectorized) ...")
    raw_tt["name_norm"] = raw_tt["station_name"].apply(normalize_name)

    # Build OSM lookup by ref code (exact)
    osm_by_ref = {row["osm_ref"]: row.to_dict() for _, row in osm_df.iterrows() if row["osm_ref"]}

    # Pre-build OSM name arrays for vectorized substring check
    osm_names_arr  = osm_df["osm_name_norm"].fillna("").tolist()
    osm_data_list  = osm_df.to_dict("records")

    def find_fuzzy_match(name_norm):
        """Return index into osm_data_list or -1 if no match."""
        if len(name_norm) < 4:
            return -1
        for i, on in enumerate(osm_names_arr):
            if len(on) < 4:
                continue
            if name_norm == on or name_norm in on or on in name_norm:
                return i
        return -1

    recon_rows = []
    # Pass 1: all exact-code matches
    exact_mask   = raw_tt["station_code"].isin(osm_by_ref)
    unmatched_df = raw_tt[~exact_mask].copy()

    for _, ogd_row in raw_tt[exact_mask].iterrows():
        code = ogd_row["station_code"]
        osm  = osm_by_ref[code]
        recon_rows.append({
            "station_code":     code,
            "ogd_name":         ogd_row["station_name"],
            "osm_name":         osm["osm_name"],
            "osm_id":           osm["osm_id"],
            "match_method":     "exact_code",
            "match_confidence": "HIGH",
            "match_status":     "MATCHED",
            "lat":              osm["lat"],
            "lon":              osm["lon"],
            "wikidata":         osm["wikidata"],
        })

    log.info("Exact-code matches: %d; fuzzy name pass for %d stations ...",
             int(exact_mask.sum()), len(unmatched_df))

    # Pass 2: fuzzy name for unmatched
    for _, ogd_row in unmatched_df.iterrows():
        code      = ogd_row["station_code"]
        name      = ogd_row["station_name"]
        name_norm = ogd_row["name_norm"]
        idx       = find_fuzzy_match(name_norm)

        if idx >= 0:
            osm_row = osm_data_list[idx]
            recon_rows.append({
                "station_code":     code,
                "ogd_name":         name,
                "osm_name":         osm_row["osm_name"],
                "osm_id":           osm_row["osm_id"],
                "match_method":     "fuzzy_name",
                "match_confidence": "MEDIUM",
                "match_status":     "MATCHED",
                "lat":              osm_row["lat"],
                "lon":              osm_row["lon"],
                "wikidata":         osm_row["wikidata"],
            })
            defects.append(make_defect(
                code, "station_name", "LOW",
                "Name matched by fuzzy substring (OGD='{}' ~ OSM='{}'); verify manually.".format(
                    name, osm_row["osm_name"]
                ),
            ))
        else:
            recon_rows.append({
                "station_code":     code,
                "ogd_name":         name,
                "osm_name":         None,
                "osm_id":           None,
                "match_method":     "none",
                "match_confidence": "NONE",
                "match_status":     "UNMATCHED",
                "lat":              None,
                "lon":              None,
                "wikidata":         None,
            })
            defects.append(make_defect(
                code, "station_code", "MEDIUM",
                "OGD station code '{}' not found in OSM dataset.".format(code),
                raw_value=code,
            ))

    recon_df = pd.DataFrame(recon_rows)
    recon_df.to_csv(OUT_RECONCILIATION, index=False, encoding="utf-8")

    matched_count   = int((recon_df["match_status"] == "MATCHED").sum())
    unmatched_count = int((recon_df["match_status"] == "UNMATCHED").sum())
    log.info("Reconciliation: %d matched, %d unmatched", matched_count, unmatched_count)

    # ── 4. Build unified station master ───────────────────────────────────────
    log.info("Building unified station master ...")
    master_rows = []
    for _, row in recon_df.iterrows():
        master_rows.append({
            "station_code":   row["station_code"],
            "station_name":   row["ogd_name"],
            "osm_name":       row["osm_name"],
            "lat":            row["lat"],
            "lon":            row["lon"],
            "wikidata":       row["wikidata"],
            "match_status":   row["match_status"],
            "match_method":   row["match_method"],
            "match_confidence": row["match_confidence"],
            "source_ogd":     "OGD_Train_details_22122017",
            "source_osm":     "OSM_chennai_thoothukudi_stations_raw.geojson"
                              if row["match_status"] == "MATCHED" else None,
        })

    master_df = pd.DataFrame(master_rows)
    master_df.to_csv(OUT_STATION_MASTER, index=False, encoding="utf-8")
    log.info("Station master written: %d rows -> %s", len(master_df), OUT_STATION_MASTER)

    # ── 5. Corridor stations: extract & sequence ─────────────────────────────
    log.info("Building corridor station list ...")

    # Load corridor trains to find all actual stop codes along the corridor
    corridor_tt = pd.read_csv(CORRIDOR_TRAINS, encoding="utf-8")
    corridor_stop_codes = set(corridor_tt["station_code"].str.upper().unique())

    # Intersect with master, then order by CORRIDOR_SEQUENCE first, then append others
    seq_dict  = {code: i for i, code in enumerate(CORRIDOR_SEQUENCE)}
    corr_rows = []
    for code in corridor_stop_codes:
        match_row = master_df[master_df["station_code"] == code]
        if match_row.empty:
            # Build stub entry
            corr_rows.append({
                "seq_index":    seq_dict.get(code, 9999),
                "station_code": code,
                "station_name": None,
                "lat":          None,
                "lon":          None,
                "match_status": "NOT_IN_MASTER",
                "is_anchor":    code in CORRIDOR_SEQUENCE,
            })
        else:
            r = match_row.iloc[0]
            corr_rows.append({
                "seq_index":    seq_dict.get(code, 9999),
                "station_code": code,
                "station_name": r["station_name"],
                "lat":          r["lat"],
                "lon":          r["lon"],
                "match_status": r["match_status"],
                "is_anchor":    code in CORRIDOR_SEQUENCE,
            })

    corr_df = pd.DataFrame(corr_rows).sort_values(["seq_index", "station_code"]).drop(columns=["seq_index"])
    corr_df.to_csv(OUT_CORRIDOR_STATIONS, index=False, encoding="utf-8")
    log.info("Corridor stations written: %d rows -> %s", len(corr_df), OUT_CORRIDOR_STATIONS)

    # ── 6. Validate coordinates ───────────────────────────────────────────────
    # Indian subcontinent bounding box: lat 6–38, lon 68–98
    for _, row in master_df.iterrows():
        if pd.notna(row["lat"]) and pd.notna(row["lon"]):
            if not (6.0 <= float(row["lat"]) <= 38.0 and 68.0 <= float(row["lon"]) <= 98.0):
                defects.append(make_defect(
                    row["station_code"], "lat/lon", "HIGH",
                    "Coordinates ({}, {}) outside Indian subcontinent bounds.".format(
                        row["lat"], row["lon"]
                    ),
                ))

    # ── 7. Write defect log ───────────────────────────────────────────────────
    defects_df = pd.DataFrame(defects)
    defects_df.to_csv(OUT_DEFECTS, index=False, encoding="utf-8")
    log.info("Station defects logged: %d -> %s", len(defects_df), OUT_DEFECTS)

    # ── 8. Write profile ─────────────────────────────────────────────────────
    sev_counts = {}
    if len(defects) > 0:
        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            sev_counts[sev] = int((defects_df["severity"] == sev).sum())

    profile = {
        "generated_at":       datetime.utcnow().isoformat(),
        "ogd_unique_stations": int(len(raw_tt)),
        "osm_ir_stations":     int(len(osm_df)),
        "matched":             matched_count,
        "unmatched":           unmatched_count,
        "match_rate_pct":      round(matched_count / max(len(raw_tt), 1) * 100, 2),
        "corridor_stops":      int(len(corr_df)),
        "total_defects":       int(len(defects)),
        "defects_by_severity": sev_counts,
        "sources": {
            "ogd":  RAW_TIMETABLE,
            "osm":  OSM_GEOJSON,
        },
    }
    with open(OUT_PROFILE, "w", encoding="utf-8") as fh:
        json.dump(profile, fh, indent=2)
    log.info("Profile written: %s", OUT_PROFILE)
    log.info("=== Station reconciliation pipeline complete ===")
    return profile


if __name__ == "__main__":
    run()
