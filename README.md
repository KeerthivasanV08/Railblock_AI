# RailBlock AI — Synthetic Dataset Generation & Preprocessing System

An AI-powered automatic block-planning system for Indian Railways. This module generates a large, internally consistent, geographically coherent, statistically realistic synthetic dataset and runs the complete preprocessing pipeline.

---

## 1. Quick Start

### Prerequisites
Python 3.11+ with `pandas`, `numpy`, `scikit-learn`, `scipy`, `joblib`, `faker`, `geopy`, `shapely`, `networkx`, `pydantic`, `pytest`.

### Execution Commands

```bash
# 1. Generate all synthetic raw datasets (12 stages)
python data/generators/generate_all.py

# 2. Run complete data cleaning, spatial translation, ML scoring & feasibility pipeline
python preprocessing/run_pipeline.py

# 3. Run automated test suite
pytest
```

---

## 2. System Architecture

```text
generate_all.py                   Network
                                  References
                                  TMS
                                  SMMS
                                  TDMS
                                  Timetable
                                  Delays
                                  Freight
                                  Slots
                                  Resources
                                  Historical Blocks
                                  MDPS Labels
                                  Disruptions
                                  Calendars
                                      │
                                      ▼
                             RAW DATA VALIDATION
                                      │
                                      ▼
                               run_pipeline.py
                                      │
                                      ├─► Cleaning & Normalization
                                      ├─► Task Unification
                                      ├─► Spatial Translation (Linear Referencing Engine)
                                      ├─► Traffic & Resource Enrichment
                                      ├─► MDPS Criticality Scoring (Gradient Boosting Model)
                                      ├─► Shadow-Block & Mega-Block Clustering
                                      ├─► Tripartite Constraint Feasibility Analysis
                                      └─► Master Planning Features Assembly
                                      │
                                      ▼
                               PROCESSED DATA & MODELS
                                      │
                                      ▼
                             FUTURE AI/OPTIMIZATION
                               (Weekly Plan, RBP, Rescheduler)
```

---

## 3. High-Volume Datasets Generated

| File Name | Location | Minimum Required Rows | Actual Generated Rows |
| :--- | :--- | :--- | :--- |
| `tms_defects.csv` | `data/raw/defects/` | 30,000 | 30,000 |
| `smms_defects.csv` | `data/raw/defects/` | 25,000 | 25,000 |
| `tdms_defects.csv` | `data/raw/defects/` | 25,000 | 25,000 |
| `train_timetable.csv` | `data/raw/traffic/` | 50,000 | 50,000 |
| `live_train_delays.csv` | `data/raw/traffic/` | 50,000 | 50,000 |
| `goods_forecast.csv` | `data/raw/traffic/` | 30,000 | 30,000 |
| `corridor_slot_availability.csv` | `data/raw/traffic/` | 50,000 | 50,000 |
| `historical_block_records.csv` | `data/raw/historical/` | 50,000 | 50,000 |
| `mdps_training_labels.csv` | `data/raw/historical/` | 30,000 | 30,000 |
| `disruption_events.csv` | `data/raw/disruptions/` | 25,000 | 25,000 |
| **Total Unified Maintenance Tasks** | `data/processed/` | **80,000** | **80,000** |

---

## 4. Key Components

1. **Universal Geo-Spatial Linear Referencing Engine** (`preprocessing/spatial_mapping.py`):
   Translates departmental location formats (`CHAINAGE` for TMS, `SIGNAL` for SMMS, `MAST` for TDMS) into common WGS84 GPS latitude/longitude and linear chainage km.

2. **MDPS Criticality Scorer** (`preprocessing/mdps_dataset.py`):
   Trains a `GradientBoostingRegressor` model on 30,000 label records to calculate task criticality scores (0-100), priority ranks, and priority bands (`Critical`, `High`, `Medium`, `Low`).

3. **Shadow-Block & Mega-Block Clustering** (`preprocessing/clustering.py`):
   Detects spatial overlap across Engineering, S&T, and TRD tasks on common block sections to form integrated multi-department maintenance blocks.

4. **Tripartite Constraint Feasibility Engine** (`preprocessing/feasibility.py`):
   Matches traffic timetable gaps, heavy machine availability/positioning distance, and crew shift availability to evaluate operational block feasibility.
