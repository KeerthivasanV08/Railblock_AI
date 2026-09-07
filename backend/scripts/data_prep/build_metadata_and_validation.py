"""
build_metadata_and_validation.py
================================
Phase 7 of RailBlock AI Data Setup & Preprocessing.
Generates comprehensive metadata and machine-readable validation reports:
  - data/metadata/data_dictionary.csv
  - data/metadata/source_registry.csv
  - data/metadata/dataset_versions.csv
  - data/metadata/provenance.json
  - data/validation/validation_reports/*.json
"""

import os
import sys
import json
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.abspath("d:/Railblock_AI")
DATA_DIR = os.path.join(BASE_DIR, "data")
META_DIR = os.path.join(DATA_DIR, "metadata")
VAL_REP_DIR = os.path.join(DATA_DIR, "validation/validation_reports")

os.makedirs(META_DIR, exist_ok=True)
os.makedirs(VAL_REP_DIR, exist_ok=True)

# -------------------------------------------------------------
# 1. DATA DICTIONARY (metadata/data_dictionary.csv)
# -------------------------------------------------------------
print("Generating Central Data Dictionary...")
dict_entries = [
    # Stations
    {"dataset": "stations.csv", "column": "station_code", "description": "Unique Indian Railways station alpha code", "data_type": "string", "unit": "none", "allowed_values": "2-5 uppercase chars", "nullable": False, "source_type": "REAL"},
    {"dataset": "stations.csv", "column": "station_name", "description": "Official name of railway station", "data_type": "string", "unit": "none", "allowed_values": "any", "nullable": False, "source_type": "REAL"},
    {"dataset": "stations.csv", "column": "latitude", "description": "WGS-84 decimal latitude of station node", "data_type": "float", "unit": "degrees", "allowed_values": "8.0 to 14.0", "nullable": False, "source_type": "REAL"},
    {"dataset": "stations.csv", "column": "longitude", "description": "WGS-84 decimal longitude of station node", "data_type": "float", "unit": "degrees", "allowed_values": "77.0 to 81.0", "nullable": False, "source_type": "REAL"},
    {"dataset": "stations.csv", "column": "division", "description": "Railway administrative division", "data_type": "string", "unit": "none", "allowed_values": "MAS, TPJ, MDU", "nullable": False, "source_type": "DERIVED"},
    {"dataset": "stations.csv", "column": "chainage_km", "description": "Cumulative distance along corridor from Chennai Egmore", "data_type": "float", "unit": "km", "allowed_values": ">= 0.0", "nullable": False, "source_type": "DERIVED"},

    # Block Sections
    {"dataset": "block_sections.csv", "column": "section_id", "description": "Unique block section identifier along corridor", "data_type": "string", "unit": "none", "allowed_values": "SEC_001 to SEC_068", "nullable": False, "source_type": "DERIVED"},
    {"dataset": "block_sections.csv", "column": "from_station", "description": "Origin station code of block section", "data_type": "string", "unit": "none", "allowed_values": "valid station_code", "nullable": False, "source_type": "DERIVED"},
    {"dataset": "block_sections.csv", "column": "to_station", "description": "Destination station code of block section", "data_type": "string", "unit": "none", "allowed_values": "valid station_code", "nullable": False, "source_type": "DERIVED"},
    {"dataset": "block_sections.csv", "column": "start_km", "description": "Corridor chainage start", "data_type": "float", "unit": "km", "allowed_values": ">= 0.0", "nullable": False, "source_type": "DERIVED"},
    {"dataset": "block_sections.csv", "column": "end_km", "description": "Corridor chainage end", "data_type": "float", "unit": "km", "allowed_values": "> start_km", "nullable": False, "source_type": "DERIVED"},
    {"dataset": "block_sections.csv", "column": "num_lines", "description": "Number of running railway tracks", "data_type": "integer", "unit": "tracks", "allowed_values": "1, 2", "nullable": False, "source_type": "REAL"},
    {"dataset": "block_sections.csv", "column": "max_speed_kmph", "description": "Sectional maximum permissible speed", "data_type": "integer", "unit": "km/h", "allowed_values": "80 to 130", "nullable": False, "source_type": "REAL"},

    # Timetable
    {"dataset": "train_timetable.csv", "column": "train_number", "description": "Official 5-digit train number", "data_type": "string", "unit": "none", "allowed_values": "5 numeric digits", "nullable": False, "source_type": "REAL"},
    {"dataset": "train_timetable.csv", "column": "station_code", "description": "Station stop code", "data_type": "string", "unit": "none", "allowed_values": "valid station_code", "nullable": False, "source_type": "REAL"},
    {"dataset": "train_timetable.csv", "column": "arrival_time", "description": "Scheduled arrival time (HH:MM:SS)", "data_type": "string", "unit": "time", "allowed_values": "00:00:00 to 23:59:59", "nullable": False, "source_type": "REAL"},
    {"dataset": "train_timetable.csv", "column": "departure_time", "description": "Scheduled departure time (HH:MM:SS)", "data_type": "string", "unit": "time", "allowed_values": "00:00:00 to 23:59:59", "nullable": False, "source_type": "REAL"},
    {"dataset": "train_timetable.csv", "column": "sequence", "description": "Monotonic stop sequence number along route", "data_type": "integer", "unit": "count", "allowed_values": ">= 1", "nullable": False, "source_type": "REAL"},
    {"dataset": "train_timetable.csv", "column": "distance_km", "description": "Cumulative route distance from train origin", "data_type": "float", "unit": "km", "allowed_values": ">= 0.0", "nullable": False, "source_type": "REAL"},

    # Maintenance Defects (TMS / SMMS / TDMS / Unified)
    {"dataset": "unified_maintenance_tasks.csv", "column": "task_id", "description": "Unique maintenance task identifier", "data_type": "string", "unit": "none", "allowed_values": "alphanumeric ID", "nullable": False, "source_type": "CALIBRATED_SYNTHETIC"},
    {"dataset": "unified_maintenance_tasks.csv", "column": "date", "description": "Date defect logged (YYYY-MM-DD)", "data_type": "string", "unit": "date", "allowed_values": "valid ISO date", "nullable": False, "source_type": "CALIBRATED_SYNTHETIC"},
    {"dataset": "unified_maintenance_tasks.csv", "column": "department", "description": "Railway maintenance engineering discipline", "data_type": "string", "unit": "none", "allowed_values": "ENGINEERING, SIGNAL, TRACTION", "nullable": False, "source_type": "CALIBRATED_SYNTHETIC"},
    {"dataset": "unified_maintenance_tasks.csv", "column": "task_type", "description": "Specific defect or maintenance activity description", "data_type": "string", "unit": "none", "allowed_values": "controlled defect taxonomy", "nullable": False, "source_type": "CALIBRATED_SYNTHETIC"},
    {"dataset": "unified_maintenance_tasks.csv", "column": "section_id", "description": "Block section where defect is located", "data_type": "string", "unit": "none", "allowed_values": "SEC_001 to SEC_068", "nullable": False, "source_type": "CALIBRATED_SYNTHETIC"},
    {"dataset": "unified_maintenance_tasks.csv", "column": "latitude", "description": "WGS-84 decimal latitude of defect site", "data_type": "float", "unit": "degrees", "allowed_values": "8.0 to 14.0", "nullable": False, "source_type": "CALIBRATED_SYNTHETIC"},
    {"dataset": "unified_maintenance_tasks.csv", "column": "longitude", "description": "WGS-84 decimal longitude of defect site", "data_type": "float", "unit": "degrees", "allowed_values": "77.0 to 81.0", "nullable": False, "source_type": "CALIBRATED_SYNTHETIC"},
    {"dataset": "unified_maintenance_tasks.csv", "column": "severity", "description": "Normalized safety and operational risk severity", "data_type": "string", "unit": "none", "allowed_values": "CRITICAL, HIGH, MEDIUM, LOW", "nullable": False, "source_type": "CALIBRATED_SYNTHETIC"},
    {"dataset": "unified_maintenance_tasks.csv", "column": "priority", "description": "Scheduling urgency priority class", "data_type": "string", "unit": "none", "allowed_values": "P1_EMERGENCY, P2_URGENT, P3_NORMAL, P4_ROUTINE", "nullable": False, "source_type": "CALIBRATED_SYNTHETIC"},
    {"dataset": "unified_maintenance_tasks.csv", "column": "estimated_duration_hours", "description": "Required block window duration calibrated by CAG standards", "data_type": "float", "unit": "hours", "allowed_values": "1.0 to 6.0", "nullable": False, "source_type": "CALIBRATED_SYNTHETIC"},
    {"dataset": "unified_maintenance_tasks.csv", "column": "required_resources", "description": "Specialized maintenance plant and gang combination required", "data_type": "string", "unit": "none", "allowed_values": "machine + gang text", "nullable": False, "source_type": "CALIBRATED_SYNTHETIC"},
    {"dataset": "unified_maintenance_tasks.csv", "column": "status", "description": "Current lifecycle status of maintenance task", "data_type": "string", "unit": "none", "allowed_values": "Open, In-Progress, Deferred, Completed", "nullable": False, "source_type": "CALIBRATED_SYNTHETIC"},

    # Environmental Events
    {"dataset": "environmental_events.csv", "column": "date", "description": "Observation date (YYYY-MM-DD)", "data_type": "string", "unit": "date", "allowed_values": "valid ISO date", "nullable": False, "source_type": "REAL"},
    {"dataset": "environmental_events.csv", "column": "event_type", "description": "Meteorological event classification", "data_type": "string", "unit": "none", "allowed_values": "normal_weather, heavy_rain, extreme_heat, cyclone, flood, dense_fog, strong_wind", "nullable": False, "source_type": "DERIVED"},
    {"dataset": "environmental_events.csv", "column": "rainfall_mm", "description": "24-hour cumulative rainfall", "data_type": "float", "unit": "mm", "allowed_values": ">= 0.0", "nullable": False, "source_type": "REAL"},
    {"dataset": "environmental_events.csv", "column": "temperature_c", "description": "Ambient dry bulb temperature", "data_type": "float", "unit": "celsius", "allowed_values": "15.0 to 48.0", "nullable": False, "source_type": "REAL"},
    {"dataset": "environmental_events.csv", "column": "wind_speed", "description": "Surface wind speed", "data_type": "float", "unit": "km/h", "allowed_values": ">= 0.0", "nullable": False, "source_type": "REAL"},
    {"dataset": "environmental_events.csv", "column": "monsoon_phase", "description": "Sub-seasonal climatic phase for Tamil Nadu", "data_type": "string", "unit": "none", "allowed_values": "Northeast Monsoon, Southwest Monsoon, Summer, Winter", "nullable": False, "source_type": "REAL"},

    # Festival Calendar
    {"dataset": "festival_calendar.csv", "column": "date", "description": "Calendar date of festival or public holiday (YYYY-MM-DD)", "data_type": "string", "unit": "date", "allowed_values": "valid ISO date", "nullable": False, "source_type": "REAL"},
    {"dataset": "festival_calendar.csv", "column": "festival_name", "description": "Official name of religious or cultural event", "data_type": "string", "unit": "none", "allowed_values": "any", "nullable": False, "source_type": "REAL"},
    {"dataset": "festival_calendar.csv", "column": "tier", "description": "Festival importance hierarchy level", "data_type": "string", "unit": "none", "allowed_values": "Tier 1, Tier 2, Tier 3", "nullable": False, "source_type": "REAL"},
    {"dataset": "festival_calendar.csv", "column": "is_public_holiday", "description": "Whether date is an official Tamil Nadu Government public holiday", "data_type": "boolean", "unit": "none", "allowed_values": "True, False", "nullable": False, "source_type": "REAL"},
    {"dataset": "festival_calendar.csv", "column": "estimated_traffic_multiplier", "description": "Calibrated passenger surge factor", "data_type": "float", "unit": "multiplier", "allowed_values": "1.0 to 2.0", "nullable": False, "source_type": "CALIBRATED_SYNTHETIC"},

    # CAG Tables
    {"dataset": "cag_block_statistics.csv", "column": "shortfall_percent", "description": "Percentage deficit between requested maintenance block hours and granted hours", "data_type": "float", "unit": "percent", "allowed_values": "0.0 to 100.0", "nullable": False, "source_type": "REAL"},
    {"dataset": "cag_maintenance_calibration.csv", "column": "parameter", "description": "Empirical audit benchmark metric name", "data_type": "string", "unit": "none", "allowed_values": "any", "nullable": False, "source_type": "REAL"},
    {"dataset": "cag_maintenance_calibration.csv", "column": "value", "description": "Benchmark numerical value", "data_type": "float", "unit": "various", "allowed_values": "any", "nullable": False, "source_type": "REAL"}
]

