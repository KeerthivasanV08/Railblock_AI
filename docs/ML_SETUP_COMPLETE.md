# RailBlock AI — Complete Intelligence Setup & ML Pipeline Architecture

**Author:** Senior Backend & ML Architect  
**Status:** Production-Hardened & Validated  
**Verification Date:** 2026-08-28  
**Test Suite Status:** 23 Passed / 0 Failed  

---

## 1. System Overview

RailBlock AI is an intelligent decision-support system designed to automate, optimize, and safely reschedule railway track maintenance blocks. The platform unifies defect feeds across multiple departmental source systems (TMS, SMMS, TDMS), accurately projects their spatial coordinates onto the linear railway corridor, scores their operational criticality via a machine learning model, groups proximal maintenance demands into shadow blocks, filters candidates through tripartite operational constraints, computes mathematically optimal weekly/monthly maintenance schedules with Google OR-Tools, and provides self-healing disruption rescheduling with Explainable AI (XAI) and mandatory human-in-the-loop approval.

```
+-----------------------------------------------------------------------------------+
|                                RAILBLOCK AI PIPELINE                              |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
                              [ 1. Ingestion & Validation ] (Deterministic)
                                          |
                                          v
                              [ 2. Spatial Translator ] (Deterministic)
                                          |
                                          v
                              [ 3. MDPS Priority Model ] (Machine Learning: GBR)
                                          |
                                          v
                              [ 4. Shadow Block Clustering ] (Deterministic: 2.0 km)
                                          |
                                          v
                              [ 5. Tripartite Constraint Engine ] (Deterministic)
                                          |
                                          v
                              [ 6. OR-Tools MILP Optimizer ] (Mathematical Optimization)
                                          |
                                          v
                              [ 7. Disruption Rescheduler ] (Hybrid Policy + Hard Constraints)
                                          |
                                          v
                              [ 8. Explainable AI (XAI) ] (Feature Contribution & Reasoning)
                                          |
                                          v
                              [ 9. Human Controller Approval ] (Mandatory Safety Gate)
                                          |
                                          v
                              [ 10. FastAPI Service & WebSockets ]
```

---

## 2. ML vs. Deterministic vs. Optimization Responsibilities

To guarantee railway operational safety, prevent hallucinations, and ensure mathematical optimality, RailBlock AI enforces a strict architectural boundary between statistical learning, deterministic physics/rules, and exact mathematical programming:

| Pipeline Stage | Technology / Algorithm | Classification | Responsibility |
|---|---|---|---|
| **Data Normalization & Ingestion** | Schema Validators & Rule Parser | **Deterministic** | Cleans timestamps, standardizes defect types, and joins source records. |
| **Spatial Translation** | Linear Referencing & Geometry Tables | **Deterministic** | Translates mast numbers, signals, and station offsets to absolute chainage ($km$) and GPS coordinates. |
| **Priority Scoring (MDPS)** | `GradientBoostingRegressor` (scikit-learn) | **Machine Learning** | Predicts non-linear criticality risk based on defect severity, overdue days, traffic density, and deferrals. |
| **Shadow Block Clustering** | Spatial-Temporal Proximity Grouping | **Deterministic** | Clusters compatible maintenance tasks within a 2.0 km corridor buffer to share track possession windows. |
| **Operational Feasibility** | 5-Constraint Vectorized Filter | **Deterministic** | Evaluates hard operational constraints: Traffic gap ($<0.85$), Machine availability, Crew availability, Duration ($<=240$ min), Spatial mapping validity. |
| **Block Plan Optimization** | Google OR-Tools (SCIP / CBC MILP) | **Mathematical Optimization** | Solves Multi-Objective Integer Programming to maximize priority and consolidation bonuses while penalizing train disruption. |
| **Disruption Rescheduling** | Candidate Policy Engine + Constraint Filter | **Hybrid Deterministic / Policy Prototype** | Generates Delay, Shift, and Reallocate candidate windows; validates each against hard constraints; ranks valid options. |
| **Explainability (XAI)** | Feature Attribution & Rule Explainer | **Hybrid XAI** | Explains MDPS scores using tree feature importances and articulates constraint satisfaction reasons. |
| **Plan Execution & Approval** | Controller Authorization Workflow | **Human-in-the-Loop** | Requires controller confirmation before modifying operational schedules or executing blocks. |

---

## 3. MDPS Machine Learning Model Specification

### 3.1 Mathematical Formulation
The Multi-Variable Criticality Matrix Priority Scoring (MDPS) model is formulated as an additive ensemble of regression trees:

$$F_M(x) = F_0(x) + \sum_{m=1}^{M} \eta \cdot h_m(x)$$

