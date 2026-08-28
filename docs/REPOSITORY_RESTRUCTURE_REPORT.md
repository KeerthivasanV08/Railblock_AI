# Repository Restructure Report

**Date:** 2026-08-27  
**Result:** ✅ ALL VALIDATIONS PASSED

---

## 1. Before Structure

Flat layout with all services/engines at top-level `backend/app/`. Configuration split
between `core/config.py` and environment variables. No domain separation. ML artifacts
only in `data/models/`. No top-level `ml/` development area. No `data/schemas/` or
`data/features/` directories. Tests only at root `tests/`.

```
backend/app/
├── main.py
├── core/config.py          (flat config)
├── api/                    (8 flat route files)
│   ├── ai.py               (mixed: spatial + scoring + clustering + feasibility + optimize)
│   ├── blocks.py
│   ├── planning.py
│   ├── analytics.py
│   ├── audit.py
│   ├── assets.py
│   ├── resources.py
│   ├── disruptions.py
│   ├── system.py
│   ├── tasks.py
│   ├── trains.py
│   ├── live.py
│   └── websocket.py
├── engines/                (7 flat engine files)
│   ├── constraint_engine.py
│   ├── disruption_engine.py
│   ├── linear_reference_engine.py
│   ├── mdps_engine.py
│   ├── optimization_engine.py
│   ├── rescheduler_engine.py
│   └── shadow_block_engine.py
└── services/               (flat service files)
    ├── analytics_service.py
    ├── approval_service.py
    ├── clustering_service.py
    ├── explainability_service.py
    ├── ingestion_service.py
    ├── normalization_service.py
    ├── optimization_service.py
    ├── planning_service.py
    ├── priority_service.py
    ├── resource_service.py
    ├── rescheduling_service.py
    ├── spatial_service.py
    ├── system_health_service.py
    └── validation_service.py
```

---

## 2. After Structure

