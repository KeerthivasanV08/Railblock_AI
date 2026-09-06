# RailBlock AI — Data Source Registry & Provenance (DATA_SOURCES.md)

This document provides complete provenance and location mapping for all original raw source files, reference documents, cleaned real datasets, derived artifacts, and calibrated synthetic datasets within the **RailBlock AI** system.

---

## 1. Raw Source Files & Reference Documents

| Dataset | Original Filename | Canonical New Filename | Source | Source Type | Date / Version | Original Location | Canonical Location | Notes |
|---|---|---|---|---|---|---|---|---|
| **Passenger Train Timetable (Canonical)** | `Train_details_22122017.csv` | `railway_train_details_original.csv` | Ministry of Railways / CRIS via data.gov.in | `RAW (REAL)` | 2017-12-22 | `data/raw/` | `data/raw/timetable/ogd/` | Primary national timetable stop records (~186k rows). SHA256: `ca6b9a677212601e...` |
| **Passenger Train Timetable (Duplicate Copy)** | `Train_details_22122017 (1).csv` | `railway_train_details_original_2.csv` | Ministry of Railways / CRIS via data.gov.in | `RAW (REAL)` | 2017-12-22 | `data/raw/` | `data/raw/timetable/ogd/` | Exact duplicate copy of original timetable file (identical size and SHA256 hash). Retained for historical provenance inspection. |
| **Historical Key Railway Statistics** | `68_Railway_Key_Statistics_1950-51_to_2013-14.csv` | `railway_key_statistics_1950_51_to_2013_14.csv` | Ministry of Railways, Directorate of Statistics & Economics | `RAW (REAL)` | 1950-51 to 2013-14 | `data/raw/` | `data/raw/reference/railway_statistics/` | Broad Gauge & Meter Gauge train-km, passenger-km, and net-tonne-km time series (56 financial years). |
| **CAG Track Maintenance Compliance Audit** | `Report_No.45_of_2018_–_Compliance_Audit_on_Maintenance_of_track_on_heavy_traffic_sections_over_India.pdf` | `cag_report_45_2018_track_maintenance.pdf` | Comptroller and Auditor General of India | `RAW (REFERENCE)` | Report 45 of 2017/18 | `data/raw/` | `data/raw/reference/cag/` | Audit of track maintenance on heavy traffic sections. Contains Table 21 (block demand vs availability across zones). |
| **CAG Derailments Performance Audit** | `Report-No.-22-of-2022_Railway_English_DSC-063a2dda55f3ce6.38649271.pdf` | `cag_report_22_2022_derailments.pdf` | Comptroller and Auditor General of India | `RAW (REFERENCE)` | Report 22 of 2022 | `data/raw/` | `data/raw/reference/cag/` | Performance audit on derailments in Indian Railways. Audit of speed restrictions, maintenance deficiencies, and block shortages. |
| **Raw Maintenance Defects (TMS)** | `tms_defects.csv` | `tms_defects.csv` | RailBlock Scenario Generator (Prototype) | `RAW (SYNTHETIC)` | 2024 Initial Prototype | `data/raw/defects/` | `data/raw/defects/` | 30,000 raw simulated track defects preserved as original inputs. |
| **Raw Signal Defects (SMMS)** | `smms_defects.csv` | `smms_defects.csv` | RailBlock Scenario Generator (Prototype) | `RAW (SYNTHETIC)` | 2024 Initial Prototype | `data/raw/defects/` | `data/raw/defects/` | 25,000 raw simulated signal/interlocking defects preserved as original inputs. |
| **Raw Traction Defects (TDMS)** | `tdms_defects.csv` | `tdms_defects.csv` | RailBlock Scenario Generator (Prototype) | `RAW (SYNTHETIC)` | 2024 Initial Prototype | `data/raw/defects/` | `data/raw/defects/` | 25,000 raw simulated OHE/TRD defects preserved as original inputs. |

---

## 2. Real & Cleaned Operational Datasets

| Dataset | File Path | Source | Source Type | Temporal Scope | Description |
|---|---|---|---|---|---|
| **Commodity Freight Statistics** | `data/real/traffic/freight_statistics.csv` | Ministry of Railways Annual Statistical Statements | `REAL` | 2010-11 to 2023-24 | Official revenue commodity loading in Million Tonnes (Coal, Steel, Cement, Grains, Fertilisers, POL, Containers). |
| **Operating Statistics** | `data/real/traffic/operating_statistics.csv` | Indian Railways Year Book & Southern Railway Reviews | `REAL` | 2018-19 to 2023-24 | Operating Ratio, punctuality, wagon turnaround days, passenger/freight output. |
| **Weather Observations** | `data/real/weather/observations.csv` | India Meteorological Department (IMD) | `REAL` | 2024 (366 days) | Daily temperature, rainfall, humidity, wind, pressure, visibility across 15 corridor stations. |
| **Rainfall Records** | `data/real/weather/rainfall.csv` | India Meteorological Department (IMD) | `REAL` | 2024 | Categorized daily rainfall observations along the corridor. |
| **Weather Warnings** | `data/real/weather/warnings.csv` | IMD Regional Meteorological Centre Chennai | `REAL` | 2024 Severe Events | Warning bulletins (Cyclone Michaung / Fengal, red alerts, heatwave). |
| **Natural Events** | `data/real/weather/natural_events.csv` | Disaster Management Authority & Southern Railway Bulletins | `REAL` | 2024 Occurrences | Ground-truth extreme weather impact occurrences on railway sections. |
| **Festival Calendar** | `data/real/reference/festival_calendar.csv` | Government of Tamil Nadu Gazette & HR&CE Department | `REAL / CALIB_SYNTHETIC` | 2024 Calendar | Authentic state public holidays & major regional temple festivals (not artificially inflated). |

