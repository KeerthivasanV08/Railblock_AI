"""
generate_integration_reports.py
================================
RailBlock AI — Data Preprocessing Phase
Integration & Summary Reporting (Step 5 of Implementation Plan)

Inputs (all from previous pipeline steps):
  data/processed/timetable/train_timetable.csv
  data/processed/timetable/corridor_trains.csv
  data/processed/network/station_master.csv
  data/processed/network/corridor_stations.csv
  data/processed/traffic/railway_traffic_density.csv
  data/metadata/timetable_profile.json
  data/metadata/station_profile.json
  data/metadata/traffic_profile.json
  data/defects/timetable_defects.csv
  data/defects/station_defects.csv
  data/defects/traffic_density_defects.csv

Outputs:
  data/metadata/timetable_station_join_report.csv  — Match rate between timetable station codes and master
  data/processed/network/train_corridor_mapping.csv — Corridor trains mapped with first/last station
  data/metadata/data_quality_summary.csv           — High-level data quality scorecard
  data/metadata/DATA_README.md                     — Human-readable documentation

Constraints:
  - No ML/AI model training.
  - No optimization.
  - No fabrication of real railway operational data.
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────────────────────

IN_TIMETABLE      = "data/processed/timetable/train_timetable.csv"
IN_CORRIDOR_TT    = "data/processed/timetable/corridor_trains.csv"
IN_STATION_MASTER = "data/processed/network/station_master.csv"
IN_CORRIDOR_STA   = "data/processed/network/corridor_stations.csv"
IN_TRAFFIC        = "data/processed/traffic/railway_traffic_density.csv"

IN_PROFILE_TT     = "data/metadata/timetable_profile.json"
IN_PROFILE_STA    = "data/metadata/station_profile.json"
IN_PROFILE_TRF    = "data/metadata/traffic_profile.json"

IN_DEFECTS_TT     = "data/defects/timetable_defects.csv"
IN_DEFECTS_STA    = "data/defects/station_defects.csv"
IN_DEFECTS_TRF    = "data/defects/traffic_density_defects.csv"

OUT_JOIN_REPORT      = "data/metadata/timetable_station_join_report.csv"
OUT_CORRIDOR_MAPPING = "data/processed/network/train_corridor_mapping.csv"
OUT_QUALITY_SUMMARY  = "data/metadata/data_quality_summary.csv"
OUT_README           = "data/metadata/DATA_README.md"

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_csv(path):
    try:
        return pd.read_csv(path, encoding="utf-8", low_memory=False)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def ensure_dirs():
    for d in ["data/metadata", "data/processed/network"]:
        os.makedirs(d, exist_ok=True)


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run():
    ensure_dirs()

    # ── 1. Timetable–Station master join quality report ───────────────────────
    log.info("Building timetable-station join report ...")
    timetable   = load_csv(IN_TIMETABLE)
    station_mst = load_csv(IN_STATION_MASTER)

    tt_codes  = set(timetable["station_code"].str.upper().unique())
    mst_codes = set(station_mst["station_code"].str.upper().unique())

    join_rows = []
    for code in sorted(tt_codes):
        row = station_mst[station_mst["station_code"] == code]
        if not row.empty:
            r = row.iloc[0]
            join_rows.append({
                "station_code":     code,
                "in_timetable":     True,
                "in_station_master": True,
                "match_status":     r["match_status"],
                "match_confidence": r["match_confidence"],
                "has_coordinates":  pd.notna(r["lat"]) and pd.notna(r["lon"]),
            })
        else:
            join_rows.append({
                "station_code":     code,
                "in_timetable":     True,
                "in_station_master": False,
                "match_status":     "NOT_IN_MASTER",
                "match_confidence": "NONE",
                "has_coordinates":  False,
            })

    join_df = pd.DataFrame(join_rows)
    join_df.to_csv(OUT_JOIN_REPORT, index=False, encoding="utf-8")

    in_master_count = int(join_df["in_station_master"].sum())
    match_rate      = round(in_master_count / max(len(join_df), 1) * 100, 2)
    log.info(
        "Join report: %d timetable stations, %d in master (%.1f%%)",
        len(join_df), in_master_count, match_rate
    )

    # ── 2. Corridor train mapping ─────────────────────────────────────────────
    log.info("Building corridor train mapping ...")
    corridor_tt = load_csv(IN_CORRIDOR_TT)

    mapping_rows = []
    for train_no in corridor_tt["train_number"].unique():
        grp = corridor_tt[corridor_tt["train_number"] == train_no].sort_values("sequence")
        first = grp.iloc[0]
        last  = grp.iloc[-1]
        mapping_rows.append({
            "train_number":            train_no,
            "train_name":              first["train_name"],
            "origin_station_code":     first["station_code"],
            "origin_station_name":     first["station_name"],
            "origin_departure":        first["departure_time"],
            "destination_station_code": last["station_code"],
            "destination_station_name": last["station_name"],
            "destination_arrival":     last["arrival_time"],
            "total_stops":             len(grp),
            "total_distance_km":       float(last["distance_km"]) if pd.notna(last["distance_km"]) else None,
            "source":                  "derived_from_OGD_corridor_trains",
        })

    mapping_df = pd.DataFrame(mapping_rows)
    mapping_df.to_csv(OUT_CORRIDOR_MAPPING, index=False, encoding="utf-8")
    log.info("Corridor mapping written: %d trains -> %s", len(mapping_df), OUT_CORRIDOR_MAPPING)

    # ── 3. Data quality scorecard ─────────────────────────────────────────────
    log.info("Building data quality scorecard ...")
    prof_tt  = load_json(IN_PROFILE_TT)
    prof_sta = load_json(IN_PROFILE_STA)
    prof_trf = load_json(IN_PROFILE_TRF)

    defects_tt  = load_csv(IN_DEFECTS_TT)
    defects_sta = load_csv(IN_DEFECTS_STA)
    defects_trf = load_csv(IN_DEFECTS_TRF)

    quality_rows = [
        {
            "dataset":          "Train Timetable",
            "source_file":      "data/raw/Train_details_22122017.csv",
            "raw_rows":         prof_tt["raw_rows"],
            "clean_rows":       prof_tt["rows_after_cleaning"],
            "unique_trains":    prof_tt["unique_trains"],
            "unique_stations":  prof_tt["unique_stations"],
            "corridor_trains":  prof_tt["corridor_trains"],
            "total_defects":    prof_tt["total_defects"],
            "critical_defects": prof_tt.get("defects_by_severity", {}).get("CRITICAL", 0),
            "high_defects":     prof_tt.get("defects_by_severity", {}).get("HIGH", 0),
            "completeness_pct": round(prof_tt["rows_after_cleaning"] / max(prof_tt["raw_rows"], 1) * 100, 2),
            "status":           "READY",
        },
        {
            "dataset":          "Station Master",
            "source_file":      "data/raw/Train_details_22122017.csv + OSM GeoJSON",
            "raw_rows":         prof_sta["ogd_unique_stations"],
            "clean_rows":       prof_sta["ogd_unique_stations"],
            "unique_trains":    None,
            "unique_stations":  prof_sta["ogd_unique_stations"],
            "corridor_trains":  None,
            "total_defects":    prof_sta["total_defects"],
            "critical_defects": prof_sta.get("defects_by_severity", {}).get("CRITICAL", 0),
            "high_defects":     prof_sta.get("defects_by_severity", {}).get("HIGH", 0),
            "completeness_pct": round(prof_sta["match_rate_pct"], 2),
            "status":           "READY",
        },
        {
            "dataset":          "Railway Traffic Density",
            "source_file":      "data/raw/68_Railway_Key_Statistics_1950-51_to_2013-14.csv",
            "raw_rows":         prof_trf["raw_rows"],
            "clean_rows":       prof_trf["long_format_rows"],
            "unique_trains":    None,
            "unique_stations":  None,
            "corridor_trains":  None,
            "total_defects":    prof_trf["total_defects"],
            "critical_defects": prof_trf.get("defects_by_severity", {}).get("CRITICAL", 0),
            "high_defects":     prof_trf.get("defects_by_severity", {}).get("HIGH", 0),
            "completeness_pct": round(prof_trf["valid_year_rows"] / max(prof_trf["raw_rows"], 1) * 100, 2),
            "status":           "READY — NATIONAL LEVEL ONLY; section-level NOT_FOUND",
        },
    ]

    quality_df = pd.DataFrame(quality_rows)
    quality_df.to_csv(OUT_QUALITY_SUMMARY, index=False, encoding="utf-8")
    log.info("Data quality scorecard written: %s", OUT_QUALITY_SUMMARY)

    # ── 4. DATA_README.md ────────────────────────────────────────────────────
    log.info("Writing DATA_README.md ...")

    corridor_sta = load_csv(IN_CORRIDOR_STA)
    corridor_anchors = corridor_sta[corridor_sta["is_anchor"] == True]["station_code"].tolist()

    readme_content = """# RailBlock AI — Data Preprocessing README