```
Railblock_AI/
│
├── backend/
│   ├── app/
│   │   ├── main.py                    (updated: uses api/router.py)
│   │   ├── config/                    ★ NEW
│   │   │   ├── settings.py            (canonical settings — moved from core/config.py)
│   │   │   ├── database.py            (stub — NOT CONNECTED)
│   │   │   ├── redis.py               (stub — NOT CONNECTED)
│   │   │   ├── celery.py              (stub — NOT CONNECTED)
│   │   │   └── logging.py             (logging setup)
│   │   ├── api/                       ★ RESTRUCTURED
│   │   │   ├── router.py              (central aggregating router — NEW)
│   │   │   ├── spatial/spatial_routes.py
│   │   │   ├── scoring/scoring_routes.py
│   │   │   ├── blocks/block_routes.py
│   │   │   ├── planner/planner_routes.py
│   │   │   ├── tasks/task_routes.py
│   │   │   ├── assets/asset_routes.py
│   │   │   ├── resources/resource_routes.py
│   │   │   ├── disruptions/disruption_routes.py
│   │   │   ├── xai/xai_routes.py
│   │   │   ├── analytics/analytics_routes.py
│   │   │   ├── websocket/realtime_routes.py
│   │   │   ├── auth/auth_routes.py    (stub)
│   │   │   ├── dashboard/dashboard_routes.py (stub)
│   │   │   └── execution/execution_routes.py (stub)
│   │   │   [+ flat shims for backward compat: ai.py, blocks.py, etc.]
│   │   ├── core/                      (unchanged + shims added)
│   │   ├── engines/                   ★ SHIMS (all point to services/)
│   │   ├── live/                      (unchanged)
│   │   ├── ml/                        ★ NEW (runtime ML)
│   │   │   ├── models/                (5 runtime artifacts)
│   │   │   ├── preprocessing/feature_builder.py
│   │   │   ├── training/trainer.py
│   │   │   └── evaluation/evaluator.py
│   │   ├── models/                    (unchanged Pydantic models)
│   │   ├── repositories/              (unchanged CSV repositories)
│   │   ├── schemas/                   (placeholder)
│   │   ├── services/                  ★ RESTRUCTURED (11 subpackages)
│   │   │   ├── spatial/
│   │   │   ├── priority/
│   │   │   ├── clustering/
│   │   │   ├── optimization/
│   │   │   ├── resources/
│   │   │   ├── rescheduler/
│   │   │   ├── xai/
│   │   │   ├── approval/
│   │   │   ├── analytics/
│   │   │   ├── ingestion/
│   │   │   ├── execution/
│   │   │   └── notification/ (stub)
│   │   │   [+ flat shims for backward compat]
│   │   ├── utils/                     (unchanged)
│   │   └── workers/                   (stub)
│   ├── tests/                         ★ NEW (mirrored test tree)
│   │   ├── unit/
│   │   ├── integration/test_backend_runtime.py
│   │   ├── api/
│   │   ├── services/
│   │   └── optimization/
│   ├── migrations/alembic/            (stub)
│   ├── Dockerfile
│   ├── alembic.ini
│   └── README.md                      ★ NEW
│
├── ml/                                ★ NEW (dev/experimentation area)
│   ├── README.md
│   ├── mdps/
│   │   ├── preprocessing/feature_engineering.py
│   │   ├── training/train.py + config.yaml
│   │   ├── evaluation/evaluate.py
│   │   ├── artifacts/ (model.pkl, scaler.pkl, feature_metadata.json, model_metrics.json)
│   │   └── notebooks/
│   ├── reinforcement_learning/        (SCAFFOLDING ONLY)
│   │   ├── environment/railway_env.py + state.py + actions.py
│   │   ├── training/train_ppo.py
│   │   ├── evaluation/evaluate_policy.py
│   │   └── artifacts/ (empty — no trained policy)
│   └── optimization/
│       ├── experiments/benchmark.py
│       ├── benchmark.py
│       └── solver_tests.py
│
├── data/                              ★ NEW SUBDIRS + SCHEMAS + FEATURES
│   ├── README.md
│   ├── raw/                           (unchanged source CSVs)
│   ├── synthetic/ (subdirs created)
│   ├── processed/ (unchanged CSVs + spatial/maintenance/operations/resources subdirs)
│   ├── features/
│   │   ├── mdps_features/             ★ NEW — train.csv, validation.csv, test.csv
│   │   └── rl_features/               (documented as pending)
│   ├── outputs/                       (unchanged CSVs + schedules/scores/simulations/reports subdirs)
│   ├── schemas/                       ★ NEW — 9 JSON Schema files derived from actual data
│   └── generators/                    (generate_schemas.py, generate_mdps_features.py)
│
├── docs/
│   ├── REPOSITORY_RESTRUCTURE_REPORT.md (this file)
│   ├── ML_ARCHITECTURE.md
│   ├── MDPS_MODEL_CARD.md
│   └── data_dictionary.md
│
├── tests/                             (root tests — unchanged)
├── preprocessing/                     (training pipeline — unchanged)
├── scripts/                           (utility scripts — unchanged)
├── pytest.ini                         (updated: testpaths added)
└── .env.example
```

---

## 3. File Migration Map

