# RailBlock AI — Performance Benchmark Report

**Date:** 2026-09-10  
**Hardware:** Development workstation (Windows, Python 3.11.8)  
**Benchmark Methodology:** Measured using `time.perf_counter()` wall-clock; single-run (not statistical average)

---

## 1. API Latency (Live Backend — Port 8765)

| Endpoint | Measured Latency | Notes |
|----------|-----------------|-------|
| `GET /health` | ~5ms | Pure health check |
| `GET /api/analytics/overview` | **115ms** | Reads multiple CSVs, computes KPIs |
| `GET /api/seasonal/sections` | ~3000ms | Computes SRS for all 68 sections including live weather load |
| `GET /api/planning/rolling` | ~500ms | Reads rolling plan CSV + filters |
| `GET /api/disruptions` | ~200ms | Reads 25,000-row disruption CSV |

> **Note:** X-Response-Time-Ms header is added by backend middleware. `analytics/overview` at 115ms includes CSV parsing for multiple files.

---

## 2. MDPS Priority Scoring

| Dataset Size | Time (ms) | Rate (tasks/sec) | ML Mode |
|-------------|-----------|-----------------|---------|
| 100 tasks | 179.9ms | 556/sec | ml_artifact_with_deterministic_guardrail |
| 1,000 tasks | 2,700ms | 370/sec | ml_artifact_with_deterministic_guardrail* |
| 80,000 (estimated) | ~216,000ms (~3.6 min) | 370/sec | — |

> **Important Note:** MDPS ML inference falls back to **deterministic mode** when raw defect CSVs are used directly (missing `overdue_days` etc. in the column format). ML inference only activates when data passes through the full preprocessing pipeline (`run_pipeline.py`) which enriches columns. The scoring mode shows `ml_artifact_available_with_deterministic_guardrail` in both cases because the model is loaded — but the per-row ML prediction fails and falls through to deterministic scoring for raw data.

> **Root Cause of Slow Rate:** Row-by-row `calculate_priority()` call in `score_dataframe()` for each task. Performance improvement opportunity: batch inference using `model.predict()` on full feature matrix.

---

## 3. MILP Optimizer (OR-Tools SCIP)

| Scenario | Candidates | Selected | Solver Status | Runtime |
|----------|-----------|----------|---------------|---------|
| Baseline (feasibility-filtered) | 1,582 | 3 | OPTIMAL | **367.8ms** |

> **Note:** Candidate count is 1,582 after hard feasibility pre-filter. MILP runtime of 367.8ms is for this filtered candidate set. Claimed `<50ms` is not achieved — actual runtime is ~370ms. For full 80k tasks, the feasibility pre-filter reduces candidates before the MILP receives them.

---

## 4. Rescheduler Pipeline

| Component | Measured Time |
|-----------|-------------|
| Disruption impact assessment | <10ms |
| PPO neural inference (1 call, 3 candidates) | ~50ms |
| HardConstraintGuard (3 candidates) | <5ms |
| XAI explanation generation (6 options) | <10ms |
| Total `generate_reschedule_options()` | ~100ms |

---

## 5. Preprocessing Pipeline (`run_pipeline.py`)

| Step | Description | Status |
|------|-------------|--------|
| 1–10 steps total | Full preprocessing pipeline | 10/10 PASS (prior run) |
| Estimated full pipeline (80k tasks) | ~45–90 seconds | Not re-benchmarked this session |

---

## 6. Frontend Build

| Metric | Value |
|--------|-------|
| `npm run build` | `built in 1.24s` |
| Output artifacts | `.output/` directory |
| TypeScript errors | 30 (strict mode) |

---

## 7. Key Performance Observations

| Observation | Severity | Recommendation |
|-------------|----------|----------------|
| MDPS row-by-row scoring: ~370 tasks/sec | MEDIUM | Vectorize `build_mdps_features()` + batch `model.predict()` call |
| Seasonal section API: ~3s for 68 sections | LOW | Cache SRS results; invalidate on weather update |
| MILP 367ms vs claimed <50ms | LOW | Acceptable for planning (non-real-time) use case |
| API analytics: 115ms | OK | Reasonable for CSV reads with computation |
