# RailBlock AI — Data Directory

CSV-first data architecture supporting the railway maintenance block planning system.

## Directory Structure

```
data/
├── raw/                        # Source data (DO NOT MODIFY)
│   ├── network/               # Track geometry, stations, sections, masts, signals
│   ├── defects/               # TMS, SMMS, TDMS defect datasets
│   ├── traffic/               # Train timetable, live delays, freight forecasts
│   ├── resources/             # Machine and crew inventory
│   ├── historical/            # Historical block records and training labels
│   ├── disruptions/           # Disruption event logs
│   └── calendars/             # Seasonal and festival calendars
│
├── synthetic/                  # Generated synthetic data for testing
│   ├── infrastructure/        # Track geometry variations
│   ├── maintenance/           # Synthetic defect scenarios
│   ├── operations/            # Train movement simulations
│   ├── resources/             # Resource allocation scenarios
│   ├── blocks/                # Synthetic block windows
│   └── disruptions/           # Disruption event scenarios
│
├── processed/                  # Pipeline outputs (auto-generated)
│   ├── unified_maintenance_tasks.csv    (from ingestion)
│   ├── spatially_mapped_tasks.csv       (from linear referencing)
│   ├── scored_tasks.csv                 (from MDPS engine)
│   ├── clustered_tasks.csv             (from shadow block engine)
│   ├── feasibility_checked_tasks.csv    (from constraint engine)
│   ├── spatial/               # Spatial join outputs
│   ├── maintenance/           # Cleaned maintenance records
│   ├── operations/            # Traffic enrichment outputs
│   └── resources/             # Resource availability views
│
├── features/                   # ML feature matrices
│   ├── mdps_features/         # MDPS training features
│   └── rl_features/           # RL environment features (future)
│
├── outputs/                    # Final plan outputs
│   ├── weekly_block_plan.csv          (planning service output)
│   ├── monthly_rolling_block_plan.csv  (planning service output)
│   ├── audit_log.csv                  (append-only audit trail)
│   ├── schedules/             # Archived weekly/monthly plans
│   ├── scores/                # Archived scoring runs
│   ├── simulations/           # Disruption & optimization results
│   └── reports/               # KPI and analytics reports
│
├── models/                     # ML artifacts (legacy + backward compat)
│   └── [see backend/app/ml/models/]
│
├── generators/                 # Data generation scripts
└── schemas/                    # JSON Schema definitions
```

## Data Provenance

All CSV files use UTF-8 encoding. Each file includes a `source` column where applicable,
tracking whether the record originated from `"csv"` (synthetic/generated) or a source system.

## Model Artifacts

Runtime model artifacts are served from `backend/app/ml/models/`.
The `data/models/` directory is maintained for backward compatibility with training scripts.