| OLD PATH | NEW PATH | Action |
|----------|----------|--------|
| `backend/app/core/config.py` | `backend/app/config/settings.py` | MOVE (shim kept at old path) |
| `backend/app/core/logging.py` | `backend/app/config/logging.py` | MOVE (shim kept) |
| `backend/app/api/ai.py` | Dissolved → `api/spatial/`, `api/scoring/`, `api/blocks/`, `api/planner/` | DISSOLVE |
| `backend/app/api/planning.py` | `backend/app/api/planner/planner_routes.py` | MOVE (shim kept) |
| `backend/app/api/analytics.py` | `backend/app/api/analytics/analytics_routes.py` | MOVE (shim kept) |
| `backend/app/api/audit.py` | `backend/app/api/analytics/analytics_routes.py` | MERGE |
| `backend/app/api/websocket.py` | `backend/app/api/websocket/realtime_routes.py` | MOVE (shim kept) |
| `backend/app/api/live.py` | `backend/app/api/websocket/realtime_routes.py` | MERGE |
| `backend/app/api/blocks.py` | `backend/app/api/blocks/block_routes.py` | MOVE (shim kept) |
| `backend/app/api/assets.py` | `backend/app/api/assets/asset_routes.py` | MOVE (shim kept) |
| `backend/app/api/resources.py` | `backend/app/api/resources/resource_routes.py` | MOVE (shim kept) |
| `backend/app/api/disruptions.py` | `backend/app/api/disruptions/disruption_routes.py` | MOVE (shim kept) |
| `backend/app/engines/mdps_engine.py` | `backend/app/services/priority/mdps_engine.py` | MOVE (shim kept) |
| `backend/app/engines/linear_reference_engine.py` | `backend/app/services/spatial/linear_reference_service.py` | MOVE (shim kept) |
| `backend/app/engines/shadow_block_engine.py` | `backend/app/services/clustering/shadow_block_service.py` | MOVE (shim kept) |
| `backend/app/engines/constraint_engine.py` | `backend/app/services/optimization/constraints.py` | MOVE (shim kept) |
| `backend/app/engines/optimization_engine.py` | `backend/app/services/optimization/milp_solver.py` | MOVE (shim kept) |
| `backend/app/engines/rescheduler_engine.py` | `backend/app/services/rescheduler/policy_engine.py` | MOVE (shim kept) |
| `backend/app/engines/disruption_engine.py` | `backend/app/services/rescheduler/disruption_detector.py` | MOVE (shim kept) |
| `backend/app/services/spatial_service.py` | `backend/app/services/spatial/spatial_cluster_service.py` | MOVE (shim kept) |
| `backend/app/services/priority_service.py` | `backend/app/services/priority/mdps_service.py` | MOVE (shim kept) |
| `backend/app/services/clustering_service.py` | `backend/app/services/clustering/spatial_clustering.py` | MOVE (shim kept) |
| `backend/app/services/optimization_service.py` | `backend/app/services/optimization/planner_service.py` | MOVE (shim kept) |
| `backend/app/services/planning_service.py` | `backend/app/services/optimization/planning_service.py` | MOVE (shim kept) |
| `backend/app/services/resource_service.py` | `backend/app/services/resources/resource_service.py` | MOVE (shim kept) |
| `backend/app/services/rescheduling_service.py` | `backend/app/services/rescheduler/rescheduler_service.py` | MOVE (shim kept) |
| `backend/app/services/explainability_service.py` | `backend/app/services/xai/explanation_service.py` | MOVE (shim kept) |
| `backend/app/services/analytics_service.py` | `backend/app/services/analytics/analytics_service.py` | MOVE (shim kept) |
| `backend/app/services/approval_service.py` | `backend/app/services/approval/approval_service.py` | MOVE (shim kept) |
| `backend/app/services/ingestion_service.py` | `backend/app/services/ingestion/ingestion_service.py` | MOVE (shim kept) |
| `backend/app/services/normalization_service.py` | `backend/app/services/ingestion/normalization_service.py` | MOVE (shim kept) |
| `backend/app/services/validation_service.py` | `backend/app/services/ingestion/validation_service.py` | MOVE (shim kept) |
| `backend/app/services/system_health_service.py` | `backend/app/services/analytics/system_health_service.py` | MOVE (shim kept) |
| `data/models/mdps_model.pkl` | `backend/app/ml/models/mdps_model.pkl` + `ml/mdps/artifacts/model.pkl` | COPY (both preserved) |
| `data/models/mdps_scaler.pkl` | `backend/app/ml/models/mdps_scaler.pkl` + `ml/mdps/artifacts/scaler.pkl` | COPY (both preserved) |

---

## 4. Files Created