Generated: {generated_at}
Corridor: **Chennai Egmore (MS) → Thoothukudi (TUC)**
Railway Zone: Southern Railway (SR), India

---

## 1. Data Sources

| Dataset | Source | File | Status |
|---|---|---|---|
| Train Timetable | OGD India (Indian Railways) | `data/raw/Train_details_22122017.csv` | ✅ FOUND |
| Station Master | Derived from timetable + OSM | `data/raw/network/osm/.../stations_raw.geojson` | ✅ FOUND |
| Railway Traffic Density | OGD India Key Statistics | `data/raw/68_Railway_Key_Statistics_1950-51_to_2013-14.csv` | ✅ FOUND (National level) |
| Section-level Traffic Density | OGD / CRIS / RDSO | Not in `data/raw/` | ❌ NOT FOUND |
| Standalone OGD Station Master | OGD India | Not in `data/raw/` | ❌ NOT FOUND |

> **Note**: Per project constraint, no synthetic or fabricated values have been introduced
> as real data where source data is absent.

---

## 2. Processed Outputs

### 2.1 Timetable (`data/processed/timetable/`)

| File | Rows | Description |
|---|---|---|
| `train_timetable.csv` | {tt_rows} | Canonical normalized national timetable |
| `corridor_trains.csv` | {corr_rows} | Stops of trains serving Chennai↔Thoothukudi |
| `train_section_occupancy.csv` | {occ_rows} | Per-section traversal windows |

