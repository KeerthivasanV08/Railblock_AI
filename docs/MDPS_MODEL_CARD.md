# MDPS Priority Model Card

## Model Overview
- **Model Name:** Multi-Variable Criticality Matrix Priority Scoring (MDPS)
- **Model Type:** `GradientBoostingRegressor` (scikit-learn)
- **Version:** `1.1.0`
- **Domain:** Railway Track Maintenance Decision Support
- **Task:** Predict continuous maintenance urgency score / priority rank ($[0, 100]$) from defect attributes and track conditions.

---

## Intended Use
- **Primary Use:** Automated ranking and prioritization of incoming civil, signal, and electrical track defects for block planning.
- **Out-of-Scope Use:** Direct real-time train movement dispatching without human controller supervision.

---

## Model Architecture & Hyperparameters
- **Ensemble Algorithm:** Gradient Boosting Decision Trees (`GradientBoostingRegressor`)
- **Number of Estimators ($M$):** `150`
- **Learning Rate ($\eta$):** `0.08`
- **Maximum Tree Depth ($d$):** `4`
- **Loss Function:** Squared Error (MSE)
- **Random Seed:** `42`
- **Feature Normalization:** `StandardScaler` fitted on training split only.

---

## Feature Schema & Transformations

| Feature Name | Source Column | Type | Encoding / Mapping |
|---|---|---|---|
| `sev_num` | `severity_class` | Integer | `'A' -> 3` (Critical), `'B' -> 2` (Major), `'C' -> 1` (Minor) |
| `overdue_days` | `overdue_days` | Integer | Pass-through non-negative integer ($\ge 0$) |
| `traffic_num` | `traffic_density_class` | Integer | `'High' -> 3`, `'Medium' -> 2`, `'Low' -> 1` |
| `deferred_count` | `deferred_count` | Integer | Pass-through integer ($\ge 0$) |

---

## Evaluated Metrics (Held-Out Test Split, N = 4,500)

- **Mean Absolute Error (MAE):** `4.0024`
- **Root Mean Squared Error (RMSE):** `5.5289`
- **Coefficient of Determination ($R^2$):** `0.9110`
- **Prediction Bounds:** `[14.64, 100.65]`
- **Target Bounds:** `[10.69, 100.00]`

---

## Feature Importance

1. `sev_num`: **0.4288** (Primary driver)
2. `overdue_days`: **0.3613** (Urgency escalation)
3. `deferred_count`: **0.1634** (Compounding risk)
4. `traffic_num`: **0.0465** (Track occupancy pressure)

---

## Target Leakage Audit
- **Status:** **PASS**
- Verified that all features represent pre-planning operational variables. Zero downstream optimization or planning decisions are present in the feature vector.

---

## Fallback & Operational Resilience
If model artifacts are missing or fail to load, `MDPSEngine` automatically reverts to deterministic weighted matrix scoring:
- `scoring_mode`: `"deterministic_fallback"`
- `model_available`: `false`
- `fallback`: `true`

---

## Artifact Locations
- **Model:** `backend/app/ml/models/mdps_model.pkl`
- **Scaler:** `backend/app/ml/models/mdps_scaler.pkl`
- **Metadata:** `backend/app/ml/models/mdps_feature_metadata.json`
- **Visual Report:** `docs/ml_evaluation_summary.png`
