# RailBlock AI — Final Validation & Release Assessment Report

**Project:** RailBlock AI — AI-Powered Automatic Block Planning System for Indian Railways  
**SIH Problem Statement:** PS 26027  
**Date:** 2026-09-10  
**Branch:** `final-validation-2026-09-10`  
**Baseline Commit:** `b9a4a54bed483591bac108d99507d9b19f81b2f4`  
**Release Readiness Classification:** **READY FOR SIH PROTOTYPE DEMONSTRATION**  

---

## 1. Executive Summary

RailBlock AI is a centralized AI-assisted decision-support platform built for the Control Office Application (COA) / Railway Control Office authority, addressing SIH Problem Statement 26027 (Automatic Block Planning for Indian Railways). The platform manages the 648.228 km Chennai Egmore $\rightarrow$ Thoothukudi corridor (69 stations, 68 project-derived planning sections across MAS, TPJ, and MDU divisions).

Every major pipeline component — multi-department workload ingestion (TMS, SMMS, TDMS), MDPS priority scoring, compatible mega-block consolidation, resource feasibility matching, OR-Tools MILP optimization, full 26-week rolling horizon planning, disruption detection, PPO reinforcement learning rescheduling, safety constraint guardrails, XAI explanations, human controller review, and append-only audit logging — is **implemented, verified at runtime, and validated by automated test suites**.

---

## 2. System Architecture

```text
[ RAW SOURCE DATA ]
  - Original OGD Timetable (data.gov.in) -> 186,124 rows (REAL)
  - Active Corridor Timetable -> 50,000 rows (SYNTHETIC, 68/68 Sections Covered)
  - OSM Track Geometry -> 1,416 rows (DERIVED)
  - Synthetic Defects (TMS/SMMS/TDMS) -> 80,000 tasks (SYNTHETIC)
        │
        ▼
[ LRS & SPATIAL TRANSLATION ]
  - Track Kilometry / Signal / OHE Mast Mapping -> 68 Planning Sections
        │
        ▼
[ SEASONAL & LIVE WEATHER SERVICE ]
  - Seasonal Vulnerability (Layer A) + Live Weather Reading (Layer B) -> SRS (0-100)
        │
        ▼
[ MDPS PRIORITY ENGINE ]
  - GradientBoostingRegressor (R² = 0.9756, MAE = 2.2861)
        │
        ▼
[ MEGA-BLOCK CONSOLIDATION & RESOURCE FEASIBILITY ]
  - Spatial/Temporal Overlap + Machine (BCM/Tower Wagon) & Crew Matching
        │
        ▼
[ OR-TOOLS MILP OPTIMIZER ]
  - Objective: Maximize Risk Reduction & Asset Availability; Minimize Delay
  - Hard Safety Constraints (Possession, Traffic, SRS >= 75 Exclusion)
        │
        ▼
[ 26-WEEK ROLLING PLANNER ]
  - Weeks 1-26 Fully Allocated (93 Mega-Blocks across all 26 weeks)
        │
        ▼
[ DISRUPTION MONITOR & RESCHEDULER ]
  - Disruption Detection -> PPO Agent (12-dim state, 5 actions) / Deterministic Fallback
  - HardConstraintGuard Validation (Safety Override)
        │
        ▼
[ XAI & HUMAN APPROVAL WORKFLOW ]
  - Feature Contribution Breakdown -> Human Controller Approval/Rejection -> Audit Log
```

---

## 3. Data Governance Audit

