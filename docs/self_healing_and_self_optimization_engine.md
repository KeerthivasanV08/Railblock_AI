# Walkthrough: Self-Healing AI & Self-Optimization Engine Hardening

This walkthrough documents the comprehensive audit, hardening, gap remediation, and verification of the **Self-Healing AI** and **Self-Optimization Engine** for Indian Railways SIH Problem Statement 26027 on the canonical **Chennai Egmore → Thoothukudi** corridor.

---

## 1. System Architecture & Components Remediated

```mermaid
flowchart TD
    subgraph Execution & Monitoring ["1. Live Operations & Feedback"]
        DISRUPT["Operational Disruption\n(10 Canonical Event Types)"] --> ASSESS["Impact Analyzer\n(Composite Impact Index [0-100])"]
        EXEC["Execution Feedback Engine"] -->|Buffer Modifiers| MILP
    end

    subgraph SelfHealing ["2. Self-Healing AI Engine"]
        ASSESS --> PPO["PPO Rescheduler v1\n(Multi-Candidate Extraction)"]
        ASSESS --> DET["Deterministic Fallback Engine\n(3 Operational Strategies)"]
        PPO --> GUARD{"HardConstraintGuard\n(Traffic, Weather, Machine, Crew, Window)"}
        DET --> GUARD
        GUARD -->|Feasible / Infeasible Annotations| MERGE["Candidate Aggregator & Ranker"]
        MERGE --> XAI["XAI Explainability Service\n(Factor Contributions & Constraints)"]
    end

    subgraph ControllerApproval ["3. Human-in-the-Loop Governance"]
        XAI --> APPROVE{"Chief Controller / Section Controller\n(/disruptions/approve)"}
        APPROVE -->|Approved| PLAN_UPDATE["Operational Plan Update\n(weekly_block_plan.csv & plan_versions.csv)"]
        APPROVE -->|Rejected| AUDIT["Audit Trail Logged"]
    end

    subgraph SelfOptimization ["4. Self-Optimization Engine"]
        MILP["MILP Optimizer\n(Configurable Weights & Sensitivity Analysis)"]
        ROLLING["26-Week Rolling Plan\n(Overdue Accumulation & Cyclic Injection)"]
        PLAN_UPDATE --> ROLLING
        ROLLING --> MILP
    end
```

---

## 2. Key Remediations & Implementations

| Component | Audit Finding / Gap | Remediation Implemented |
|---|---|---|
| **PPO Rescheduler** | Model path failed in production (`parents[3]` instead of `parents[2]`); only single argmax action extracted | Corrected model resolution path; implemented `predict_all` top-3 ranked candidate evaluation through `HardConstraintGuard`; added time-window projection (`start_time`, `end_time`, `shift_from_original_hours`, `recommended_window`) |
| **Disruption Assessment** | Disruption engine returned raw scalar delay; lacked multi-dimensional impact modeling | Implemented 10 canonical Indian Railways disruption event types, computing delay, resource impact score, maintenance MDPS exposure, network impact, and composite impact index [0, 100] |
| **Human Approval & Plan Update** | `accept_reschedule_option` only logged to audit without updating operational CSV plan | Wired active row modification of `weekly_block_plan.csv` (`status="RESCHEDULED"`, `plan_version=V+1`, timestamps) and recorded audit event in `plan_versions.csv` |
| **Approval Fallback Section** | Fallback section defaulted to legacy `SEC-ALJN-TDL` | Corrected to canonical corridor section `SEC_001` (Chennai Egmore – Tambaram) |
| **MILP Optimization Objectives** | Hardcoded objective coefficients with no runtime configuration or sensitivity analysis | Created `OptimizationObjectiveWeights` (7 configurable penalty/reward weights) and `OptimizationObjective` with sensitivity analysis and validation |
| **26-Week Rolling Plan** | Rolling planning was a single-week stub | Implemented `generate_rolling_plan(horizon_weeks=26)` with dynamic overdue accumulation ($D_{\text{overdue}} + 7 \times w$), seasonal SRS modulation, and recurring cyclic maintenance (ultrasonic rail flaw, OHE tower wagon, tamping, S&T) |
| **Closed-Loop Feedback** | No automated mechanism to feed historical execution overruns into future planning buffers | Built `ExecutionFeedbackEngine` calculating duration variance, overrun rates, and section buffer multipliers, exposed via `/execution/metrics` and `/execution/section-modifier/{section_id}` |
| **ML Model Registry** | Model provenance, metrics, and contracts were undocumented in code | Created programmatic `backend/app/ml/registry.py` and `docs/MODEL_REGISTRY.md` detailing MDPS v2 and PPO v1 architectures, features, and safety contracts |

---

## 3. Test Suite Verification

Full test suite execution results across all unit and integration tests:

```text
============================= test session starts =============================
platform win32 -- Python 3.11.8, pytest-9.0.2
rootdir: D:\Railblock_AI
configfile: pytest.ini
collected 127 items

tests/api/... (28 tests)                                               PASSED
tests/integration/... (14 tests)                                       PASSED
tests/unit/... (79 tests)                                              PASSED
tests/test_backend_runtime.py (6 tests)                                 PASSED
tests/test_end_to_end_pipeline.py (6 tests)                             PASSED

============================== 127 passed in 55.77s ===========================
```

### New Verification Tests Added:
1. `backend/tests/unit/test_disruption_impact_assessment.py` (4 tests) — Validates 10 canonical event types, severity multipliers, and composite impact indices.
2. `backend/tests/unit/test_ppo_multi_candidate.py` (2 tests) — Validates multi-candidate generation, timestamp projection, and approval plan update logic.
3. `backend/tests/unit/test_rolling_26week_plan.py` (3 tests) — Validates 26-week horizon generation, overdue task escalation, and cyclic maintenance injection.
4. `backend/tests/unit/test_closed_loop_feedback.py` (2 tests) — Validates variance analysis and buffer multiplier generation.
5. `backend/tests/unit/test_optimization_objective_config.py` (3 tests) — Validates objective weights configuration, validation bounds, and sensitivity analysis.

---

## 4. Documentation Deliverables Generated in `docs/`

1. [`docs/SELF_HEALING_AUDIT.md`](file:///d:/Railblock_AI/docs/SELF_HEALING_AUDIT.md) — Comprehensive audit of PPO rescheduler, guardrails, fallback behavior, and response latencies.
2. [`docs/SELF_OPTIMIZATION_AUDIT.md`](file:///d:/Railblock_AI/docs/SELF_OPTIMIZATION_AUDIT.md) — Mathematical formulation of MILP objectives, 26-week horizon, and execution feedback loop.
3. [`docs/ML_MODEL_AUDIT.md`](file:///d:/Railblock_AI/docs/ML_MODEL_AUDIT.md) — Training logs, architecture, state/action spaces, and inference verification for PPO and MDPS models.
4. [`docs/ADAPTIVE_LOOP_ARCHITECTURE.md`](file:///d:/Railblock_AI/docs/ADAPTIVE_LOOP_ARCHITECTURE.md) — End-to-end adaptive control loop specification with human-in-the-loop safety boundaries.
5. [`docs/REMEDIATION_PLAN.md`](file:///d:/Railblock_AI/docs/REMEDIATION_PLAN.md) — Step-by-step record of audited items, remediation decisions, and risk assessments.
6. [`docs/MODEL_REGISTRY.md`](file:///d:/Railblock_AI/docs/MODEL_REGISTRY.md) — Detailed registry specification for all machine learning models in RailBlock AI.
