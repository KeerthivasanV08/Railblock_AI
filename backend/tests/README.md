# RailBlock AI — Backend Test Suite
 
## Test Execution Status
- **Current Verified Test Suite:** **143 PASSED, 0 FAILED** (138s execution time)
- **Framework:** Pytest 9.0.2 with AnyIO, Faker, and FastAPI TestClient
- **Command:** `python -m pytest backend/tests/ -v`

---

## Test Suite Structure & Coverage

| Category | Path | Key Test Scenarios | Verified Count |
|---|---|---|---|
| **API Endpoints** | `backend/tests/api/` | CORS preflight options, `/api/blocks/{id}/approve`, `/reject`, `/modify`, `/execute`, endpoint regressions | 7 |
| **Integration** | `backend/tests/integration/` | End-to-end route registration, validation service schemas, MDPS artifact loading, live provider health | 5 |
| **Machine Learning** | `backend/tests/ml/` | MDPS feature builder schema stability, missing value imputations, deterministic inference bounds | 2 |
| **MILP Optimization** | `backend/tests/optimization/` | Optimal subset selection, max blocks per day constraint, resource fleet bounds, empty candidates, infeasibility | 5 |
| **System Runtime & Pipeline** | `backend/tests/` | Spatial translation, MDPS priority with XAI, shadow block clustering, constraint feasibility, rescheduler approval, data integrity, preprocessing | 19 |
| **Unit Tests** | `backend/tests/unit/` | Monthly dynamic progression, Multi-horizon synchronization & lifecycle safety, Data provider abstractions & provenance, Closed-loop execution feedback, Disruption impact assessment, Live routes, PPO rescheduler artifact & guardrails, 26-week rolling plan, Seasonal intelligence & weather traceability | 105 |
| **Total** | | | **143 PASSED** |

---

## Key Test Principles
1. **Human-in-the-Loop Enforcement:** `test_execute_unapproved_block_fails` validates that direct execution of unapproved blocks (`PROPOSED -> EXECUTED`) is strictly rejected with a 400 error.
2. **Multi-Horizon Synchronization:** `test_approve_then_execute_flow_syncs` ensures status, versions, and execution records synchronize across Weekly, Monthly, and 26-Week plans via dual-key matching (`block_id` or `task_ids`).
3. **Dynamic Progression:** `test_generate_monthly_plan_dynamic_progression` verifies that subsequent weeks do not duplicate Week 1, carrying forward unaddressed tasks, escalating overdue days, and injecting cyclic USFD maintenance at Week 4.
4. **Data Provider Provenance:** `test_csv_maintenance_data_provider` and related tests assert that provenance metadata truthfully tags sources (`CALIBRATED_SYNTHETIC`, `REAL_OGD`, `DERIVED_FREIGHT_MODEL`), while enterprise adapters raise `NotImplementedError`.
5. **Weather Resilience:** `test_live_weather_service_unavailable_resilience` verifies that unavailable weather returns `UNKNOWN` and rescales seasonal weights without silently defaulting severity to zero.

