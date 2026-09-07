# RAILBLOCK AI — ADAPTIVE CLOSED-LOOP OPTIMIZATION ARCHITECTURE
**Corridor**: Chennai Egmore → Thoothukudi (Tamil Nadu)  
**Status**: ARCHITECTURAL SPECIFICATION & DEPLOYMENT BLUEPRINT

---

## 1. System Vision
RailBlock AI is not a static one-shot planner. It is an **adaptive closed-loop railway operations optimization system** engineered for Indian Railways.

The architecture enforces clear boundaries:
- **Self-Optimization Engine**: Operates at the tactical and strategic horizon (weeks to 26 weeks) to solve large-scale resource allocation and multi-department block pairing.
- **Self-Healing AI**: Operates at execution time (minutes to hours) to rapidly recover from delays, breakdowns, and emergency defects.
- **Human Authority**: Human Section Controllers retain ultimate decision authority over block possession approval and plan modification.

---

## 2. End-to-End Operational Lifecycle

```text
               ┌────────────────────────────────────────────────────────┐
               │           Historical + Live Operational Data           │
               │         TMS / SMMS / TDMS / COA / Live Weather         │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │           Feature Extraction & Priority Scoring        │
               │            (LRS Spatial Mapping + MDPS Engine)         │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │         Tripartite Feasibility & Mega-Block Clustering │
               │      (Timetable Gaps + Machine Movement + Gang Shift)  │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │              OR-Tools MILP Global Optimizer            │
               │   (Multi-Objective: Risk Reduction, Wastage, Delays)   │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │             26-Week Rolling & Weekly Schedule          │
               │     (Cyclic Inspection + Overdue Risk Compounding)     │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │            Human Controller Review & Approval          │
               │        (Transparent XAI Breakdown & Conflict Proof)    │
               └───────────────────────────┬────────────────────────────┘
                                           │
                     ┌─────────────────────┴─────────────────────┐
                     ▼                                           ▼
           [No Disruption Detected]                    [Operational Disruption]
                     │                                 (Late Train / Defect / SRS)
                     │                                           │
                     │                                           ▼
                     │                         ┌───────────────────────────────────┐
                     │                         │ Disruption Impact Assessment      │
                     │                         └─────────────────┬─────────────────┘
                     │                                           │
                     │                                           ▼
                     │                         ┌───────────────────────────────────┐
                     │                         │ Multi-Candidate PPO Rescheduler   │
                     │                         └─────────────────┬─────────────────┘
                     │                                           │
                     │                                           ▼
                     │                         ┌───────────────────────────────────┐
                     │                         │ Hard Constraint Safety Guard      │
                     │                         │ (Deterministic Fallback if Fail)  │
                     │                         └─────────────────┬─────────────────┘
                     │                                           │
                     │                                           ▼
                     │                         ┌───────────────────────────────────┐
                     │                         │ Human Approval & Plan Update      │
                     │                         └─────────────────┬─────────────────┘
                     │                                           │
                     └─────────────────────┬─────────────────────┘
                                           │
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │               Field Execution of Block                 │
               │            (Track Possession, Machines, Gangs)         │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │          Outcome Measurement & Variance Capture        │
               │       (Actual vs Planned Duration, Overrun, Delays)    │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │        Closed-Loop Feedback & Adaptive Calibration     │
               │     (Learned Section Buffer Modifiers, Bias Correction)│
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           └──────► (Feeds Future Planning Cycles)
```

---

## 3. Strict Safety Invariants
1. **RL never directly moves railway signals or executes possessions**: RL outputs are candidate proposals.
2. **Safety constraints are external to ML models**: The Hard Constraint Guard operates outside the neural policy.
3. **Deterministic fallback is always guaranteed**: If neural inference encounters any failure, the deterministic engine takes over seamlessly.
4. **Auditability**: Every proposal, acceptance, rejection, and version increment is timestamped and recorded in permanent audit ledgers.