df_dict = pd.DataFrame(dict_entries)
dict_path = os.path.join(META_DIR, "data_dictionary.csv")
df_dict.to_csv(dict_path, index=False)
print(f"Saved central data dictionary with {len(df_dict)} entries to {dict_path}")

# -------------------------------------------------------------
# 2. SOURCE REGISTRY (metadata/source_registry.csv)
# -------------------------------------------------------------
print("Generating Source Registry...")
sources = [
    {"source_id": "SRC-OSM-01", "source_name": "OpenStreetMap Railway Infrastructure", "source_type": "REAL", "dataset": "track_geometry, stations", "url": "https://www.openstreetmap.org", "organization": "OpenStreetMap Contributors", "retrieval_date": "2024-03-15", "license": "ODbL", "geographic_scope": "Chennai to Thoothukudi Corridor", "temporal_scope": "2024 Snapshot", "notes": "Extracted via Overpass API with railway tags"},
    {"source_id": "SRC-OGD-01", "source_name": "Open Government Data (OGD) Timetable", "source_type": "REAL", "dataset": "train_timetable.csv", "url": "https://data.gov.in", "organization": "Ministry of Railways, Centre for Railway Information Systems (CRIS)", "retrieval_date": "2024-03-10", "license": "Government Open Data License - India", "geographic_scope": "Pan-India National Timetable", "temporal_scope": "Dec 2017 Release", "notes": "Official passenger train timetable with ~186k stop records"},
    {"source_id": "SRC-OGD-02", "source_name": "Railway Key Statistics 1950-51 to 2013-14", "source_type": "REAL", "dataset": "railway_statistics.csv, traffic_density.csv", "url": "https://data.gov.in", "organization": "Ministry of Railways, Directorate of Statistics and Economics", "retrieval_date": "2024-03-10", "license": "Government Open Data License - India", "geographic_scope": "Pan-India National Aggregate", "temporal_scope": "1950-51 to 2013-14", "notes": "Broad Gauge and Meter Gauge density time series"},
    {"source_id": "SRC-MOR-01", "source_name": "Indian Railways Annual Statistical Statements", "source_type": "REAL", "dataset": "freight_statistics.csv, operating_statistics.csv", "url": "https://indianrailways.gov.in", "organization": "Railway Board, Ministry of Railways", "retrieval_date": "2024-03-12", "license": "Public Domain / Official Publication", "geographic_scope": "Pan-India / Southern Railway", "temporal_scope": "2010-11 to 2023-24", "notes": "Commodity loading in million tonnes and operating ratios"},
    {"source_id": "SRC-CAG-45", "source_name": "CAG Report No. 45 of 2017/2018 Track Maintenance", "source_type": "REAL", "dataset": "cag_block_statistics.csv, cag_maintenance_calibration.csv", "url": "https://cag.gov.in", "organization": "Comptroller and Auditor General of India", "retrieval_date": "2024-03-01", "license": "Public Audit Document", "geographic_scope": "Heavy Traffic Sections over Indian Railways", "temporal_scope": "2013-14 to 2016-17", "notes": "Detailed audit of maintenance blocks, machine utilization, and AT welds"},
    {"source_id": "SRC-CAG-22", "source_name": "CAG Report No. 22 of 2022 Derailments", "source_type": "REAL", "dataset": "cag_block_statistics.csv, cag_maintenance_calibration.csv", "url": "https://cag.gov.in", "organization": "Comptroller and Auditor General of India", "retrieval_date": "2024-03-01", "license": "Public Audit Document", "geographic_scope": "All Zonal Railways", "temporal_scope": "2017-18 to 2020-21", "notes": "Root causes of derailments and track maintenance backlogs"},
    {"source_id": "SRC-IMD-01", "source_name": "India Meteorological Department (IMD) Observations", "source_type": "REAL", "dataset": "observations.csv, rainfall.csv, warnings.csv", "url": "https://mausam.imd.gov.in", "organization": "India Meteorological Department, Regional Meteorological Centre Chennai", "retrieval_date": "2024-03-14", "license": "Public Climatological Data", "geographic_scope": "Tamil Nadu Corridor Stations", "temporal_scope": "2024 Calendar Year", "notes": "Daily rainfall, temperature, wind, and severe weather bulletins"},
    {"source_id": "SRC-TNG-01", "source_name": "Government of Tamil Nadu Public Holidays & HR&CE Calendar", "source_type": "REAL", "dataset": "festival_calendar.csv", "url": "https://www.tn.gov.in", "organization": "Public (Miscellaneous) Department & Hindu Religious and Charitable Endowments", "retrieval_date": "2024-03-10", "license": "Official State Gazette", "geographic_scope": "Tamil Nadu Statewide & Corridor Districts", "temporal_scope": "2024 Calendar Year", "notes": "Authentic public holidays and major regional temple festivals"},
    {"source_id": "SRC-RB-CAL-01", "source_name": "RailBlock Calibrated Operational Generator", "source_type": "CALIBRATED_SYNTHETIC", "dataset": "tms_defects, smms_defects, tdms_defects, historical_block_records, block_utilization, machine_inventory, crew_inventory", "url": "", "organization": "RailBlock AI Project", "retrieval_date": "2026-09-06", "license": "Proprietary / Project Internal", "geographic_scope": "Chennai to Thoothukudi Corridor (68 sections)", "temporal_scope": "2023-2024 Simulated Operational Windows", "notes": "Calibrated against CAG empirical audit shortfall ratios and OSM network geometry"},
    {"source_id": "SRC-RB-SYN-01", "source_name": "RailBlock Disruption & Scenario Generator", "source_type": "SYNTHETIC", "dataset": "disruption_events, scenario_events, synthetic_operational_events", "url": "", "organization": "RailBlock AI Project", "retrieval_date": "2026-09-06", "license": "Proprietary / Project Internal", "geographic_scope": "Chennai to Thoothukudi Corridor", "temporal_scope": "Simulation Scenarios", "notes": "Purely synthetic scenarios with RB- identifiers for stress-testing optimization engines"}
]

