# RAILBLOCK AI — REMEDIATION PLAN & GAP CLOSURE SUMMARY
**Corridor**: Chennai Egmore → Thoothukudi (Tamil Nadu)  
**Status**: REMEDIATED & VERIFIED

---

## 1. Traceability of Discovered Gaps & Fixes Applied

| ID | Component | Gap Description | Priority | File Modified | Fix Summary |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GAP-01** | Plan Modification on Approval | Reschedule approval recorded an audit entry but left the active block plan unchanged. | **P0** | `rescheduler_service.py`, `disruption_routes.py` | Automatically updates `weekly_block_plan.csv`, transitions block status to `RESCHEDULED`, updates timestamps, and increments `plan_version`. |
| **GAP-02** | Disruption Event Taxonomy | Only 3 hardcoded event types; missing 7 operational types. | **P1** | `impact_analyzer.py` | Implemented 10 canonical event types (`LATE_TRAIN`, `EMERGENCY_DEFECT`, `RESOURCE_UNAVAILABLE`, `BLOCK_OVERRUN`, etc.). |
| **GAP-03** | Impact Assessment Engine | Missing structured multi-dimensional impact scoring. | **P1** | `impact_analyzer.py` | Created `DisruptionImpactAssessment` calculating schedule, resource, maintenance MDPS exposure, network pressure, and composite score. |
| **GAP-04** | PPO Multi-Candidate Evaluation | Only evaluated argmax action; immediately abandoned RL if guard rejected top-1. | **P1** | `rescheduler_service.py` | Added ranked evaluation across policy distribution (`predict_all`); tests top 3 actions before triggering deterministic fallback. |
| **GAP-05** | RL Operational Timestamps | RL candidates only returned abstract action names without concrete start/end times. | **P1** | `rescheduler_service.py` | Implemented `_project_time_window` generating concrete `start_time`, `end_time`, `recommended_window`, `shift_from_original_hours`, and `new_block_id`. |
| **GAP-06** | XAI Disconnect | `explain_rescheduled_block` existed but was never invoked in production pipeline. | **P1** | `rescheduler_service.py` | Attached full XAI breakdown (`why_recommended`, `risk_factors`, `constraint_checks`, `estimated_train_impact`) to every candidate. |
| **GAP-07** | Optimization Multi-Objective | Solver had hardcoded formulas and disconnected 3-constant stub. | **P1** | `objective.py`, `milp_solver.py` | Built `OptimizationObjectiveWeights` with calibrated multi-objective terms and sensitivity analysis. |
| **GAP-08** | 26-Week Rolling Planning | Only generated 4-week duplicate plan. | **P1** | `planning_service.py` | Implemented `generate_rolling_plan(horizon_weeks=26)` with overdue day escalation, deferred risk compounding, seasonal modulation, and cyclic maintenance. |
| **GAP-09** | Execution Feedback Loop | `execution_monitor.py` was an empty stub returning `[]`. | **P1** | `feedback_engine.py`, `execution_routes.py` | Implemented `ExecutionFeedbackEngine` analyzing duration variance, overrun rates, buffer wastage, and calibrating learned section buffers. |
| **GAP-10** | Central Model Registry | No programmatic registry for ML models. | **P2** | `app/ml/registry.py` | Implemented `ModelRegistry` serving metadata, feature schemas, training provenance, and decision audit logs. |
| **GAP-11** | Legacy Section ID Fallback | Hardcoded `SEC-ALJN-TDL` in approval service fallback. | **P2** | `approval_service.py` | Replaced with `SEC_001` matching Chennai Egmore corridor topology. |
