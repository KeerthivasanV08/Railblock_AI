# MDPS Priority Model Card

## Model Overview
- **Model Name:** Multi-Variable Criticality Matrix Priority Scoring (MDPS)
- **Model Version:** `v2_weather_enabled`
- **Model Type:** `GradientBoostingRegressor` (scikit-learn)
- **Domain:** Railway Track Maintenance Decision Support
- **Task:** Predict continuous maintenance urgency score / priority rank ($[0, 100]$) from defect attributes, track conditions, and seasonal/weather intelligence.
- **Artifact:** `backend/app/ml/models/mdps_model.pkl` (also `data/models/mdps_model.pkl`)
- **Scaler Artifact:** `backend/app/ml/models/mdps_scaler.pkl`
- **Metadata:** `backend/app/ml/models/mdps_feature_metadata.json`

---

## Intended Use
- **Primary Use:** Automated ranking and prioritization of incoming civil, signal, and electrical track defects for block planning and candidate clustering.
- **Out-of-Scope Use:** Direct real-time train movement dispatching without human controller supervision.
- **Governance:** Human-in-the-Loop decision support only. AI-generated priority scores feed the MILP optimizer and provide explainability justifications; they do not autonomously authorize track possession.

---

## Data Provenance & Disclosure

> [!WARNING]
> **Synthetic Benchmark Evaluation:** Training labels and defect records are **calibrated synthetic data** modeled on Indian Railways maintenance policies (CAG Report 45 benchmarks, Indian Railways Permanent Way Manual, and Southern Railway corridor topology). Evaluation metrics reflect accuracy on synthetic benchmark data, **not** live Indian Railways operational records.

| Property | Value |
|---|---|
| Training Set | 21,000 synthetic task records |
| Validation Set | 4,500 synthetic task records |
| Test Set | 4,500 synthetic task records |
| Data Provenance | Calibrated synthetic maintenance demands with authentic corridor topology |
| Ground-Truth Basis | Derived from severity class, overdue days, traffic density, deferral count, and seasonal risk score |

---

## Feature Schema (8 Features)

| Feature Name | Source Column | Type | Encoding / Mapping |
|---|---|---|---|
| `sev_num` | `severity_class` | Integer | `'A' -> 3` (Critical), `'B' -> 2` (Major), `'C' -> 1` (Minor) |
| `overdue_days` | `overdue_days` | Float | Non-negative numeric days since scheduled inspection/maintenance |
| `traffic_num` | `traffic_density_class` | Integer | `'Critical Peak' -> 4`, `'High' -> 3`, `'Medium' -> 2`, `'Low' -> 1` |
| `deferred_count` | `deferred_count` | Float | Number of times maintenance window was previously requested but deferred |
| `seasonal_risk_score` | `srs` / `seasonal_risk_score` | Float | Normalized corridor section seasonal risk score $[0.0, 1.0]$ |
| `live_weather_risk_score` | `live_weather_severity` | Float | Normalized live weather telemetry severity $[0.0, 1.0]$ |
| `weather_maintenance_suitability` | Derived formula | Float | Maintenance suitability factor: $\max(0, 1.0 - [0.4 \times \text{SRS} + 0.6 \times \text{LWR}])$ |
| `task_weather_sensitivity` | `department` / `asset_type` | Float | Asset weather multiplier: Track = 1.0, Signal = 1.1, OHE/TRD = 1.3 |

---

## Evaluated Metrics (Synthetic Benchmark Test Split, N = 4,500)

| Metric | Value | Interpretation |
|---|---|---|
| **Mean Absolute Error (MAE)** | `2.2861` | Average point deviation on a 0–100 priority scale |
| **Root Mean Squared Error (RMSE)** | `2.8938` | Penalizes large priority ranking deviations |
| **Coefficient of Determination ($R^2$)** | `0.9756` | Model accounts for 97.6% of variance in calibrated priority scores |
| **Spearman Rank Correlation** | `0.9872` | Monotonic ranking consistency across candidate maintenance tasks |
| **Top-20% Critical Recall** | `0.9189` | 91.9% of top-quintile emergency defects correctly placed in top band |

---

## Deterministic Guardrails & Fallback
If model artifacts are missing or unpickling fails due to library version differences, the backend automatically transitions to `deterministic_mdps` fallback mode:
$$\text{Priority}_{\text{det}} = 0.40 \cdot \text{sev} + 0.30 \cdot \min(100, \text{overdue} \times 2) + 0.20 \cdot \text{traffic} + 0.10 \cdot \min(100, \text{deferred} \times 10)$$
The system reports `scoring_mode: "deterministic_mdps"` in the response payload without crashing.
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