df_src = pd.DataFrame(sources)
src_path = os.path.join(META_DIR, "source_registry.csv")
df_src.to_csv(src_path, index=False)
print(f"Saved source registry to {src_path}")

# -------------------------------------------------------------
# 3. DATASET VERSIONS (metadata/dataset_versions.csv)
# -------------------------------------------------------------
print("Generating Dataset Version Registry...")
datasets_to_register = [
    ("stations.csv", "v1.1", "data/processed/network/stations.csv", "REAL/DERIVED", "Reconciled OGD & OSM coordinates"),
    ("block_sections.csv", "v1.1", "data/processed/network/block_sections.csv", "DERIVED", "68 corridor block sections with speeds & lines"),
    ("train_timetable.csv", "v1.0", "data/processed/timetable/train_timetable.csv", "REAL", "Normalized OGD timetable with HH:MM:SS format"),
    ("corridor_trains.csv", "v1.0", "data/processed/timetable/corridor_trains.csv", "REAL/DERIVED", "62 corridor trains Chennai <-> Thoothukudi"),
    ("train_section_occupancy.csv", "v1.0", "data/processed/timetable/train_section_occupancy.csv", "DERIVED", "1,259 section occupancy traversal windows"),
    ("railway_statistics.csv", "v1.0", "data/real/reference/railway_statistics.csv", "REAL", "Official 1950-2014 railway key statistics"),
    ("freight_statistics.csv", "v1.0", "data/real/traffic/freight_statistics.csv", "REAL", "Official commodity loading 2010-2024"),
    ("operating_statistics.csv", "v1.0", "data/real/traffic/operating_statistics.csv", "REAL", "Operating ratio and asset utilization"),
    ("enriched_traffic.csv", "v1.0", "data/derived/traffic/enriched_traffic.csv", "DERIVED", "Corridor section traffic density and headways"),
    ("observations.csv", "v1.0", "data/real/weather/observations.csv", "REAL", "IMD daily climatological observations"),
    ("rainfall.csv", "v1.0", "data/real/weather/rainfall.csv", "REAL", "IMD daily rainfall records"),
    ("warnings.csv", "v1.0", "data/real/weather/warnings.csv", "REAL", "Severe weather warning bulletins"),
    ("natural_events.csv", "v1.0", "data/real/weather/natural_events.csv", "REAL", "Natural extreme events log"),
    ("environmental_events.csv", "v1.0", "data/processed/weather/environmental_events.csv", "REAL/DERIVED", "Unified environmental records"),
    ("festival_calendar.csv", "v1.0", "data/real/reference/festival_calendar.csv", "REAL/CALIBRATED_SYNTHETIC", "Authentic TN festivals with traffic multipliers"),
    ("cag_block_statistics.csv", "v1.0", "data/derived/cag/cag_block_statistics.csv", "REAL", "Extracted from CAG Report 45 & 22"),
    ("cag_maintenance_calibration.csv", "v1.0", "data/derived/cag/cag_maintenance_calibration.csv", "REAL", "Extracted from CAG Report 45 & 22"),
    ("tms_defects.csv", "v2.0", "data/calibrated/maintenance/tms_defects.csv", "CALIBRATED_SYNTHETIC", "30,000 rows spatially grounded to 68 sections"),
    ("smms_defects.csv", "v2.0", "data/calibrated/maintenance/smms_defects.csv", "CALIBRATED_SYNTHETIC", "25,000 rows with RB-SIG IDs"),
    ("tdms_defects.csv", "v2.0", "data/calibrated/maintenance/tdms_defects.csv", "CALIBRATED_SYNTHETIC", "25,000 rows with RB-OHE IDs"),
    ("historical_block_records.csv", "v2.0", "data/calibrated/blocks/historical_block_records.csv", "CALIBRATED_SYNTHETIC", "50,000 rows with CAG shortfall calibration"),
    ("block_utilization.csv", "v1.0", "data/calibrated/blocks/block_utilization.csv", "CALIBRATED_SYNTHETIC", "25,000 rows of capacity & shadow blocks"),
    ("machine_inventory.csv", "v2.0", "data/calibrated/resources/machine_inventory.csv", "CALIBRATED_SYNTHETIC", "25,000 machine deployment units"),
    ("crew_inventory.csv", "v2.0", "data/calibrated/resources/crew_inventory.csv", "CALIBRATED_SYNTHETIC", "25,000 gang shift roster units"),
    ("disruption_events.csv", "v2.0", "data/synthetic/disruptions/disruption_events.csv", "SYNTHETIC", "25,000 synthetic disruption events"),
    ("scenario_events.csv", "v1.0", "data/synthetic/scenarios/scenario_events.csv", "SYNTHETIC", "25,000 multi-hazard emergency scenarios"),
    ("synthetic_operational_events.csv", "v1.0", "data/synthetic/operational/synthetic_operational_events.csv", "SYNTHETIC", "25,000 operational events"),
    ("unified_maintenance_tasks.csv", "v2.0", "data/processed/unified/unified_maintenance_tasks.csv", "CALIBRATED_SYNTHETIC", "80,000 unified maintenance tasks"),
    ("planning_features.csv", "v2.0", "data/processed/features/planning_features.csv", "DERIVED", "80,000 feature-ready un-modeled inputs"),
    ("priority_score_inputs.csv", "v1.0", "data/processed/features/priority_score_inputs.csv", "DERIVED", "80,000 raw feature inputs for future MDPS")
]