---

## 3. Derived Analytical Datasets

| Dataset | File Path | Source | Source Type | Description |
|---|---|---|---|---|
| **CAG Block Statistics** | `data/derived/cag/cag_block_statistics.csv` | CAG Report 45 Table 21 & Report 22 | `REAL / DERIVED` | Structured zonal shortfall hours and percentages extracted from audit tables. |
| **CAG Maintenance Calibration** | `data/derived/cag/cag_maintenance_calibration.csv` | CAG Reports 45 & 22 | `REAL / DERIVED` | Empirical benchmark parameters (minimum block hours, machine idle days, weld defect ratios). |
| **Corridor Stations** | `data/processed/network/corridor_stations.csv` | OSM + OGD Reconciled Master | `DERIVED` | Sequenced station nodes along Chennai Egmore → Thoothukudi corridor. |
| **Block Sections** | `data/processed/network/block_sections.csv` | OSM Railway Topology | `DERIVED` | 68 contiguous block sections (`SEC_001` to `SEC_068`) with line counts and permissible speeds. |
| **Train Section Occupancy** | `data/processed/timetable/train_section_occupancy.csv` | OGD Timetable + OSM Topology | `DERIVED` | 1,259 section traversal windows for corridor passenger trains. |
| **Enriched Traffic** | `data/derived/traffic/enriched_traffic.csv` | Timetable + Block Sections | `DERIVED` | Capacity utilization, train headways, and goods rake forecasts per section. |
| **Corridor Weather Features** | `data/derived/weather/corridor_weather_features.csv` | IMD Observations + Network Topology | `DERIVED` | Section-level weather metrics and risk levels. |
| **Planning Features** | `data/processed/features/planning_features.csv` | Unified Data Fusion Engine | `DERIVED` | 80,000 feature-ready un-modeled task records (strictly no ML predictions). |
| **Priority Score Inputs** | `data/processed/features/priority_score_inputs.csv` | Unified Data Fusion Engine | `DERIVED` | 80,000 normalized input matrices for future MDPS ranking. |

---

## 4. Calibrated Synthetic Datasets ($\ge$ 25,000 Rows)

| Dataset | File Path | Source Type | Rows | Description |
|---|---|---|---|---|
| **Calibrated TMS Defects** | `data/calibrated/maintenance/tms_defects.csv` | `CALIBRATED_SYNTHETIC` | 30,000 | Track maintenance defects grounded to 68 block sections with interpolated OSM coordinates. |
| **Calibrated SMMS Defects** | `data/calibrated/maintenance/smms_defects.csv` | `CALIBRATED_SYNTHETIC` | 25,000 | Signal defects with standardized internal identifiers (`RB-SIG-xxxxxx`). |
| **Calibrated TDMS Defects** | `data/calibrated/maintenance/tdms_defects.csv` | `CALIBRATED_SYNTHETIC` | 25,000 | Traction/OHE defects with standardized internal identifiers (`RB-OHE-xxxxxx`). |
| **Historical Block Records** | `data/calibrated/blocks/historical_block_records.csv` | `CALIBRATED_SYNTHETIC` | 50,000 | Block request/grant records calibrated against CAG shortfall distributions. |
| **Block Utilization** | `data/calibrated/blocks/block_utilization.csv` | `CALIBRATED_SYNTHETIC` | 25,000 | Section utilization and shadow block capacity availability. |
| **Machine Inventory** | `data/calibrated/resources/machine_inventory.csv` | `CALIBRATED_SYNTHETIC` | 25,000 | Specialized track maintenance plant deployment units (`RB-MCH-xxxxxx`). |
| **Crew Inventory** | `data/calibrated/resources/crew_inventory.csv` | `CALIBRATED_SYNTHETIC` | 25,000 | Maintenance gang shift rosters and certifications (`RB-CREW-xxxxxx`). |
| **Unified Maintenance Tasks** | `data/processed/unified/unified_maintenance_tasks.csv` | `CALIBRATED_SYNTHETIC` | 80,000 | Integrated multi-disciplinary task register across ENGINEERING, SIGNAL, and TRACTION. |

---

## 5. Purely Synthetic Simulation Datasets ($\ge$ 25,000 Rows)

| Dataset | File Path | Source Type | Rows | Description |
|---|---|---|---|---|
| **Disruption Events** | `data/synthetic/disruptions/disruption_events.csv` | `SYNTHETIC` | 25,000 | Operational disruption occurrences (`RB-DIS-xxxxxx`). |
| **Scenario Events** | `data/synthetic/scenarios/scenario_events.csv` | `SYNTHETIC` | 25,000 | Multi-hazard emergency simulation scenarios (`RB-SCN-xxxxxx`). |
| **Synthetic Operational Events** | `data/synthetic/operational/synthetic_operational_events.csv` | `SYNTHETIC` | 25,000 | Unscheduled train delays, precedences, and crossing waits (`RB-OPS-xxxxxx`). |

---

## 6. Data Integrity & Reproducibility Policy

- **No Model Training**: The data layer is prepared strictly for feature-ready consumption; no models have been trained or tuned in this phase.
- **No Fabricated Official Identifiers**: Synthetic assets use internal prefixes (`RB-SIG-`, `RB-OHE-`, `RB-MCH-`, `RB-CREW-`, `RB-DIS-`, `RB-SCN-`, `RB-OPS-`).
- **Deterministic Reproducibility**: All calibrated generation scripts use fixed pseudo-random seeds (`seed=42`).
- **Quality Gate Compliance**: All 27 verification checks of the RailBlock Quality Gate are passing.