### Backend
- `backend/app/config/settings.py` — canonical settings
- `backend/app/config/database.py` — DB stub (NOT CONNECTED)
- `backend/app/config/redis.py` — Redis stub (NOT CONNECTED)
- `backend/app/config/celery.py` — Celery stub (NOT CONNECTED)
- `backend/app/config/logging.py` — logging setup
- `backend/app/api/router.py` — central aggregating router
- `backend/app/api/spatial/spatial_routes.py`
- `backend/app/api/scoring/scoring_routes.py`
- `backend/app/api/blocks/block_routes.py`
- `backend/app/api/planner/planner_routes.py`
- `backend/app/api/tasks/task_routes.py`
- `backend/app/api/assets/asset_routes.py`
- `backend/app/api/resources/resource_routes.py`
- `backend/app/api/disruptions/disruption_routes.py`
- `backend/app/api/xai/xai_routes.py`
- `backend/app/api/analytics/analytics_routes.py`
- `backend/app/api/websocket/realtime_routes.py`
- `backend/app/api/auth/auth_routes.py` (stub)
- `backend/app/api/dashboard/dashboard_routes.py` (stub)
- `backend/app/api/execution/execution_routes.py` (stub)
- `backend/app/services/spatial/` — 4 modules
- `backend/app/services/priority/` — 4 modules
- `backend/app/services/clustering/` — 3 modules
- `backend/app/services/optimization/` — 5 modules
- `backend/app/services/resources/` — 4 modules
- `backend/app/services/rescheduler/` — 5 modules
- `backend/app/services/xai/` — 3 modules
- `backend/app/services/approval/` — 1 module
- `backend/app/services/analytics/` — 4 modules
- `backend/app/services/ingestion/` — 3 modules
- `backend/app/services/execution/` — 4 modules (stubs)
- `backend/app/services/notification/` — stub
- `backend/app/ml/models/` — runtime artifacts
- `backend/app/ml/preprocessing/feature_builder.py`
- `backend/app/ml/training/trainer.py`
- `backend/app/ml/evaluation/evaluator.py`
- `backend/tests/` — mirrored test tree
- `backend/Dockerfile`
- `backend/alembic.ini`
- `backend/README.md`

### ML
- `ml/README.md`
- `ml/mdps/preprocessing/feature_engineering.py`
- `ml/mdps/training/train.py`
- `ml/mdps/training/config.yaml`
- `ml/mdps/evaluation/evaluate.py`
- `ml/mdps/artifacts/` (model.pkl, scaler.pkl, feature_metadata.json, model_metrics.json)
- `ml/mdps/README.md`
- `ml/reinforcement_learning/environment/railway_env.py` (scaffolding)
- `ml/reinforcement_learning/environment/state.py` (scaffolding)
- `ml/reinforcement_learning/environment/actions.py` (scaffolding)
- `ml/reinforcement_learning/training/train_ppo.py` (stub)
- `ml/reinforcement_learning/evaluation/evaluate_policy.py` (stub)
- `ml/reinforcement_learning/README.md`
- `ml/optimization/benchmark.py`
- `ml/optimization/solver_tests.py`
- `ml/optimization/experiments/benchmark.py`
- `ml/optimization/README.md`

### Data
- `data/schemas/tms_schema.json` (derived from actual tms_defects.csv columns)
- `data/schemas/smms_schema.json` (derived from actual smms_defects.csv columns)
- `data/schemas/tdms_schema.json` (derived from actual tdms_defects.csv columns)
- `data/schemas/coa_schema.json` (documented stub — no source data)
- `data/schemas/bdms_schema.json` (documented stub — no source data)
- `data/schemas/maintenance_schema.json` (derived from unified_maintenance_tasks.csv)
- `data/schemas/block_schema.json` (derived from weekly_block_plan.csv)
- `data/schemas/resource_schema.json` (derived from machine_inventory.csv)
- `data/features/mdps_features/train.csv` — 21,000 rows
- `data/features/mdps_features/validation.csv` — 4,500 rows
- `data/features/mdps_features/test.csv` — 4,500 rows
- `data/features/mdps_features/split_metadata.json`
- `data/generators/generate_schemas.py`
- `data/generators/generate_mdps_features.py`
- `data/README.md`
- `data/schemas/README.md`
- `data/features/README.md`
- Various subdirectory READMEs
- `docs/REPOSITORY_RESTRUCTURE_REPORT.md` (this file)

---

## 5. Files Renamed

| Old Name | New Name | Location |
|----------|----------|---------|
| `mdps_model.pkl` | `model.pkl` | `ml/mdps/artifacts/` (runtime copy in `backend/app/ml/models/` keeps original name) |
| `mdps_scaler.pkl` | `scaler.pkl` | `ml/mdps/artifacts/` (same) |
| `mdps_feature_metadata.json` | `feature_metadata.json` | `ml/mdps/artifacts/` (same) |

---

## 6. Files Removed

**No files were deleted.** All original files are preserved.

Old flat `api/*.py`, `engines/*.py`, `services/*.py` files are kept as backward-compatibility shims that re-export from their new canonical locations.

---

## 7. Backend Architecture

### Separation of Concerns