ver_records = []
now_str = "2026-09-06"

for name, ver, rel_path, stype, notes in datasets_to_register:
    full_p = os.path.join(BASE_DIR, rel_path)
    if os.path.exists(full_p):
        df_tmp = pd.read_csv(full_p, low_memory=False)
        rc = len(df_tmp)
    else:
        rc = 0
    ver_records.append({
        "dataset": name,
        "version": ver,
        "created_at": now_str,
        "source_type": stype,
        "row_count": rc,
        "processing_version": "RailBlock-Prep-v2.0",
        "relative_path": rel_path,
        "notes": notes
    })

df_vers = pd.DataFrame(ver_records)
ver_path = os.path.join(META_DIR, "dataset_versions.csv")
df_vers.to_csv(ver_path, index=False)
print(f"Saved dataset version registry ({len(df_vers)} datasets) to {ver_path}")

# -------------------------------------------------------------
# 4. PROVENANCE GRAPH (metadata/provenance.json)
# -------------------------------------------------------------
print("Generating Provenance Graph...")
prov_graph = {
    "project": "RailBlock AI",
    "corridor": "Chennai Egmore (MS) -> Thoothukudi (TN)",
    "generated_at": now_str,
    "lineage_nodes": [
        {
            "node_id": "RAW_OGD_TIMETABLE",
            "type": "REAL",
            "file": "data/raw/timetable/Train_details_22122017.csv",
            "source": "Ministry of Railways / CRIS",
            "consumers": ["data/processed/timetable/train_timetable.csv", "data/processed/timetable/corridor_trains.csv"]
        },
        {
            "node_id": "RAW_OSM_NETWORK",
            "type": "REAL",
            "file": "data/raw/network/osm/chennai_thoothukudi/tracks_raw.geojson",
            "source": "OpenStreetMap",
            "consumers": ["data/processed/network/block_sections.csv", "data/processed/network/track_geometry.csv"]
        },
        {
            "node_id": "CAG_AUDIT_REPORTS",
            "type": "REAL",
            "file": "data/raw/cag/CAG_Report_45_of_2017_Track_Maintenance.pdf",
            "source": "Comptroller and Auditor General of India",
            "consumers": ["data/derived/cag/cag_block_statistics.csv", "data/derived/cag/cag_maintenance_calibration.csv", "data/calibrated/maintenance/*"]
        },
        {
            "node_id": "CALIBRATED_MAINTENANCE_DEFECTS",
            "type": "CALIBRATED_SYNTHETIC",
            "file": "data/calibrated/maintenance/tms_defects.csv, smms_defects.csv, tdms_defects.csv",
            "calibration_source": "CAG Report 45 Table 21 & OSM 68 Block Sections",
            "consumers": ["data/processed/unified/unified_maintenance_tasks.csv", "data/processed/features/planning_features.csv"]
        },
        {
            "node_id": "WEATHER_AND_FESTIVALS",
            "type": "REAL_AND_CALIBRATED",
            "file": "data/real/weather/*, data/real/reference/festival_calendar.csv",
            "sources": ["IMD", "Government of Tamil Nadu Gazette"],
            "consumers": ["data/processed/weather/environmental_events.csv", "data/processed/features/planning_features.csv"]
        }
    ],
    "pipeline_execution_order": [
        "Phase 1: audit_existing_defects.py",
        "Phase 2: extract_cag_evidence.py",
        "Phase 3: process_environmental_and_festivals.py",
        "Phase 4: process_freight_and_traffic.py",
        "Phase 5: generate_calibrated_operational_data.py",
        "Phase 6: build_unified_feature_tables.py",
        "Phase 7: build_metadata_and_validation.py",
        "Phase 8: verify_processed_data.py"
    ]
}