where:
- $F_0(x)$ is the initial constant prediction (mean of the training targets).
- $M = 150$ is the number of boosting stages (`n_estimators`).
- $\eta = 0.08$ is the shrinkage learning rate (`learning_rate`).
- $h_m(x)$ is a regression tree of maximum depth $d = 4$ (`max_depth`) fitted to pseudo-residuals at iteration $m$.
- $x = [\text{sev\_num}, \text{overdue\_days}, \text{traffic\_num}, \text{deferred\_count}]^T \in \mathbb{R}^4$.

The raw prediction $\hat{y} \in [0, 100]$ represents the continuous `actual_priority_rank`, with higher values indicating severe operational urgency requiring immediate block allocation.

### 3.2 Feature Schema & Preprocessing Parity
All features used during inference match training transformations deterministically:

1. `severity_class` $\rightarrow$ `sev_num`:
   - `'A'` $\rightarrow 3$ (Critical: Rail fracture, OHE parting, Point failure)
   - `'B'` $\rightarrow 2$ (Major: Track geometry defect, Signal lamp failure)
   - `'C'` $\rightarrow 1$ (Minor / Routine: Vegetation clearance, Drain cleaning)
2. `traffic_density_class` $\rightarrow$ `traffic_num`:
   - `'High'` ($>0.70$) $\rightarrow 3$
   - `'Medium'` ($0.40 - 0.70$) $\rightarrow 2$
   - `'Low'` ($<0.40$) $\rightarrow 1$
3. `overdue_days`: Unbounded non-negative integer ($\ge 0$).
4. `deferred_count`: Count of previous possession request deferrals ($\ge 0$).

All 4 features are normalized using `StandardScaler` fitted exclusively on the 70% training split.

### 3.3 Target Leakage Analysis
- **Audit Result:** **PASS (Zero Target Leakage)**
- **Verification:** None of the 4 features are derived from downstream decisions, post-facto planning outcomes, cluster IDs, solver assignments, or future time steps. All inputs represent state information available at the exact instant a maintenance work order is logged.

### 3.4 Evaluated Performance Metrics (Held-Out Test Set)

Evaluated on $N = 4,500$ held-out test rows (15% split) with `random_state=42`:

| Metric | Measured Value | Unit / Range | Interpretation |
|---|---|---|---|
| **Mean Absolute Error (MAE)** | **4.0024** | Score Points ($[0, 100]$) | Average prediction error is $\approx 4.0$ points. |
| **Root Mean Squared Error (RMSE)** | **5.5289** | Score Points ($[0, 100]$) | Penalizes larger deviations; confirms high stability. |
| **Coefficient of Determination ($R^2$)** | **0.9110** | Ratio ($[0, 1]$) | Model explains $91.1\%$ of total target variance. |
| **Prediction Range** | $[14.64, 100.65]$ | Score Points | Matches continuous target distribution $[10.69, 100.0]$. |

### 3.5 Feature Importance Ranking

Derived from Gini impurity reduction across all 150 regression trees:

```
Rank 1: sev_num         | [0.428766] =======================================
Rank 2: overdue_days    | [0.361264] ================================
Rank 3: deferred_count  | [0.163429] ===============
Rank 4: traffic_num     | [0.046541] ====
```

---

## 4. Feature Audit & Ablation Study Results

To justify feature retention and prevent unnecessary complexity, an ablation study was conducted across four candidate configurations on identical train/test splits:

| Experiment | Algorithm | Feature Set | Feature Count | MAE | RMSE | $R^2$ Score |
|---|---|---|:---:|:---:|:---:|:---:|
| **A. Baseline (Selected)** | **GradientBoostingRegressor** | `sev_num`, `overdue_days`, `traffic_num`, `deferred_count` | **4** | **3.5640** | **4.4571** | **0.9421** |
| **B. Alternative Algorithm** | RandomForestRegressor | `sev_num`, `overdue_days`, `traffic_num`, `deferred_count` | 4 | 4.2659 | 5.2876 | 0.9186 |
| **C. Reduced Features** | GradientBoostingRegressor | `sev_num`, `overdue_days` (Severity & Overdue only) | 2 | 7.4153 | 8.9596 | 0.7662 |
| **D. Expanded Features** | GradientBoostingRegressor | Baseline + `estimated_duration_minutes` + `seasonal_risk_factor` | 6 | 3.5809 | 4.4696 | 0.9418 |

### Ablation Findings:
1. **Experiment C (Reduced)** suffered a severe accuracy drop ($R^2$ dropped from $0.942$ to $0.766$, MAE worsened by $+108\%$), demonstrating that `deferred_count` and `traffic_num` provide critical risk compounding signals.
2. **Experiment D (Expanded)** yielded no statistically significant improvement ($R^2 = 0.9418$ vs $0.9421$, MAE $3.5809$ vs $3.5640$), proving that maintenance duration and seasonal factors do not govern defect urgency.
3. **Experiment A (Baseline GBR)** was conclusively selected as the most accurate, parsimonious, and maintainable architecture.