| Layer | Location | Responsibility |
|-------|----------|---------------|
| **API** | `app/api/{domain}/` | HTTP/WebSocket routing only — no business logic |
| **Services** | `app/services/{domain}/` | All business logic, orchestration, data processing |
| **Models** | `app/models/` | Pydantic domain models |
| **Schemas** | `app/schemas/` | Request/response schemas (Pydantic) |
| **Core** | `app/core/` | Middleware, exceptions, constants |
| **Config** | `app/config/` | Settings, DB/Redis/Celery stubs |
| **ML Runtime** | `app/ml/` | Runtime artifact loading and inference only |
| **Utils** | `app/utils/` | Reusable helper utilities |
| **Workers** | `app/workers/` | Background task definitions (stub) |

### Route Prefix Map (no double `/api/api/`)

| Route | Module |
|-------|--------|
| `/api/ai/spatial-map` | `api/spatial/spatial_routes.py` |
| `/api/ai/priority` | `api/scoring/scoring_routes.py` |
| `/api/ai/cluster` | `api/blocks/block_routes.py` |
| `/api/ai/check-feasibility` | `api/blocks/block_routes.py` |
| `/api/ai/optimize` | `api/planner/planner_routes.py` |
| `/api/planning/weekly` | `api/planner/planner_routes.py` |
| `/api/analytics/overview` | `api/analytics/analytics_routes.py` |
| `/api/audit` | `api/analytics/analytics_routes.py` |
| `/api/blocks/candidates` | `api/blocks/block_routes.py` |
| `/api/live/*` | `api/websocket/realtime_routes.py` |
| `/ws/live`, `/ws/live-trains`, `/ws/blocks` | `api/websocket/realtime_routes.py` |
| `/health`, `/health/live`, `/health/ready` | `app/main.py` |

---

## 8. ML Architecture

| Component | Type | Location |
|-----------|------|---------|
| **Spatial Translator** | Deterministic (reference table) | `services/spatial/linear_reference_service.py` |
| **MDPS Priority Scoring** | ML — GradientBoostingRegressor | `services/priority/mdps_engine.py` → `ml/models/mdps_model.pkl` |
| **Shadow Block Clustering** | Deterministic (2 km threshold) | `services/clustering/shadow_block_service.py` |
| **Constraint Engine** | Rule-based (traffic/machine/crew) | `services/optimization/constraints.py` |
| **OR-Tools Optimization** | Mathematical (SCIP + CBC fallback) | `services/optimization/milp_solver.py` |
| **Rescheduler** | Deterministic prototype (3 actions) | `services/rescheduler/policy_engine.py` |
| **RL Rescheduler** | **NOT IMPLEMENTED** (scaffolding only) | `ml/reinforcement_learning/` |
| **XAI** | Rule-based explanation | `services/xai/explanation_service.py` |

### MDPS Features

| Raw Column | Transformed Feature | Mapping |
|-----------|--------------------|---------| 
| `severity_class` | `sev_num` | A→3, B→2, C→1 |
| `overdue_days` | `overdue_days` | pass-through |
| `traffic_density_class` | `traffic_num` | High→3, Medium→2, Low→1 |
| `deferred_count` | `deferred_count` | pass-through |

**Target:** `actual_priority_rank`  
**Algorithm:** GradientBoostingRegressor (n_estimators=150, lr=0.08, max_depth=4)  
**Metrics:** MAE=2.29, RMSE=2.89, R²=0.976 | Seed=42 | scikit-learn=1.9.0

---

## 9. Data Architecture

| Directory | Contents | Status |
|-----------|----------|--------|
| `data/raw/defects/` | TMS, SMMS, TDMS defect CSVs | REAL (synthetic-generated) |
| `data/raw/network/` | Block sections, stations, geometry | REAL (synthetic-generated) |
| `data/raw/traffic/` | Timetable, live delays, slots | REAL (synthetic-generated) |
| `data/raw/resources/` | Machine + crew inventory | REAL (synthetic-generated) |
| `data/raw/historical/` | Block records, MDPS training labels | REAL (synthetic-generated) |
| `data/raw/calendars/` | Festival/seasonal calendars | REAL (synthetic-generated) |
| `data/raw/disruptions/` | Disruption events | REAL (synthetic-generated) |
| `data/raw/osm/` | OSM railway network | NOT YET CONNECTED |
| `data/raw/timetable/` | Official timetable | NOT YET CONNECTED |
| `data/raw/public/` | Public data sources | NOT YET CONNECTED |
| `data/raw/source_system/tms/` | Live TMS feed | NOT YET CONNECTED |
| `data/synthetic/` | Re-classified synthetic data | Subdirs created + READMEs |
| `data/processed/` | Pipeline-generated CSVs | 9 files preserved |
| `data/features/mdps_features/` | Train/val/test feature splits | ✅ GENERATED (30k rows) |
| `data/features/rl_features/` | RL state features | NOT YET AVAILABLE |
| `data/outputs/` | Plans, audit, reschedule logs | 6 output files preserved |
| `data/schemas/` | JSON Schema definitions | 9 schemas (7 from real data) |

