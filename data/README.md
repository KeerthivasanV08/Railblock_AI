# RailBlock AI — Data Architecture

This directory houses the complete multi-tier data architecture supporting the railway maintenance block planning system for the **Chennai Egmore → Thoothukudi** corridor.

For complete provenance, source URLs, and original file mappings, see [`DATA_SOURCES.md`](DATA_SOURCES.md).

---

## Directory Organization

```text
data/
├── raw/                        # Original source data (DO NOT MODIFY)
│   ├── timetable/ogd/         # railway_train_details_original.csv (national passenger timetable)
│   ├── infrastructure/        # Raw OSM GeoJSON and network topology
│   ├── traffic/               # Freight forecasts, live delays, slot availability
│   ├── reference/
│   │   ├── railway_statistics/ # railway_key_statistics_1950_51_to_2013_14.csv
│   │   └── cag/                # CAG Reports 45 (2018) & 22 (2022) reference PDFs
│   ├── defects/               # Raw simulated defects from initial prototype
│   ├── resources/             # Raw fleet and crew rosters
│   └── calendars/             # Raw seasonal calendar
│
├── real/                       # Cleaned/normalized datasets from real public sources
│   ├── traffic/               # freight_statistics.csv, operating_statistics.csv, traffic_density.csv
│   ├── weather/               # observations.csv, rainfall.csv, warnings.csv, natural_events.csv
│   └── reference/             # festival_calendar.csv, railway_statistics.csv
│
├── derived/                    # Reconciled, aggregated, or empirically derived data
│   ├── network/               # stations.csv, block_sections.csv, track_geometry.csv
│   ├── traffic/               # enriched_traffic.csv (headways, capacities, density)
│   ├── weather/               # corridor_weather_features.csv
│   └── cag/                   # cag_block_statistics.csv, cag_maintenance_calibration.csv
│
├── calibrated/                 # Calibrated operational simulation datasets (>= 25,000 rows)
│   ├── maintenance/           # tms_defects.csv (30k), smms_defects.csv (25k), tdms_defects.csv (25k)
│   ├── blocks/                # historical_block_records.csv (50k), block_utilization.csv (25k)
│   └── resources/             # machine_inventory.csv (25k), crew_inventory.csv (25k)
│
├── synthetic/                  # Purely synthetic simulation datasets (>= 25,000 rows)
│   ├── disruptions/           # disruption_events.csv (25k, RB-DIS-xxxxxx)
│   ├── scenarios/             # scenario_events.csv (25k, RB-SCN-xxxxxx)
│   └── operational/           # synthetic_operational_events.csv (25k, RB-OPS-xxxxxx)
│
├── processed/                  # Final feature-ready tables prepared for downstream services
│   ├── network/               # Reconciled corridor network masters
│   ├── timetable/             # Train timetable, corridor trains, section occupancy
│   ├── weather/               # environmental_events.csv
│   ├── unified/               # unified_maintenance_tasks.csv (80,000 multi-disciplinary tasks)
│   └── features/              # planning_features.csv (80k), priority_score_inputs.csv (80k)
│
├── metadata/                   # Central data dictionaries, registries, and schemas
│   ├── data_dictionary.csv    # 45 column definitions with data types and allowed domains
│   ├── source_registry.csv    # Source organizations, retrieval dates, and licenses
│   ├── dataset_versions.csv   # Version tracking across all 30 active datasets
│   └── provenance.json        # Machine-readable end-to-end data lineage graph
│
├── validation/                 # Automated quality reports
│   └── validation_reports/    # 17 machine-readable JSON validation reports
│
└── defects/                    # Quality defect registers (anomalies logged during cleaning)
    ├── station_defects.csv
    ├── timetable_defects.csv
    └── traffic_density_defects.csv
```

---

## Provenance Policy & Source Classifications

1. **`REAL`**: Original open government data (OGD, CRIS, IMD, Ministry of Railways, Tamil Nadu Gazette, CAG).
2. **`DERIVED`**: Spatial joins, network linear referencing, section traversal occupancy windows, and audit statistical extractions.
3. **`CALIBRATED_SYNTHETIC`**: Operational datasets calibrated against CAG empirical shortfall percentages and grounded to real OpenStreetMap corridor block sections.
4. **`SYNTHETIC`**: Simulation stress-test scenarios using explicit internal identifiers (`RB-DIS-`, `RB-SCN-`, `RB-OPS-`).

---

## Quality Gate & Constraints

- **Mandatory 25k Rows**: Every generated operational dataset contains $\ge 25,000$ rows with domain variation.
- **Festival Calendar Exception**: Authentic event dates only (26 days across the calendar year); strictly avoiding artificial duplication.
- **No Model Training**: The data layer is prepared strictly for feature-ready consumption; no models have been trained or tuned.
