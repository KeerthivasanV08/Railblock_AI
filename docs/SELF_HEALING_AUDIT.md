# RAILBLOCK AI — SELF-HEALING AI AUDIT REPORT
**Corridor**: Chennai Egmore → Thoothukudi (Tamil Nadu)  
**Author**: RailBlock AI Core Systems Architecture Team  
**Status**: AUDITED & HARDENED

---

## 1. Executive Summary
The Self-Healing AI capability in RailBlock AI automates operational recovery when unexpected disruptions (e.g. late passenger/freight trains, emergency rail fractures, machine failures, or weather hazard surges) threaten scheduled track maintenance blocks.

This audit verified the end-to-end execution path, addressed critical gaps in multi-candidate evaluation, concrete time-window projection, transparent XAI explanation wiring, and active schedule synchronization.

---

## 2. Execution Flow Architecture

```text
COA / Simulated Live Telemetry
        ↓
Disruption Engine & Taxonomy Classification (impact_analyzer.py)
        ↓
Multi-Dimensional Disruption Impact Assessment
        ↓
Canonical State Builder (12-dim continuous feature vector)
        ↓
PPO Rescheduler Policy (ppo_rescheduler_v1.pt)
        ↓
Multi-Candidate Action Generation (Top Actions by Policy Probability)
        ↓
Hard Constraint Guard Validation (Non-negotiable external safety gate)
        ↓
Deterministic Rescheduler Fallback (if all RL candidates rejected)
        ↓
Explainable AI (XAI) Transparent Reasoning Attachment
        ↓
Human Controller Approval Queue (/disruptions/approve)
        ↓
Active Schedule Commitment (weekly_block_plan.csv update & versioning)
        ↓
Closed-Loop Execution & Outcome Monitoring
```

---

## 3. Disruption Event Taxonomy & Impact Assessment
The disruption engine classifies operational incidents into ten canonical types:
1. `LATE_TRAIN`: Cascading delay on mixed passenger/freight corridors.
2. `EMERGENCY_DEFECT`: Severity A track defect or fracture requiring immediate possession.
3. `RESOURCE_UNAVAILABLE`: Heavy track machine breakdown or reassignment.
4. `BLOCK_OVERRUN`: Field possession exceeding granted window by >15 minutes.
5. `CREW_DELAY`: Gang shift violation or transit delay.
6. `MACHINE_DELAY`: Heavy machinery en-route delay.
7. `WEATHER_DISRUPTION`: Severe weather or high Seasonal Risk Score (SRS ≥ 75).
8. `TRAFFIC_SURGE`: Heavy corridor congestion approaching maximum section capacity.
9. `BLOCK_CANCELLATION`: Administrative cancellation by section controller.
10. `INFRASTRUCTURE_FAILURE`: OHE power trip or interlocking/signaling failure.

### Multi-Dimensional Impact Scoring
For every event, a structured `DisruptionImpactAssessment` computes:
- **Schedule Delay Impact**: Delay minutes and anticipated train conflict counts.
- **Resource Impact (0-100)**: Machine/gang availability and travel feasibility.
- **Maintenance MDPS Exposure (0-100)**: Aggregate criticality of unserviced tasks.
- **Network Impact (0-100)**: Section traffic density and weather hazard pressure.
- **Composite Impact Score (0-100)**: Weighted index determining whether immediate rescheduling is mandated.

---

## 4. PPO Rescheduler & Safety Guarding
- **Artifact**: `ml/reinforcement_learning/artifacts/ppo_rescheduler_v1.pt` & `backend/app/ml/models/ppo_rescheduler_v1.pt`.
- **State Space**: 12-dimensional continuous normalized vector.
- **Action Space**:
  - `KEEP` (0): Maintain schedule if timetable gap allows.
  - `DELAY` (1): Shift window start by delay magnitude or +60 min.
  - `SHIFT` (2): Move block to next low-traffic early-morning window (01:00 AM).
  - `SHORTEN` (3): Compress duration by ~35% while preserving critical core tasks.
  - `CANCEL` (4): Defer block (forbidden for high MDPS tasks).

### Hard Constraint Guard Safety Rules (External to RL)
1. **Traffic Hard Limit**: Reject any candidate with corridor traffic density ≥ 0.85.
2. **Weather SRS Gate**: Reject any candidate with Seasonal Risk Score ≥ 75.0.
3. **Minimum Window**: Reject any candidate window < 30 minutes.
4. **Machine Availability**: Verified against equipment depot deployment.
5. **Crew Availability**: Maximum consecutive shift limit enforced at 12.0 hours.
6. **High-Priority Deferral Ban**: Tasks with MDPS ≥ 85.0 cannot be cancelled or deferred.

### Fallback Hierarchy
1. PPO candidate #1 passes Guard → accepted as top recommendation.
2. PPO candidate #1 fails Guard → PPO candidate #2 and #3 evaluated.
3. All PPO candidates fail Guard → **Deterministic Rescheduler** generates delay, shift, and reallocate alternatives.
4. If deterministic options fail → Escalated to Controller for manual intervention.
5. **Rule**: RL failure *never* produces an unsafe or empty schedule.

---

## 5. Audit Findings & Remediations Applied

| Issue | Severity | Status Before | Fix Applied |
| :--- | :--- | :--- | :--- |
| Single-candidate PPO check | P1 | Only tested top-1 action; dropped RL immediately if rejected | Evaluates ranked action distribution through Guard |
| Abstract RL candidates | P1 | Candidates had only action name; lacked operational timestamps | Projections generate concrete `start_time`, `end_time`, `recommended_window` |
| Disconnected XAI | P1 | `explain_rescheduled_block` existed but was never called | Wired directly into every candidate proposal |
| Schedule update disconnect | P0 | Approval only logged audit event, leaving plan unchanged | Active modification of `weekly_block_plan.csv` and version tracking |