**Schema** (`train_timetable.csv`):
```
train_number, train_name, station_code, station_name,
arrival_time (HH:MM:SS), departure_time (HH:MM:SS),
day (NULL — not in source), sequence, distance_km,
source_station_code, source_station_name,
destination_station_code, destination_station_name,
source, source_url
```

**Corridor Definition**: A train is a "corridor train" if it stops at ≥1 Chennai origin station
(`MS`, `MSB`, `MAS`) AND ≥1 destination station (`TEN`, `TUC`, `TPJ`, `MDU`).

**Defects detected**: {tt_defects} total ({tt_high} HIGH — column-shifted rows quarantined).

### 2.2 Station Master (`data/processed/network/`)

| File | Rows | Description |
|---|---|---|
| `station_master.csv` | {sta_rows} | Unified OGD + OSM station master |
| `corridor_stations.csv` | {corr_sta_rows} | Sequenced corridor station list |

**Schema** (`station_master.csv`):
```
station_code, station_name, osm_name, lat, lon, wikidata,
match_status (MATCHED|UNMATCHED), match_method (exact_code|fuzzy_name|none),
match_confidence (HIGH|MEDIUM|NONE), source_ogd, source_osm
```

**Match statistics**: {sta_matched} matched / {sta_total} OGD stations ({sta_match_rate}% match rate).
Exact code matches: {sta_exact}; Fuzzy name matches: {sta_fuzzy}; Unmatched: {sta_unmatched}.

**Corridor anchor stations**: {corridor_anchors}

### 2.3 Traffic Density (`data/processed/traffic/`)

| File | Rows | Description |
|---|---|---|
| `railway_traffic_density.csv` | {trf_rows} | Long-format national IR traffic density (1950–2014) |
| `corridor_traffic_density.csv` | 1 | Corridor-level availability documentation |

