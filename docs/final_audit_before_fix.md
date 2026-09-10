# RailBlock AI — Pre-Fix Final Repository Audit Report

**Date:** 2026-09-10  
**Branch:** `final-validation-2026-09-10`  
**Commit:** `b9a4a54bed483591bac108d99507d9b19f81b2f4`  
**Auditor Role:** Senior Full-Stack + ML + Optimization + Data Governance + QA Engineer  

---

## 1. Repository Structure

```text
Railblock_AI/
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI routers (auth, tasks, planner, disruptions, weather, etc.)
│   │   ├── core/            # Security, config, auth middleware
│   │   ├── db/              # In-memory CSV repositories & session handlers
│   │   ├── ml/              # PPO model loader & features
│   │   ├── models/          # Data schemas & Pydantic models
│   │   ├── services/        # Business logic (priority, optimization, weather, rescheduler, xai)
│   │   └── utils/           # CSV utilities, LRS math, logging
│   └── tests/               # 131 pytest unit/integration tests
├── frontend/
│   ├── src/                 # React + TanStack Router + Tailwind CSS application
│   └── package.json         # Vite + Nitro setup
├── data/
│   ├── raw/                 # Immutable datasets (network, traffic, defects, reference)
│   ├── derived/             # Spatial geometry & section weather sensitivity
│   ├── models/              # MDPS model & scaler artifacts
│   └── outputs/             # Runtime plans, audit logs, disruption logs
├── ml/
│   └── reinforcement_learning/  # PPO agent artifacts & training code
└── docs/                    # Architectural documents & validation matrices
```

---

## 2. Source of Truth Contradiction Findings

| Item / Claim | Documented Claim | Source Code / File Evidence | Truth Verdict | Impact |
| :--- | :--- | :--- | :--- | :--- |
| **OGD vs Timetable Hash** | Claimed identical | `OGD`: `ca6b9a...`, `train_timetable`: `d2da85...` | **FALSE / CONTRADICTION** | Data Governance error in docs; fixed in manifest |
| **Section Coverage** | Claimed full 68 sections | `train_timetable.csv` covers 49 unique sections (`SEC_001`–`SEC_049`) | **PARTIAL (49/68)** | Sections `SEC_050`–`SEC_068` have 0 scheduled trains |
| **MDPS Algorithm** | Claimed "RF Regressor" | `data/models/mdps_model.pkl` is `GradientBoostingRegressor` | **CONTRADICTION** | Terminology updated to `GradientBoostingRegressor` |
| **MDPS Weather Gain** | Claimed ML weather uplift | Delta $R^2 = 0.0000$, MAE delta = $0.0000$ | **ZERO UPLIFT** | Weather features give zero gain on synthetic dataset |
| **MILP Runtime** | Claimed $<50$ ms | Measured runtime: $367.8$ ms (OR-Tools SCIP solver) | **367.8 ms MEASURED** | Planning is non-real-time; runtime acceptable |
| **RBAC Status** | Claimed "VERIFIED" | `auth_routes.py` contains `NOT_CONNECTED` prototype stub | **PROTOTYPE STUB** | Header-based mock auth; not production RBAC |
| **TypeScript Strict** | Claimed passing | `npx tsc --noEmit` fails with 30 errors (`exactOptionalPropertyTypes`) | **KNOWN TS ERRORS** | Vite build succeeds via Nitro; TS types need strict cleanup |
| **PPO Metrics** | Claimed 16.345 vs 17.89 | 16.345 = overall episode mean, 17.89 = last 50 updates rolling mean | **BOTH ACCURATE** | Metrics re-labeled for clarity |

---

## 3. Dataset Inventory & Provenance Summary

- **Total Datasets**: 20 audited files.
- **Raw Immutable Files**: `data/raw/timetable/ogd/railway_train_details_original.csv` (186,124 rows, REAL), `cag_report_45_2018.pdf` (REFERENCE), `cag_report_22_2022.pdf` (REFERENCE).
- **Derived Infrastructure Data**: `stations.csv` (69 stations), `block_sections.csv` (68 planning sections), `track_geometry.csv` (1416 rows).
- **Synthetic Maintenance Workloads**: `tms_defects.csv` (30,000 Engineering tasks), `smms_defects.csv` (25,000 S&T tasks), `tdms_defects.csv` (25,000 TRD tasks).

---

## 4. Subsystem Audits

### ML Priority Scoring (MDPS)
- **Artifact**: `data/models/mdps_model.pkl` (GradientBoostingRegressor).
- **Fallback**: Deterministic scoring fallback executes when input features are incomplete or raw defect data lacks engineered features (`overdue_days`).

### Optimization Engine (MILP)
- **Solver**: OR-Tools SCIP 10.0.0.
- **Formulation**: Hard constraints for track possession, resource availability, seasonal exclusion ($SRS \ge 75$), traffic density windows. Hard constraints produce `OPTIMAL` status in 367.8 ms.

### PPO Rescheduler & Safety Guard
- **Checkpoint**: `ml/reinforcement_learning/artifacts/ppo_rescheduler_v1.pt`.
- **Safety Architecture**: Disruption $\rightarrow$ PPO Recommendation $\rightarrow$ `HardConstraintGuard` $\rightarrow$ XAI Explanation $\rightarrow$ Human Controller Review $\rightarrow$ Append-only Audit Log.

---

## 5. Required Action Items & Fix Strategy

1. **Phase 2 & 3 Data Manifest**: Update `data_manifest.csv` with distinct SHA256 checksums for `railway_train_details_original.csv` vs `train_timetable.csv` and document 49/68 section coverage.
2. **Phase 7 MDPS Model Card**: Standardize algorithm description to `GradientBoostingRegressor` and explicitly state 0.0000 ML weather uplift on synthetic labels.
3. **Phase 16 Auth / RBAC**: Mark RBAC clearly as `PROTOTYPE_STUB` (header-based authentication) in claim matrix and validation reports.
4. **Phase 23 TypeScript**: Document Vite Nitro build success while noting `exactOptionalPropertyTypes` warnings in non-blocking frontend dev build.
5. **Phase 39 Final Report & Claim Matrix**: Produce `docs/baseline_validation_final.md`, `docs/data_governance_final.md`, `docs/rolling_plan_validation.md`, `docs/final_claim_verification_matrix.md`, and update `docs/final_validation_report.md` with complete evidence.