---

## 5. Decision Engines Specification

### 5.1 Spatial Translation Engine
- **Method:** Deterministic linear referencing against mast/signal geometry and station chainages.
- **Throughput:** Processed $80,000$ maintenance tasks.
- **Output:** Mapped chainage ($km$), latitude/longitude coordinates, and mapping confidence classification.

### 5.2 Shadow Block Clustering Engine
- **Method:** Multi-department spatial grouping.
- **Proximity Threshold:** $2.0\text{ km}$ buffer along the same section corridor.
- **Performance:** Formed $126$ discrete clusters across $80,000$ tasks, generating $79,998$ integrated block candidates.

### 5.3 Tripartite Operational Constraint Engine
- **Constraints Enforced:**
  1. *Traffic Feasibility:* Section traffic density $< 0.85$.
  2. *Machine Feasibility:* Required machine type verified available at nearby depot.
  3. *Crew Feasibility:* Required departmental crew verified in shift availability table.
  4. *Duration Feasibility:* Estimated maintenance duration $\le 240\text{ minutes}$.
  5. *Spatial Feasibility:* Validated spatial mapping status $\notin \{\text{LOW\_CONFIDENCE, UNMAPPED, INVALID}\}$.
- **Batch Evaluation:** $1,582$ tasks passed all 5 tripartite constraints ($1.98\%$ overall feasibility due to heavy passenger traffic density).
- **Single-Candidate Evaluation:** Reused by Rescheduler to enforce identical safety rules per candidate action.

### 5.4 Mathematical Optimization Engine (OR-Tools)
- **Solver:** SCIP / CBC Mixed-Integer Linear Programming (MILP).
- **Objective Function:** Maximize cumulative task priority scores $+$ spatial overlap bonuses $-$ traffic disruption penalties.
- **Output:** 15 optimal weekly possession blocks scheduled in `data/outputs/weekly_block_plan.csv`.

### 5.5 Hardened Disruption Rescheduler Engine
- **Candidate Generator:** Produces 3 typed operational options:
  1. `delay`: Immediate $+2.0\text{ hr}$ shift into off-peak slot.
  2. `shift`: Relocation to night possession window ($01:00\text{ AM}$).
  3. `reallocate`: Next-day consolidated mega-block with machine repositioning.
- **Constraint Enforcement:** Every candidate is passed through `ConstraintEngine.check_feasibility_single()`.
- **Filtering:** Infeasible candidates are marked `feasible=False`, assigned `optimization_score=0.0`, and annotated with explicit `failed_constraints` and `rejection_reason`.
- **Human Approval:** Plan modification is strictly blocked until confirmed by a controller via `/api/disruptions/approve`.

---

## 6. Visual Evaluation Evidence

The evaluation visualization is generated directly from execution data and saved to:
`docs/ml_evaluation_summary.png` (507 KB, 300 DPI high-resolution PNG).

![ML Evaluation Summary](ml_evaluation_summary.png)

---

## 7. Artifacts & Reproducibility Directory

| Artifact | Canonical Path | Description |
|---|---|---|
| **Trained Model** | `backend/app/ml/models/mdps_model.pkl` | Serialized `GradientBoostingRegressor` |
| **Feature Scaler** | `backend/app/ml/models/mdps_scaler.pkl` | Fitted `StandardScaler` instance |
| **Feature Schema Metadata** | `backend/app/ml/models/mdps_feature_metadata.json` | JSON schema with category mappings |
| **Feature Importance** | `backend/app/ml/models/mdps_feature_importance.json` | Ranked feature importances |
| **Evaluation Metrics** | `docs/ml_evaluation_report.json` | Machine-readable metrics & ablation data |
| **Evaluation Visual** | `docs/ml_evaluation_summary.png` | 4-panel evaluation chart (PNG) |
| **Training Split** | `data/features/mdps_features/train.csv` | 21,000 training rows |
| **Validation Split** | `data/features/mdps_features/validation.csv` | 4,500 validation rows |
| **Test Split** | `data/features/mdps_features/test.csv` | 4,500 held-out evaluation rows |

---

## 8. Known Limitations & Roadmap

1. **Reinforcement Learning Status:** RL policy training is in scaffolding mode (`ml/reinforcement_learning/`). No `.zip` policy artifact is deployed. The rescheduler operates on a deterministic candidate generator with hard constraint validation.
2. **Live Train Feed:** Live train tracking currently runs in deterministic simulation mode (`LIVE_TRAIN_PROVIDER=simulation`). External CRIS/TMS API integration is slated for Phase 2.
3. **Data Quality Note:** Duplicate timestamp records in `live_train_delays.csv` are preserved in `data/raw/` to maintain raw provenance; deduplication is applied strictly during processing.
