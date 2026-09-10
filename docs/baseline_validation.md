# RailBlock AI — Phase 0: Baseline Validation Report

**Date:** 2026-09-10  
**Tag:** `railblock-sih-baseline-2026-09-10`  
**Branch:** `main`  
**Git Status:** Clean working tree — nothing to commit  
**Auditor Role:** Senior Full-Stack + ML/AI + Optimization + QA Engineer

---

## 1. Repository State

| Property | Value |
|----------|-------|
| Branch | `main` |
| Last Commit | `af8a34b` — "needed docs added" |
| Working Tree | **Clean** (no uncommitted changes) |
| Baseline Tag | `railblock-sih-baseline-2026-09-10` |

### Recent Commit History
```
af8a34b needed docs added
e82ace3 ml retrained checked
9dafb8c The mock/wrong data shown in pages changed
261ab78 dataset updated
aae2344 Modification in the weather intelligence work flow
64ac46c Errors resolved
a55df60 Frontend routing corrected and updated
```

---

## 2. Backend Test Suite — Baseline Run

**Command:** `python -m pytest backend/tests -q --tb=short`

| Metric | Value |
|--------|-------|
| **Tests Collected** | **131** |
| **Tests Passed** | **131** |
| **Tests Failed** | **0** |
| **Warnings** | 37 (non-fatal: deprecation warnings from FastAPI/httpx/OR-Tools) |
| **Runtime** | 88.00 seconds (1m 28s) |
| **Exit Code** | **0 (SUCCESS)** |

### Warning Categories (non-blocking)
- `StarletteDeprecationWarning`: FastAPI `HTTP_422_UNPROCESSABLE_ENTITY`
- `DeprecationWarning`: OR-Tools SwigPy internal types
- `DtypeWarning`: Mixed types in large CSV (non-fatal: `csv_utils.py:32`)
- `UserWarning`: Datetime format inference in `validation_service.py:261`

**Assessment:** All 131 tests pass. Warnings are cosmetic or from third-party libraries.

---

## 3. Backend Startup Verification

**Method:** `uvicorn app.main:app --host 127.0.0.1 --port 8765` (from `backend/`)

| Check | Result |
|-------|--------|
| Backend imports successfully | YES |
| FastAPI app routes loaded | **93 routes registered** |
| Server starts without crash | YES |
| `/health` endpoint responds | `{"status":"healthy","data_source":"csv"}` |
| Root `/` endpoint responds | `{"service":"RailBlock AI Backend","status":"healthy"}` |

---

## 4. Key API Endpoint Runtime Verification

### 4.1 Analytics Overview — `/api/analytics/overview`
```json
{
  "asset_availability": "99.9%",
  "maintenance_completion": "3.3%",
  "active_blocks": 3,
  "critical_defects": 30627,
  "overdue_tasks": 77330,
  "block_utilization": "69.6%",
  "integrated_block_percentage": "85.0%",
  "unused_block_time_minutes": 164,
  "deferred_tasks": 21549,
  "total_unified_tasks": 80000
}
```
**Status:** LIVE (computed from CSV)  
**Note:** `maintenance_completion = 3.3%` reflects synthetic dataset where most tasks are overdue — not a bug, but a known synthetic dataset characteristic requiring documentation.

### 4.2 Seasonal Sections — `/api/seasonal/sections`
- Returns **68 sections** with full SRS data per section
- Season: Southwest Monsoon (season_score=30.0, correct for September)
- weather_source_status: `"AVAILABLE"` for all sections
- SRS range: 21.2 – 39.0 (all LOW risk at current simulation baseline)
- hard_safety_exclusion: `false` for all (expected)
- **Status:** CORRECT

### 4.3 26-Week Rolling Plan — `/api/planning/rolling`
- Returns blocks: `RB-W{week}-{section}-{n}` and `CYC-W{week}-{type}-{section}`
- `total: 43` (includes both MDPS-ranked and cyclic maintenance blocks)
- Includes `xai_reason`, `departments`, `priority`, `seasonal_risk_score_projected`
- `source` field: `rolling_optimizer` vs `cyclic_maintenance_calendar`
- **Status:** Backend-generated, dynamic

### 4.4 Disruptions — `/api/disruptions`
- Returns paginated disruptions: `total: 25000`, `pages: 500`
- Types: `Late Train`, `Machine Breakdown`, `Emergency Defect`
- **Status:** LIVE CSV data

