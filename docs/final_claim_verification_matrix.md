# RailBlock AI — Final Claim Verification Matrix

**Date:** 2026-09-10  
**Branch:** `final-validation-2026-09-10`  
**Evidence Standard:** Strict Code & Runtime Evidence  

---

| ID | Claim | Expected Value | Actual Measured / Code Value | Source File | Code Reference | Runtime Test / Evidence | Status | Severity | Recommended Action |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CLM-01** | Corridor | Chennai Egmore → Thoothukudi | 648.228 km, 69 stations, MS → TN | `data/raw/network/stations.csv` | `StationRepository` | Station list & chainage calculation | **VERIFIED** | INFO | None |
| **CLM-02** | Planning Sections | 68 planning sections | 68 sections (`SEC_001`–`SEC_068`) | `data/raw/network/block_sections.csv` | `block_sections.csv` | Project-derived planning sections | **VERIFIED** | INFO | Label as derived planning sections |
| **CLM-03** | Divisions | 3 divisions (MAS, TPJ, MDU) | MAS, TPJ, MDU present in station data | `data/raw/network/stations.csv` | `stations.csv:L2-L70` | Division mapping verified | **VERIFIED** | INFO | None |
| **CLM-04** | OGD Timetable Source | Real IR public timetable | 186,124 rows, 11,113 unique trains | `data/raw/timetable/ogd/...` | `railway_train_details_original.csv` | SHA256: `ca6b9a677212601e` | **VERIFIED** | INFO | None |
| **CLM-05** | Runtime Timetable | 50,000 schedule rows | 50,000 rows, 500 trains, 68 sections | `data/raw/traffic/train_timetable.csv` | `train_timetable.csv` | SHA256: `0379382f9f4fd4f4` | **VERIFIED** | INFO | None |
| **CLM-06** | Timetable Section Coverage | 68 / 68 sections | 68 / 68 sections (`SEC_001`–`SEC_068`) | `data/raw/traffic/train_timetable.csv` | `train_timetable.csv` | pandas unique check: 68 sections | **VERIFIED** | INFO | Full 68-section coverage verified |
| **CLM-07** | MDPS Algorithm | ML Priority Scoring | GradientBoostingRegressor ($R^2=0.9756$) | `data/models/mdps_model.pkl` | `mdps_engine.py:L142` | `type(model)` = GradientBoostingRegressor | **VERIFIED** | INFO | Update docs to GradientBoostingRegressor |
| **CLM-08** | MDPS Weather Uplift | Positive predictive gain | Delta $R^2 = 0.0000$, MAE delta = $0.0000$ | `data/models/mdps_model.pkl` | `mdps_engine.py` | Ablation comparison: base vs weather | **KNOWN LIMITATION** | P2 | Document 0 ML uplift on synthetic labels |
| **CLM-09** | MILP Solver | OR-Tools SCIP optimizer | SCIP 10.0.0 / SoPlex, OPTIMAL output | `backend/.../planner_service.py` | `planner_service.py:L85` | Optimization benchmark run | **VERIFIED** | INFO | None |
| **CLM-10** | MILP Runtime Target | $<50$ ms | $367.8$ ms measured wall-clock | `docs/performance_benchmark.md` | `planner_service.py` | `time.perf_counter()` benchmark | **KNOWN LIMITATION** | P3 | Accept 367.8 ms for non-real-time plan |
| **CLM-11** | Seasonal Weather Engine | SRS 0–100 risk score | Seasonal risk engine with Layer A/B | `backend/.../seasonal_service.py` | `SeasonalRiskEngine` | SRS calculation test pass | **VERIFIED** | INFO | None |
| **CLM-12** | Weather Safety Gate | Hard exclusion for high risk | SRS $\ge 75$ excludes block scheduling | `backend/.../constraints.py` | `constraints.py:L45` | Hard constraint unit test pass | **VERIFIED** | INFO | None |
| **CLM-13** | Resource Feasibility | Machine & crew matching | BCM/Tower Wagon department check | `backend/.../resource_service.py` | `ResourceFeasibilityService` | Resource overlap test pass | **VERIFIED** | INFO | None |
| **CLM-14** | Mega-Block Discovery | Multi-department merge | Compatible TMS + SMMS + TDMS merge | `backend/.../planner_service.py` | `OptimizationService` | Mega-block test pass | **VERIFIED** | INFO | None |
| **CLM-15** | 26-Week Rolling Planner | Backend dynamic planner | 93 blocks scheduled across W1–W26 | `data/outputs/...` | `rolling_26week_block_plan.csv` | CSV inspection: W1–W26 populated | **VERIFIED** | INFO | Full 26-week horizon verified |
| **CLM-16** | PPO Rescheduler Model | Actor-Critic RL agent | MLP trained ~199k steps (reward 16.35) | `ml/.../ppo_rescheduler_v1.pt` | `ReschedulingService` | PyTorch checkpoint loading test | **VERIFIED** | INFO | None |
| **CLM-17** | Rescheduler Safety Guard | Safety override on RL | `HardConstraintGuard` blocks unsafe action | `backend/.../rescheduler_service.py` | `HardConstraintGuard` | Guard unit test pass | **VERIFIED** | INFO | None |
| **CLM-18** | Human-in-the-Loop Approval | Controller review required | AI recommends $\rightarrow$ Human approves | `backend/.../block_routes.py` | `block_routes.py:L110` | Approve/Reject endpoint test pass | **VERIFIED** | INFO | Safety override strictly enforced |
| **CLM-19** | Audit Logging | Append-only decision log | Action logging with timestamp & user | `data/outputs/audit_log.csv` | `CSVRepository` | CSV log update verified | **VERIFIED** | INFO | None |
| **CLM-20** | Authentication / RBAC | Enterprise RBAC roles | Centralized COA authority dashboard | `backend/.../auth_routes.py` | `auth_routes.py:L35` | Positioned as COA decision platform | **OUT OF SCOPE** | INFO | RBAC is out of scope for prototype |
| **CLM-21** | Frontend TypeScript | Clean strict compilation | 0 errors (`npx tsc --noEmit`) | `frontend/tsconfig.json` | `package.json` | `npx tsc --noEmit` passed with 0 errors | **VERIFIED** | INFO | All TS errors resolved |
| **CLM-22** | Unit Test Suite | Backend unit/integration | 131 / 131 tests passing cleanly | `backend/tests` | `pytest` | Pytest run: 131 passed in 97s | **VERIFIED** | INFO | None |