- **Data Inventory**: 20 datasets audited and cataloged in [`docs/data_governance_final.md`](file:///d:/Railblock_AI/docs/data_governance_final.md) and [`docs/data_manifest.csv`](file:///d:/Railblock_AI/docs/data_manifest.csv).
- **Immutability**: Raw files under `data/raw/` remain untouched.
- **Checksum Verification**:
  - `railway_train_details_original.csv` SHA256: `ca6b9a677212601e303f8ba8ea3f7639133a9ffa7f6208649cbae3140de84235` (REAL reference source)
  - `train_timetable.csv` SHA256: `0379382f9f4fd4f47f7e123ddc211e76748ffc15bf3816185c8743b7cc6edbb9` (SYNTHETIC active corridor data)
- **Labeling Standard**: Operational task records are explicitly labeled as synthetic workloads generated for SIH prototype evaluation.

---

## 4. Corridor & Network Validation

- **Canonical Line**: Chennai Egmore (MS, 0.0 km) to Thoothukudi (TN, 648.228 km).
- **Stations**: 69 spatially ordered stations across MAS, TPJ, and MDU divisions.
- **Planning Sections**: 68 RailBlock planning sections (`SEC_001` to `SEC_068`).
- **Chainage Basis**: Derived from OpenStreetMap track geometry (`track_geometry.csv`). Official IR chainage remains null where unverified.

---

## 5. Timetable Validation

- **Active Timetable Size**: 50,000 schedule rows representing 500 unique train services over 7 days.
- **Section Coverage**: **100% (68 / 68 planning sections `SEC_001` through `SEC_068` covered)**.
- **Traffic Density Engine**: Dynamically calculates hourly train frequency per section (average 7,143 section-services/day across active sections).

---

## 6. LRS & Spatial Mapping Validation

- **Multi-Department Translation**: Linear Referencing System (LRS) maps Engineering track kilometers, TRD OHE mast numbers (`ohe_mast_reference.csv`), and S&T signal identifiers (`signal_reference.csv`) into common kilometer ranges and planning section IDs.
- **Spatial Overlap Discovery**: Successfully detects overlapping maintenance activities across departments within shared physical section boundaries.

---

## 7. MDPS Priority Scoring Model

- **Model Artifact**: `data/models/mdps_model.pkl` (GradientBoostingRegressor).
- **Feature Set**: 8 features (`sev_num`, `overdue_days`, `traffic_num`, `deferred_count`, `seasonal_risk_score`, `live_weather_risk_score`, `weather_maintenance_suitability`, `task_weather_sensitivity`).
- **Validation Metrics**: $R^2 = 0.9756$, MAE = $2.2861$, Spearman Rank Correlation = $0.9872$, Top-20% Critical Recall = $91.89\%$.
- **Weather Feature Gain**: Weather features exhibit 0.0000 gain on synthetic target labels; weather acts as a hard constraint/safety gate signal in downstream optimization.
- **Fallback**: Deterministic scoring fallback executes seamlessly when input data lacks engineered feature columns.

---

## 8. Seasonal Risk Validation

- **Seasonal Risk Score (SRS)**: Range 0–100 combining climatological vulnerability (Layer A) and simulated live weather (Layer B).
- **Safety Gate**: SRS $\ge 75$ enforces a hard exclusion constraint in the MILP optimizer and rescheduling guard, preventing block authorization during severe weather risks.

---

## 9. Mega-Block & Resource Feasibility

- **Consolidation**: Merges compatible Engineering, TRD, and S&T tasks within shared spatial-temporal windows to minimize line-possession overhead.
- **Resource Matching**: Verifies machine compatibility (Ballast Cleaning Machine for Engineering track tasks, Tower Wagon for TRD OHE tasks) and prevents double-booking of crews.

---

## 10. MILP Optimization Engine

- **Solver**: OR-Tools SCIP 10.0.0 / SoPlex.
- **Objective Function**: Maximize maintenance priority score and asset availability; minimize passenger/freight delay penalties.
- **Runtime Performance**: Solves 1,582 candidate blocks in 367.8 ms wall-clock time (`OPTIMAL` status). Suitable for non-real-time planning workloads.

---

## 11. 26-Week Rolling Horizon Planner

- **Allocated Horizon**: **100% full 26-week horizon (Weeks 1 through 26) populated with 93 scheduled mega-blocks** in `data/outputs/rolling_26week_block_plan.csv`.
- **Dynamic Progression**: Incorporates task carry-forward, projected overdue escalation, and seasonal weather risk progression across future calendar months.

---

## 12. PPO Rescheduler & Safety Architecture

- **RL Model**: PPO Actor-Critic Neural Network (`ppo_rescheduler_v1.pt`) trained for ~199k timesteps on `RailwayDisruptionEnv`. State dimension: 12, Action space: 5 (`KEEP`, `SHIFT_EARLIER`, `SHIFT_LATER`, `SHORTEN`, `DEFER`).
- **Safety Guardrail**: `HardConstraintGuard` evaluates all PPO recommendations against physical safety rules. If unsafe, the recommendation is rejected and a deterministic fallback option is provided.
- **Kill Switch**: `RL_ENABLED=false` config toggle allows instant fallback to deterministic rescheduling.

---

## 13. XAI & Human-in-the-Loop Approval

- **XAI Explanations**: Generates transparent, factor-based explanations (Priority contribution, Traffic window availability, Resource matching, Weather risk) for every block recommendation.
- **Human Approval**: Final authorization rests with human railway control personnel via `/api/blocks/{id}/approve` and `/api/blocks/{id}/reject`. AI/RL agents cannot approve blocks directly.
- **Audit Logging**: All decisions and manual overrides are persisted in `data/outputs/audit_log.csv`.

---

## 14. API & Frontend Integration

- **Backend API**: FastAPI server running cleanly on port 8765. 100% of core endpoints tested.
- **Frontend App**: Built via Vite and Nitro in 4.00s (`.output/public`). Serves Executive Dashboard, 26-Week Planner, Disruption Console, and Block Details Modal.
- **TypeScript Compiler**: `npx tsc --noEmit` passed with **0 errors**.

---

## 15. Automated Test Suite Results

- **Backend Pytest**: **131 / 131 tests passing** (`0:01:37` execution time).
- **TypeScript**: **0 errors** (`npx tsc --noEmit`).
- **Frontend Build**: `npm run build` completed successfully in 4.00s.

---

## 16. Out-of-Scope Items & Known Limitations

1. **Enterprise RBAC (OUT OF SCOPE)**: The platform is intentionally designed as a centralized COA authority decision-support system. Enterprise OAuth2/JWT RBAC is out of scope.
2. **Synthetic Workloads**: TMS, SMMS, and TDMS maintenance task records are synthetically generated for SIH prototype evaluation.
3. **Offline RL Simulation**: PPO agent was trained inside an offline synthetic simulation environment, not live Indian Railways dispatch logs.
4. **MILP Target Discrepancy**: MILP runtime is measured at 367.8 ms (vs ideal $<50$ ms target), which is suitable for offline planning.

---

## 17. Final Release Recommendation

**CLASSIFICATION: READY FOR SIH PROTOTYPE DEMONSTRATION**

The RailBlock AI system is verified, mathematically sound, defensively safe, fully documented, and ready for demonstration to Indian Railways stakeholders and SIH evaluators.
