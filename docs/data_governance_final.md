# RailBlock AI — Data Governance & Provenance Report (Final Audit)

**Date:** 2026-09-10  
**Status:** Audit Complete & Verified  

---

## 1. Dataset Inventory & Provenance Matrix

| Dataset Name | File Path | Provenance Class | Row Count / Size | SHA256 Checksum (First 16 chars) | Active Runtime Usage | Notes & Operational Limitations |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `stations` | `data/raw/network/stations.csv` | **DERIVED** | 69 stations | `372653b799ecba48` | Active | 69 stations MS $\rightarrow$ TN. Chainage derived from OSM track geometry. NOT official IR chainage. |
| `block_sections` | `data/raw/network/block_sections.csv` | **DERIVED** | 68 sections | `64ab800f7c780ffa` | Active | 68 planning sections `SEC_001`–`SEC_068`. Labeled as RailBlock Planning Sections — NOT official IR block sections. |
| `track_geometry` | `data/raw/network/track_geometry.csv` | **DERIVED** | 1416 rows | `fa3c5a0bd74eb528` | Active | OSM-derived track geometry for Chennai–Thoothukudi corridor. Coordinate accuracy varies. |
| `signal_reference` | `data/raw/network/signal_reference.csv` | **DERIVED** | 246 entries | `6f6cddef25c7370b` | Active | Synthetic signal identifiers used for planning logic demonstration. NOT official IR signal codes. |
| `ohe_mast_reference` | `data/raw/network/ohe_mast_reference.csv` | **DERIVED** | 10278 entries | `44c1c9447b46620f` | Active | Synthetic OHE mast identifiers for TRD task spatial mapping. NOT official OHE records. |
| `train_timetable` | `data/raw/traffic/train_timetable.csv` | **SYNTHETIC** | 50000 rows | `0379382f9f4fd4f4` | Active | Synthetic schedule: 500 trains $\times$ 7 days $\times$ 68 sections. **Full 68 / 68 section timetable coverage**. |
| `railway_train_details_original` | `data/raw/timetable/ogd/railway_train_details_original.csv` | **REAL** | 186124 rows | `ca6b9a677212601e` | Reference | Full national IR timetable from data.gov.in (11,113 unique trains). REAL reference source dataset. Distinct hash from train_timetable.csv. |
| `tms_defects` | `data/raw/defects/tms_defects.csv` | **SYNTHETIC** | 30000 rows | `fb9c6e11a59fca8c` | Active | Synthetic Engineering (Track) maintenance task workload. Generated for SIH prototype. NOT actual IR TMS records. |
| `smms_defects` | `data/raw/defects/smms_defects.csv` | **SYNTHETIC** | 25000 rows | `cff3a7c245b60c68` | Active | Synthetic S&T maintenance task workload. Generated for SIH prototype. NOT actual IR SMMS records. |
| `tdms_defects` | `data/raw/defects/tdms_defects.csv` | **SYNTHETIC** | 25000 rows | `112bbc2feabf1db8` | Active | Synthetic TRD maintenance task workload. Generated for SIH prototype. NOT actual IR TDMS records. |
| `cag_report_45_2018` | `data/raw/reference/cag/cag_report_45_2018_track_maintenance.pdf` | **REFERENCE** | 3.07 MB | `3f495c5725597cb5` | Reference | CAG Audit Report on Track Maintenance used for benchmark context only. NOT operational data. |
| `cag_report_22_2022` | `data/raw/reference/cag/cag_report_22_2022_derailments.pdf` | **REFERENCE** | 1.99 MB | `9483f27a0bd356f2` | Reference | CAG Audit Report on Derailments used for context/benchmarks. NOT operational data. |
| `corridor_slot_availability` | `data/raw/traffic/corridor_slot_availability.csv` | **SYNTHETIC** | 50000 rows | `1de8a80288afc2d3` | Active | Synthetic corridor block slot availability schedule derived from timetable traffic density patterns. |
| `live_train_delays` | `data/raw/traffic/live_train_delays.csv` | **SIMULATED** | 50000 rows | `28c627c92c4db675` | Active | Simulated train delay event log for disruption simulation and rescheduler testing. |
| `section_weather_sensitivity` | `data/derived/weather/section_weather_sensitivity.csv` | **DERIVED** | 68 rows | N/A | Active | Per-section weather vulnerability profile derived from terrain/coastal exposure. Layer A in SRS. |
| `live_weather_simulation` | `data/derived/weather/live_weather_simulation.csv` | **SIMULATED** | 68 rows | N/A | Active | Simulated live weather readings for 68 sections (Layer B). Provider-abstracted for future IMD integration. |
| `mdps_model` | `data/models/mdps_model.pkl` | **SYNTHETIC LABELS** | 651768 bytes | `6d213bf130f20e08` | Active | GradientBoostingRegressor trained on synthetic priority labels. $R^2=0.9756$, MAE$=2.2861$. Weather feature uplift is 0.0000 (known limitation). |
| `mdps_scaler` | `data/models/mdps_scaler.pkl` | **DERIVED** | 807 bytes | N/A | Active | Feature scaler fitted on MDPS training dataset. |
| `ppo_rescheduler_v1` | `ml/reinforcement_learning/artifacts/ppo_rescheduler_v1.pt` | **SIMULATION TRAINED** | 80359 bytes | `1af9f66acb6988d6` | Active | PPO Actor-Critic MLP trained for ~199k timesteps on RailwayDisruptionEnv. 5 actions. 12-dim state. Mean reward: 16.35. Simulation-trained. |

---

## 2. Checksum & Provenance Audit Findings

### OGD vs Active Timetable Hash Discrepancy Analysis
- **Original National OGD File**: `data/raw/timetable/ogd/railway_train_details_original.csv`  
  **SHA256**: `ca6b9a677212601e303f8ba8ea3f7639133a9ffa7f6208649cbae3140de84235` (REAL)
- **Active Runtime Timetable File**: `data/raw/traffic/train_timetable.csv`  
  **SHA256**: `0379382f9f4fd4f47f7e123ddc211e76748ffc15bf3816185c8743b7cc6edbb9` (SYNTHETIC)

**Finding**: The files have distinct hashes because `railway_train_details_original.csv` is the complete 186,124-row national timetable downloaded from data.gov.in (covering all Indian Railways zones), whereas `train_timetable.csv` is a 50,000-row synthetic dataset generated specifically for the Chennai Egmore $\rightarrow$ Thoothukudi planning corridor.

### Section Coverage Audit Findings
- All **68 planning sections (`SEC_001` to `SEC_068`)** are 100% represented in `train_timetable.csv`.
- **Classification**: Section Coverage is **VERIFIED (68/68 sections, 100% corridor coverage)**.