### 4.5 Route Discovery Note
- `/api/planner/rolling-plan` → 404 (frontend must use `/api/planning/rolling`)

---

## 5. Frontend Build

**Command:** `npm run build` (in `frontend/`)

| Metric | Value |
|--------|-------|
| Build Artifacts Generated | YES (`.output/` created) |
| Build Message | `built in 1.24s` |
| TypeScript `--noEmit` | **30 errors** in 8 files |
| TypeScript Error Type | `exactOptionalPropertyTypes` strictness violations |
| Affected Files | `TaskFilters.tsx`, `operations.ts`, `resources.ts`, `sections.ts`, `stations.ts`, `random.ts`, `csvExportService.ts`, `aiService.ts`, `notificationStore.ts` |

**Assessment:** Build generates output. TypeScript errors are strict-mode optional property violations in static data files — no runtime breakage, but type safety debt.

---

## 6. Data File Checksums (Baseline)

| File | Size | SHA256 (first 16) |
|------|------|-------------------|
| `data/raw/network/stations.csv` | 4,454 B | `372653b799ecba48` |
| `data/raw/network/block_sections.csv` | 2,961 B | `64ab800f7c780ffa` |
| `data/raw/traffic/train_timetable.csv` | 3,004,920 B | `d2da85440c0bc640` |
| `data/raw/defects/tms_defects.csv` | 2,806,923 B | `fb9c6e11a59fca8c` |
| `data/raw/defects/smms_defects.csv` | 2,400,645 B | `cff3a7c245b60c68` |
| `data/raw/defects/tdms_defects.csv` | 2,414,299 B | `112bbc2feabf1db8` |
| `data/models/mdps_model.pkl` | 651,768 B | `6d213bf130f20e08` |
| `ml/reinforcement_learning/artifacts/ppo_rescheduler_v1.pt` | 80,359 B | `1af9f66acb6988d6` |

---

## 7. Dataset Quick-Count Verification

| Dataset | Rows | Provenance |
|---------|------|------------|
| `stations.csv` | **69 stations** | DERIVED (OSM + public) |
| `block_sections.csv` | **68 sections** | DERIVED (OSM + public) |
| `train_timetable.csv` | **50,000 rows** | SYNTHETIC (timetable-grounded) |
| `tms_defects.csv` | **30,000 tasks** | SYNTHETIC operational workload |
| `smms_defects.csv` | **25,000 tasks** | SYNTHETIC operational workload |
| `tdms_defects.csv` | **25,000 tasks** | SYNTHETIC operational workload |
| **Total unified tasks** | **80,000** | SYNTHETIC |
| Unique trains in timetable | **500 trains** | SYNTHETIC |
| Avg services/day (computed) | **7,143** | Computed from timetable |

---

## 8. Known Issues at Baseline

| Issue | Severity | Impact |
|-------|----------|--------|
| `maintenance_completion = 3.3%` (all-overdue synthetic dataset) | LOW | Documentation needed |
| 30 TypeScript `exactOptionalPropertyTypes` errors | LOW | No runtime impact |
| `npx tsc --noEmit` exits code 1 | LOW | Type strictness debt |
| `/api/planner/rolling-plan` returns 404 | MEDIUM | Frontend must use `/api/planning/rolling` |
| FastAPI deprecation warnings (`HTTP_422`) | COSMETIC | No functional impact |
| OR-Tools SwigPy deprecation warnings | COSMETIC | No functional impact |

---

## 9. Baseline Summary

| Gate | Status |
|------|--------|
| Backend tests passing | 131/131 PASS |
| Backend starts and is healthy | PASS |
| Analytics API live | PASS |
| Seasonal API live (68 sections) | PASS |
| Rolling 26-week plan API live | PASS |
| Disruptions API live (25,000 events) | PASS |
| Frontend build produces output | PASS |
| Frontend TypeScript clean (`--noEmit`) | FAIL (30 errors) |
| Git working tree clean | PASS |
| Baseline tag created | PASS (`railblock-sih-baseline-2026-09-10`) |

> **Conclusion:** The system is functional. Backend is healthy and all major API families respond correctly. Frontend build completes but has TypeScript strict-mode errors. The system is suitable for Phase 1 claim verification.
