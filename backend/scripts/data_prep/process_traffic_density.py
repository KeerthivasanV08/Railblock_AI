"""
process_traffic_density.py
===========================
RailBlock AI — Data Preprocessing Phase
Traffic Density Pipeline (Step 4 of Implementation Plan)

Inputs:
  data/raw/68_Railway_Key_Statistics_1950-51_to_2013-14.csv  — National IR traffic statistics

Outputs:
  data/processed/traffic/railway_traffic_density.csv        — Normalized annual traffic density metrics
  data/processed/traffic/corridor_traffic_density.csv       — Corridor-level density documentation
  data/defects/traffic_density_defects.csv                  — Data quality issues found
  data/metadata/traffic_profile.json                        — Profile statistics

Constraints:
  - No ML/AI model training.
  - No optimization.
  - Section-level published traffic density data is NOT FOUND in data/raw/.
    We document this absence; we do NOT fabricate section-level values.
  - Raw source file is never modified.
"""

import os
import re
import json
import logging
import pandas as pd
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────────────────────

CANONICAL_TRAFFIC = "data/raw/reference/railway_statistics/railway_key_statistics_1950_51_to_2013_14.csv"
FALLBACK_TRAFFIC  = "data/raw/68_Railway_Key_Statistics_1950-51_to_2013-14.csv"
RAW_TRAFFIC = CANONICAL_TRAFFIC if os.path.exists(CANONICAL_TRAFFIC) else FALLBACK_TRAFFIC

OUT_TRAFFIC          = "data/processed/traffic/railway_traffic_density.csv"
OUT_CORRIDOR_TRAFFIC = "data/processed/traffic/corridor_traffic_density.csv"
OUT_DEFECTS          = "data/defects/traffic_density_defects.csv"
OUT_PROFILE          = "data/metadata/traffic_profile.json"

# Column mapping from raw CSV headers to canonical schema
# Format: raw_col -> (track_type, metric, unit)
COLUMN_META = {
    "Broad Gauge - Train Kms. per Running Track Km. per Day": (
        "broad_gauge", "train_km_per_running_track_km_per_day", "train_km/running_track_km/day"
    ),
    "Broad Gauge - Passenger Kms. per Route Km. per Annum 000s": (
        "broad_gauge", "passenger_km_per_route_km_per_annum", "000s_passenger_km/route_km/year"
    ),
    "Broad Gauge - Net tonnes Kms. per Route Km. per Annum 000s": (
        "broad_gauge", "net_tonne_km_per_route_km_per_annum", "000s_net_tonne_km/route_km/year"
    ),
    "Meter Gauge - Train Kms. per Running Track Km. per Day": (
        "meter_gauge", "train_km_per_running_track_km_per_day", "train_km/running_track_km/day"
    ),
    "Meter Gauge - Passenger Kms. per Route Km. per Annum 000s": (
        "meter_gauge", "passenger_km_per_route_km_per_annum", "000s_passenger_km/route_km/year"
    ),
    "Meter Gauge - Net tonnes Kms. per Route Km. per Annum 000s": (
        "meter_gauge", "net_tonne_km_per_route_km_per_annum", "000s_net_tonne_km/route_km/year"
    ),
}

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────


def parse_numeric(val):
    """Strip commas/spaces and parse to float; return None if unparseable."""
    if pd.isna(val):
        return None
    s = re.sub(r"[,\s]", "", str(val).strip())
    try:
        return float(s)
    except ValueError:
        return None


def validate_financial_year(fy: str) -> bool:
    """Check that the year string matches 'YYYY-YY' or 'YYYY-YYYY' pattern."""
    return bool(re.match(r"^\d{4}-\d{2,4}$", str(fy).strip()))


def make_defect(financial_year, field, severity, description, raw_value=None):
    return {
        "financial_year": financial_year,
        "field":          field,
        "severity":       severity,
        "description":    description,
        "raw_value":      str(raw_value) if raw_value is not None else None,
        "detected_at":    datetime.utcnow().isoformat(),
    }