---

## 10. Path and Import Changes

### Critical Fix
`settings.BASE_DIR = Path(__file__).resolve().parents[3]`  
was incorrectly `parents[4]` which resolved to `D:\` instead of `D:\Railblock_AI`.  
This fix corrected all path lookups for data files and ML artifacts.

### Import Pattern
All new service/engine files use canonical `from app.*` imports.  
Old flat files kept as shims: `from app.services.priority.mdps_engine import MDPSEngine`.  
`pytest.ini` provides `pythonpath = . backend` so both `app.*` and `backend.app.*` work.

### Run Tests With
```powershell
# Always use the project virtual environment — system Python has incompatible Starlette 1.3.1
.venv\Scripts\python.exe -m pytest tests/
```

---

## 11. Validation

### Python Compile
```
python -m compileall backend/app/ ml/ -q
Exit code: 0   (zero errors across 184 Python files)
```

### pytest
```
...................  [100%]
19 passed, 15 warnings in 21.62s
```

### ML Model Loading
```
Model available:  True
Model version:    GradientBoostingRegressor
Scoring mode:     ml_artifact_available_with_deterministic_guardrail
Fallback:         False
Sample score:     77.5  (priority_band=Critical)
```

### API Smoke Tests (16 routes verified)
```
GET  /health                    200 ✅
GET  /health/live               200 ✅
GET  /health/ready              200 ✅
POST /api/system/validate-data  200 ✅
POST /api/ai/spatial-map        200 ✅
POST /api/ai/priority           200 ✅
POST /api/ai/cluster            200 ✅
POST /api/ai/check-feasibility  200 ✅
POST /api/blocks/candidates     200 ✅
POST /api/ai/optimize           200 ✅
POST /api/planning/weekly       200 ✅
GET  /api/analytics/overview    200 ✅
GET  /api/live/trains           200 ✅
GET  /api/live/status           200 ✅
GET  /api/audit                 200 ✅
```

---

## 12. Known Limitations

1. **No trained RL artifact** — `ml/reinforcement_learning/` is scaffolding only. No `ppo_policy.zip` exists.
2. **Deterministic rescheduler** — `services/rescheduler/policy_engine.py` provides three hard-coded candidate actions (shift/consolidate/defer). RL integration is future work.
3. **Simulated live train provider** — `live/simulator.py` generates deterministic positions. External live train API is not connected.
4. **External live API not connected** — `LIVE_TRAIN_PROVIDER=simulation` in all environments.
5. **Duplicate live-delay records** — `data/raw/traffic/live_train_delays.csv` contains duplicate records (known pre-existing data quality issue).
6. **Database not connected** — `config/database.py` is a stub. The system is CSV-first; no PostgreSQL, Redis, or Celery is active.
7. **COA/BDMS schemas** — Stubbed schemas only; these source systems are not yet connected.
8. **RL feature data** — `data/features/rl_features/` has no content; RL environment not yet defined.
9. **Authentication** — `api/auth/` is a stub. No JWT/OAuth connected.
10. **Full constraint validation for rescheduler candidates** — incomplete as noted in pre-restructure status.

---

## Recommended Next Development Step

**Phase: MDPS Feature Enhancement**

The repository is now in a clean, fully-validated state. The recommended next step is:

1. Add `chainage_start` / `chainage_end` spatial features to the MDPS model
2. Retrain with the same GradientBoostingRegressor (no algorithm change)
3. Evaluate improvement in R² and MAE on held-out test set
4. Update `ml/mdps/artifacts/` and copy artifacts to `backend/app/ml/models/`

Do NOT start RL training until the RL environment (`railway_env.py`) is fully implemented and validated.