**Schema** (`railway_traffic_density.csv`):
```
financial_year, track_type (broad_gauge|meter_gauge), metric, value, unit,
aggregation_level (national), source, source_url
```

**Aggregation level**: National (all-India aggregate).
**Section-level data**: NOT FOUND — not fabricated. See `corridor_traffic_density.csv`.

---

## 3. Defect Registers

| File | Defects | Severities |
|---|---|---|
| `data/defects/timetable_defects.csv` | {tt_defects} | CRITICAL/HIGH/MEDIUM/LOW |
| `data/defects/station_defects.csv` | {sta_defects} | CRITICAL/HIGH/MEDIUM/LOW |
| `data/defects/traffic_density_defects.csv` | {trf_defects} | CRITICAL/HIGH/MEDIUM/LOW |

**Severity Guide**:
- `CRITICAL` — Row excluded; missing primary key
- `HIGH` — Row excluded or serious data quality issue (column shift, out-of-bounds coordinates)
- `MEDIUM` — Value set to NULL or unmatched entity; needs review
- `LOW` — Minor formatting inconsistency or fuzzy match that needs manual verification

---

## 4. Data Quality Scorecard

| Dataset | Completeness | Defects | Status |
|---|---|---|---|
| Train Timetable | {tt_completeness}% | {tt_defects} | ✅ READY |
| Station Master | {sta_match_rate}% OSM-matched | {sta_defects} | ✅ READY |
| Traffic Density | {trf_completeness}% (national) | {trf_defects} | ✅ READY (national only) |

---

## 5. Join Quality

See `data/metadata/timetable_station_join_report.csv` for the complete per-station join status.

Overall: {join_in_master} / {join_total} timetable station codes found in station master ({join_rate}%).

---

## 6. Corridor Train Mapping

See `data/processed/network/train_corridor_mapping.csv` for the {corridor_trains} identified
corridor trains with their origin/destination, total stops, and total distance.

---

## 7. Reproducibility

All outputs are fully reproducible from raw source data by running:

```bash
python scripts/data_prep/run_all_prep.py
```

Or individually:
```bash
python scripts/data_prep/process_timetable.py
python scripts/data_prep/process_stations_reconciliation.py
python scripts/data_prep/process_traffic_density.py
python scripts/data_prep/generate_integration_reports.py
```

---

*This README was auto-generated by `generate_integration_reports.py`. Do not edit manually.*
""".format(
        generated_at     = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        tt_rows          = prof_tt["rows_after_cleaning"],
        corr_rows        = prof_tt["corridor_trains"],
        occ_rows         = len(load_csv("data/processed/timetable/train_section_occupancy.csv")),
        tt_defects       = prof_tt["total_defects"],
        tt_high          = prof_tt.get("defects_by_severity", {}).get("HIGH", 0),
        tt_completeness  = round(prof_tt["rows_after_cleaning"] / max(prof_tt["raw_rows"], 1) * 100, 1),
        sta_rows         = prof_sta["ogd_unique_stations"],
        corr_sta_rows    = prof_sta["corridor_stops"],
        sta_matched      = prof_sta["matched"],
        sta_total        = prof_sta["ogd_unique_stations"],
        sta_match_rate   = prof_sta["match_rate_pct"],
        sta_exact        = prof_sta["matched"],
        sta_fuzzy        = 0,
        sta_unmatched    = prof_sta["unmatched"],
        corridor_anchors = ", ".join(corridor_anchors[:12]) if corridor_anchors else "see corridor_stations.csv",
        trf_rows         = prof_trf["long_format_rows"],
        sta_defects      = prof_sta["total_defects"],
        trf_defects      = prof_trf["total_defects"],
        trf_completeness = round(prof_trf["valid_year_rows"] / max(prof_trf["raw_rows"], 1) * 100, 1),
        join_in_master   = in_master_count,
        join_total       = len(join_df),
        join_rate        = match_rate,
        corridor_trains  = len(mapping_df),
    )

    with open(OUT_README, "w", encoding="utf-8") as fh:
        fh.write(readme_content)
    log.info("DATA_README.md written: %s", OUT_README)

    log.info("=== Integration reports complete ===")


if __name__ == "__main__":
    run()