def ensure_dirs():
    for d in [
        "data/processed/traffic",
        "data/defects",
        "data/metadata",
    ]:
        os.makedirs(d, exist_ok=True)


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run():
    ensure_dirs()
    defects = []

    # ── 1. Load raw traffic statistics ───────────────────────────────────────
    log.info("Loading raw traffic statistics: %s", RAW_TRAFFIC)
    raw = pd.read_csv(
        RAW_TRAFFIC,
        encoding="utf-8",
        on_bad_lines="skip",
    )
    log.info("Raw shape: %d rows x %d cols", *raw.shape)

    profile_raw_rows = len(raw)

    # ── 2. Rename Year column if needed ──────────────────────────────────────
    raw = raw.rename(columns={"Year": "financial_year"})
    raw["financial_year"] = raw["financial_year"].astype(str).str.strip()

    # ── 3. Validate financial year format ────────────────────────────────────
    bad_fy = raw[~raw["financial_year"].apply(validate_financial_year)]
    for _, row in bad_fy.iterrows():
        defects.append(make_defect(
            row["financial_year"], "financial_year", "MEDIUM",
            "Financial year '{}' does not match expected 'YYYY-YY' format; row skipped.".format(
                row["financial_year"]
            ),
            raw_value=row["financial_year"],
        ))
    raw = raw[raw["financial_year"].apply(validate_financial_year)].copy()
    log.info("Valid financial year rows: %d", len(raw))

    # ── 4. Melt to long (tidy) format ────────────────────────────────────────
    long_rows = []
    for _, row in raw.iterrows():
        fy = row["financial_year"]
        for raw_col, (track_type, metric, unit) in COLUMN_META.items():
            if raw_col not in raw.columns:
                defects.append(make_defect(
                    fy, raw_col, "HIGH",
                    "Expected column '{}' not found in source file.".format(raw_col),
                ))
                continue
            num_val = parse_numeric(row[raw_col])
            if num_val is None and pd.notna(row[raw_col]):
                defects.append(make_defect(
                    fy, raw_col, "LOW",
                    "Non-numeric value '{}' in column '{}'; set to NULL.".format(
                        row[raw_col], raw_col
                    ),
                    raw_value=row[raw_col],
                ))
            long_rows.append({
                "financial_year":    fy,
                "track_type":        track_type,
                "metric":            metric,
                "value":             num_val,
                "unit":              unit,
                "aggregation_level": "national",
                "source":            "OGD_68_Railway_Key_Statistics_1950-51_to_2013-14",
                "source_url":        "https://data.gov.in/resource/railway-key-statistics",
            })

    density_df = pd.DataFrame(long_rows)
    density_df.to_csv(OUT_TRAFFIC, index=False, encoding="utf-8")
    log.info("Traffic density written: %d rows -> %s", len(density_df), OUT_TRAFFIC)

    # ── 5. Corridor traffic density documentation ─────────────────────────────
    # Section-level published density for Chennai→Thoothukudi is NOT FOUND in data/raw/.
    # We document this explicitly without fabricating values.
    log.info("Building corridor traffic density documentation ...")
    corridor_doc = pd.DataFrame([
        {
            "corridor":              "Chennai Egmore (MS) → Thoothukudi (TUC)",
            "railway_zone":          "Southern Railway (SR)",
            "section_level_data":    "NOT_FOUND",
            "national_proxy_available": True,
            "latest_national_year":  density_df["financial_year"].max(),
            "notes": (
                "Section-level traffic density (GTKM, GPKM, GTK) for the "
                "Chennai→Thoothukudi corridor is NOT available in data/raw/. "
                "The national railway key statistics (1950-51 to 2013-14) provide "
                "Broad Gauge aggregate density only. "
                "Per project constraint, no section-level values have been fabricated."
            ),
            "source_national": "OGD_68_Railway_Key_Statistics_1950-51_to_2013-14",
            "source_section":  "NOT_FOUND",
            "generated_at":    datetime.utcnow().isoformat(),
        }
    ])
    corridor_doc.to_csv(OUT_CORRIDOR_TRAFFIC, index=False, encoding="utf-8")
    log.info("Corridor traffic density documentation written: %s", OUT_CORRIDOR_TRAFFIC)

    # ── 6. Write defect log ───────────────────────────────────────────────────
    defects_df = pd.DataFrame(defects)
    defects_df.to_csv(OUT_DEFECTS, index=False, encoding="utf-8")
    log.info("Traffic defects logged: %d -> %s", len(defects_df), OUT_DEFECTS)

    # ── 7. Write profile ─────────────────────────────────────────────────────
    sev_counts = {}
    if len(defects) > 0:
        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            sev_counts[sev] = int((defects_df["severity"] == sev).sum())

    # Get latest BG train density value for reference
    bg_density = density_df[
        (density_df["track_type"] == "broad_gauge") &
        (density_df["metric"] == "train_km_per_running_track_km_per_day")
    ].dropna(subset=["value"])

    latest_bg_density = None
    latest_fy = None
    if len(bg_density) > 0:
        latest_row = bg_density.iloc[-1]
        latest_bg_density = float(latest_row["value"])
        latest_fy = latest_row["financial_year"]

    profile = {
        "generated_at":             datetime.utcnow().isoformat(),
        "source_file":              RAW_TRAFFIC,
        "raw_rows":                 int(profile_raw_rows),
        "valid_year_rows":          int(len(raw)),
        "long_format_rows":         int(len(density_df)),
        "financial_year_range":     [
            density_df["financial_year"].min(),
            density_df["financial_year"].max(),
        ],
        "track_types":              sorted(density_df["track_type"].unique().tolist()),
        "metrics":                  sorted(density_df["metric"].unique().tolist()),
        "aggregation_level":        "national",
        "section_level_available":  False,
        "latest_bg_train_density":  {
            "financial_year": latest_fy,
            "value":          latest_bg_density,
            "unit":           "train_km/running_track_km/day",
        },
        "total_defects":       int(len(defects)),
        "defects_by_severity": sev_counts,
    }
    with open(OUT_PROFILE, "w", encoding="utf-8") as fh:
        json.dump(profile, fh, indent=2)
    log.info("Profile written: %s", OUT_PROFILE)
    log.info("=== Traffic density pipeline complete ===")
    return profile


if __name__ == "__main__":
    run()
