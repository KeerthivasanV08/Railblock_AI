# RailBlock AI — Machine Learning & Intelligence Architecture

## Architectural Hierarchy

```
                                  RAILBLOCK AI
                                       |
                   +-------------------+-------------------+
                   |                                       |
                   v                                       v
          MDPS Priority Model                      Spatial Translator
          [Machine Learning: GBR]                  [Deterministic Linear Referencing]
                   |                                       |
                   +-------------------+-------------------+
                                       |
                                       v
                            Shadow Block Clustering
                            [Deterministic Proximity: 2.0 km]
                                       |
                                       v
                           Tripartite Constraint Engine
                           [Deterministic 5-Constraint Filter]
                                       |
                                       v
                                OR-Tools Solver
                           [Mathematical Optimization: MILP]
                                       |
                                       v
                             Disruption Rescheduler
                           [Candidate Policy + Constraint Filter]
                                       |
                                       v
                               Explainable AI (XAI)
                           [Feature Attribution & Reasoning]
                                       |
                                       v
                              Human Controller Gate
                           [Mandatory Operational Approval]
                                       |
                                       v
                             FastAPI & Live WebSockets
```

---

## 1. Machine Learning Layer (MDPS)
- **Model:** `GradientBoostingRegressor` (150 estimators, learning rate 0.08, max depth 4)
- **Features:** `sev_num`, `overdue_days`, `traffic_num`, `deferred_count`
- **Output:** Continuous criticality score $[0, 100]$
- **Inference Mode:** ML inference with deterministic guardrails and automated fallback.

---

## 2. Deterministic Intelligence Layer
- **Spatial Translator:** Linear referencing against OHE masts, signals, and station coordinates.
- **Shadow Block Clustering:** 2.0 km corridor buffer consolidation across civil, signal, and electrical departments.
- **Tripartite Constraint Engine:** Hard rejection of infeasible windows (traffic density $\ge 0.85$, missing machine, missing crew, duration $> 240$ min, unmapped coordinates).

---

## 3. Mathematical Optimization Layer
- **OR-Tools Solver:** SCIP/CBC Mixed-Integer Linear Program.
- **Objective:** Maximizes total priority score and consolidation bonus while penalizing passenger train delay minutes.

---

## 4. Disruption Rescheduling & Self-Healing
- **Candidate Generator:** Evaluates Delay ($+2$ hr), Shift (night window), and Reallocate (next-day mega-block) options.
- **Constraint Filter:** Rejects infeasible options before ranking.
- **Human-in-the-Loop:** Plan updates strictly require controller confirmation.

---

## 5. Artifact Directory Layout

```
backend/app/ml/models/
├── mdps_model.pkl                 # Runtime ML model
├── mdps_scaler.pkl                # Runtime feature scaler
├── mdps_feature_metadata.json     # Feature schema & mappings
└── mdps_feature_importance.json   # Feature importances for XAI
```
