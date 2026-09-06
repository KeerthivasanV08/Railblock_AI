# RailBlock AI — Baseline Audit Report

**Generated:** 2026-09-06
**Auditor:** Senior Backend/ML/Railway Systems Architect

## 1. Baseline Test Results (Pre-Modification)

`
pytest backend/tests -q
Result: 1 failed, 107 passed, 53 warnings in 66.01s
`

Regressed from 108/108 to 107/108. One failure:
FAILED backend/tests/test_end_to_end_pipeline.py::test_e2e_shadow_block_clustering

Root Cause: PermissionError [WinError 5] during atomic CSV write of clustered_tasks.csv.
A leftover clustered_tasks.csv.tmp (21.6 MB) blocked os.replace() on Windows.
Classification: P0

## 2. Sklearn Version Mismatch (P2)

sklearn trained: 1.9.0 | sklearn runtime: 1.6.1
InconsistentVersionWarning on every MDPS model load.
Impact: possible incorrect MDPS priority scores.
Justification for retraining: YES.

## 3. MDPS Model Summary

Algorithm: GradientBoostingRegressor (n_estimators=100, max_depth=5)
Features: sev_num, overdue_days, traffic_num, deferred_count
Target: actual_priority_rank (separate labels file, no leakage)
Training rows: 21,000 | MAE: 2.2861 | RMSE: 2.8938 | R2: 0.9756
Feature importance: sev_num=43%, overdue_days=36%, deferred_count=16%, traffic_num=5%
Status: NEEDS RETRAINING (sklearn version mismatch)

## 4. Atomic Write Bug (P0)

atomic_write_csv() uses fixed .tmp extension. On Windows, if the temp already exists
from a prior interrupted write, os.replace() fails with WinError 5.
Fix: Use UUID-named temp file to prevent collision. Cleanup on failure.

## 5. MILP Constraints (P3)

Only one constraint exists: max blocks per day. Missing:
- Time-overlap check (two blocks same section same time)
- Resource conflict (same machine two tasks same time)
- max_train_delay_allowance param accepted but never used

## 6. Clustering Compatibility (P3)

Clusters by spatial proximity only. Missing:
- Department compatibility validation
- Work-type compatibility
- Temporal overlap check

## 7. Seasonal Intelligence (P3)

SRS calculated but only used in hard weather gate (SRS >= 75).
Not connected to MDPS scoring, planning window ordering, or prioritization.

## 8. Analytics KPIs (P4)

get_overview_kpis() returns hardcoded strings like "94.2%", "88.5%". Not computed.

## 9. Data Provenance

Train timetable (OGD): REAL
OSM network/geometry: REAL
CAG audit reports: REAL
Calibrated maintenance defects: CALIBRATED_SYNTHETIC
MDPS training labels: SYNTHETIC (calibrated from defect distribution)
Resource availability: SYNTHETIC

## 10. What Is Correct and Working

- PPO training, artifact, inference (PyTorch, self-contained)
- HardConstraintGuard (6 constraints, REJECT on failure)
- Hybrid rescheduler (PPO -> Guard -> deterministic fallback)
- XAI explanation service (uses actual inputs)
- Disruption simulator (7 scenario types)
- Spatial coordinate mapper (CHAINAGE/SIGNAL/MAST -> GPS)
- Constraint engine (6-constraint tripartite check)
- MILP solver (OR-Tools, basic objective)
- Planning service (weekly/monthly/26-week)
- Audit service (CSV-based append log)
- Approval workflow (human gate, approval_required=true)
- Data provenance contract (provenance.json)
- API router (14 route groups)
- Feature builder schema parity (training == inference)

## 11. Fix Priority

P0: Fix atomic CSV write (UUID temp, cleanup on failure)
P2: Retrain MDPS with sklearn 1.6.1
P3: Add MILP resource/overlap constraints
P3: Add clustering compatibility validation
P3: Connect seasonal SRS to planning prioritization
P4: Compute analytics KPIs from actual data