prov_path = os.path.join(META_DIR, "provenance.json")
with open(prov_path, "w", encoding="utf-8") as f:
    json.dump(prov_graph, f, indent=2)
print(f"Saved provenance graph to {prov_path}")

# -------------------------------------------------------------
# 5. MACHINE-READABLE VALIDATION REPORTS (validation/validation_reports/*.json)
# -------------------------------------------------------------
print("Executing Dataset Validation Suite & Generating JSON Reports...")

def validate_dataset(name, rel_path, coord_cols=None, date_cols=None, req_cols=None, ref_checks=None):
    full_p = os.path.join(BASE_DIR, rel_path)
    if not os.path.exists(full_p):
        return {
            "dataset": name,
            "file_path": rel_path,
            "status": "ERROR",
            "error": "File not found"
        }
    
    df = pd.read_csv(full_p, low_memory=False)
    rows = len(df)
    cols = len(df.columns)
    dups = int(df.duplicated().sum())
    missing = {k: int(v) for k, v in df.isna().sum().to_dict().items() if v > 0}
    
    coord_errors = 0
    if coord_cols and all(c in df.columns for c in coord_cols):
        lat_c, lon_c = coord_cols[0], coord_cols[1]
        bad_coords = (df[lat_c] < 8.0) | (df[lat_c] > 14.5) | (df[lon_c] < 77.0) | (df[lon_c] > 81.5)
        coord_errors = int(bad_coords.sum())
        
    date_errors = 0
    if date_cols:
        for dcol in date_cols:
            if dcol in df.columns:
                p_dates = pd.to_datetime(df[dcol], errors="coerce")
                date_errors += int(p_dates.isna().sum())
                
    ref_errors = 0
    if ref_checks:
        for col_name, valid_set in ref_checks:
            if col_name in df.columns:
                invalid_refs = ~df[col_name].isin(valid_set)
                ref_errors += int(invalid_refs.sum())
                
    missing_req = []
    if req_cols:
        missing_req = [c for c in req_cols if c not in df.columns]
        
    is_valid = (dups == 0) and (coord_errors == 0) and (date_errors == 0) and (ref_errors == 0) and (len(missing_req) == 0)
    
    rep = {
        "dataset": name,
        "file_path": rel_path,
        "row_count": rows,
        "column_count": cols,
        "columns": df.columns.tolist(),
        "missing_values": missing,
        "duplicate_rows": dups,
        "invalid_rows": dups + coord_errors + date_errors + ref_errors,
        "coordinate_errors": coord_errors,
        "date_errors": date_errors,
        "referential_integrity_errors": ref_errors,
        "missing_required_columns": missing_req,
        "validation_status": "PASSED" if is_valid else "PASSED_WITH_WARNINGS" if dups == 0 and coord_errors == 0 else "FAILED"
    }
    
    out_rep = os.path.join(VAL_REP_DIR, f"{name.lower().replace('.csv', '')}_validation.json")
    with open(out_rep, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2)
    print(f"  [VALIDATION REPORT] {name:32s} -> {rep['validation_status']} ({rows} rows, {cols} cols)")
    return rep

# Reference sets
valid_sections = set(pd.read_csv(os.path.join(DATA_DIR, "processed/network/block_sections.csv"))["section_id"].unique())
valid_stations = set(pd.read_csv(os.path.join(DATA_DIR, "processed/network/stations.csv"))["station_code"].unique())

# Run validation across all datasets
val_targets = [
    ("stations_validation.json", "stations.csv", "data/processed/network/stations.csv", ["latitude", "longitude"], None, ["station_code", "station_name", "latitude", "longitude"], None),
    ("timetable_validation.json", "train_timetable.csv", "data/processed/timetable/train_timetable.csv", None, None, ["train_number", "station_code", "arrival_time", "departure_time", "sequence"], None),
    ("freight_validation.json", "freight_statistics.csv", "data/real/traffic/freight_statistics.csv", None, None, ["year", "coal_total", "total_revenue_traffic"], None),
    ("environmental_validation.json", "environmental_events.csv", "data/processed/weather/environmental_events.csv", ["latitude", "longitude"], ["date"], ["date", "event_type", "severity", "rainfall_mm", "temperature_c"], None),
    ("festival_validation.json", "festival_calendar.csv", "data/real/reference/festival_calendar.csv", None, ["date"], ["date", "festival_name", "tier", "is_public_holiday", "estimated_traffic_multiplier"], None),
    ("cag_validation.json", "cag_block_statistics.csv", "data/derived/cag/cag_block_statistics.csv", None, None, ["year", "zone", "block_demanded_hours", "block_granted_hours", "shortfall_percent"], None),
    ("tms_validation.json", "tms_defects.csv", "data/calibrated/maintenance/tms_defects.csv", ["latitude", "longitude"], ["logged_date", "target_completion_date"], ["task_id", "department", "defect_type", "section_id", "severity", "priority"], [("section_id", valid_sections)]),
    ("smms_validation.json", "smms_defects.csv", "data/calibrated/maintenance/smms_defects.csv", ["latitude", "longitude"], ["logged_date", "target_completion_date"], ["task_id", "department", "signal_id", "section_id", "severity", "priority"], [("section_id", valid_sections)]),
    ("tdms_validation.json", "tdms_defects.csv", "data/calibrated/maintenance/tdms_defects.csv", ["latitude", "longitude"], ["logged_date", "target_completion_date"], ["task_id", "department", "mast_number", "section_id", "severity", "priority"], [("section_id", valid_sections)]),
    ("blocks_validation.json", "historical_block_records.csv", "data/calibrated/blocks/historical_block_records.csv", None, None, ["record_id", "task_id", "section_id", "requested_window_minutes", "granted_window_minutes"], [("section_id", valid_sections)]),
    ("block_util_validation.json", "block_utilization.csv", "data/calibrated/blocks/block_utilization.csv", None, ["date"], ["utilization_id", "date", "section_id", "total_window_available_minutes", "capacity_utilization_rate_percent"], [("section_id", valid_sections)]),
    ("resources_validation.json", "machine_inventory.csv", "data/calibrated/resources/machine_inventory.csv", ["latitude", "longitude"], None, ["machine_id", "machine_type", "home_depot", "assigned_section_id"], [("assigned_section_id", valid_sections)]),
    ("crew_validation.json", "crew_inventory.csv", "data/calibrated/resources/crew_inventory.csv", ["latitude", "longitude"], None, ["crew_id", "department", "home_depot", "assigned_section_id", "headcount"], [("assigned_section_id", valid_sections)]),
    ("disruptions_validation.json", "disruption_events.csv", "data/synthetic/disruptions/disruption_events.csv", ["latitude", "longitude"], None, ["event_id", "event_type", "section_id", "severity"], [("section_id", valid_sections)]),
    ("scenarios_validation.json", "scenario_events.csv", "data/synthetic/scenarios/scenario_events.csv", ["latitude", "longitude"], None, ["scenario_id", "scenario_type", "primary_section_id", "urgency_level"], [("primary_section_id", valid_sections)]),
    ("operational_validation.json", "synthetic_operational_events.csv", "data/synthetic/operational/synthetic_operational_events.csv", ["latitude", "longitude"], ["event_timestamp"], ["operational_event_id", "section_id", "train_number", "delay_minutes"], [("section_id", valid_sections)]),
    ("unified_validation.json", "unified_maintenance_tasks.csv", "data/processed/unified/unified_maintenance_tasks.csv", ["latitude", "longitude"], ["date"], ["task_id", "date", "department", "task_type", "section_id", "severity", "priority", "estimated_duration_hours"], [("section_id", valid_sections)])
]

for rep_file, ds_name, p, coords, dates, reqs, refs in val_targets:
    validate_dataset(ds_name, p, coord_cols=coords, date_cols=dates, req_cols=reqs, ref_checks=refs)

print("\n--- PHASE 7: METADATA & VALIDATION SUITE COMPLETE ---")
