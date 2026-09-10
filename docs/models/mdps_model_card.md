# MDPS Model Card — RailBlock AI

**Model Name:** MDPS (Multi-Variable Criticality Matrix Priority Scoring Engine)  
**Model Version:** `mdps-v2-weather-enabled`  
**Artifact:** `data/models/mdps_model.pkl`  
**Scaler Artifact:** `data/models/mdps_scaler.pkl`  
**Metadata:** `data/models/mdps_feature_metadata.json`  
**Training Timestamp:** 2026-09-10T20:20:04.735053 (UTC)

---

## Model Purpose

Predicts maintenance task criticality priority rank (0–100 scale) to enable the MILP optimizer to allocate maintenance blocks to highest-risk track sections first.

This is a **decision-support model**. Its output feeds MILP optimization and requires human approval for final block authorization. The model does **not** directly authorize maintenance actions.

---

## Data Provenance

> **⚠️ IMPORTANT:** Training labels are **synthetic** and generated to demonstrate planning intelligence. They are **not** actual Indian Railways maintenance priority records.

| Property | Value |
|----------|-------|
| Training set | 21,000 synthetic task records |
| Validation set | 4,500 synthetic task records |
| Test set | 4,500 synthetic task records |
| Data provenance | Synthetic training labels grounded in railway planning engineering concepts |
| Dataset hash (SHA256) | `f65635bda417398e...` |
| Label source | Derived from severity class, overdue days, traffic density, deferral count |

---

## Feature Schema (8 features)

| Feature | Type | Range | Description |
|---------|------|-------|-------------|
| `sev_num` | int | 1–3 | Severity class encoding: A=3, B=2, C=1 |
| `overdue_days` | float | 0–∞ | Days since maintenance was due |
| `traffic_num` | int | 1–4 | Traffic density encoding: Low=1, Medium=2, High=3, Critical Peak=4 |
| `deferred_count` | float | 0–∞ | Number of times task was previously deferred |
| `seasonal_risk_score` | float | 0.0–1.0 | Normalized SRS (÷100) |
| `live_weather_risk_score` | float | 0.0–1.0 | Normalized live weather severity |
| `weather_maintenance_suitability` | float | 0.0–1.0 | `1 - combined_risk` |
| `task_weather_sensitivity` | float | 1.0–1.3 | Asset type weather sensitivity multiplier |

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| MAE | 2.2861 |
| RMSE | 2.8938 |
| R² | 0.9756 |
| Spearman Rank Correlation | 0.9872 |
| Top-20% Critical Recall | 0.9189 |

---

## Ablation Study

| Configuration | MAE | RMSE | R² |
|--------------|-----|------|-----|
| Baseline (4 features) | 2.2861 | 2.8938 | 0.9756 |
| Weather-enabled (8 features) | 2.2861 | 2.8938 | 0.9756 |
| **Delta** | **0.0** | **0.0** | **0.0** |

**Analysis:** Weather features have zero measured predictive uplift on the current synthetic dataset. This is expected: synthetic labels were generated primarily from the 4 base features. Weather features are architecturally integrated for live signal enrichment but require a dataset where weather genuinely correlates with maintenance priority to demonstrate measurable uplift.

**Feature Importance (from trained model):**

| Feature | Importance |
|---------|-----------|
| `sev_num` | 0.4288 |
| `overdue_days` | 0.3613 |
| `deferred_count` | 0.1634 |
| `traffic_num` | 0.0465 |
| `seasonal_risk_score` | **0.000** |
| `live_weather_risk_score` | **0.000** |
| `weather_maintenance_suitability` | **0.000** |
| `task_weather_sensitivity` | **0.000** |

---

## Runtime Behavior

- ML inference requires preprocessed input (columns: `severity_class`, `overdue_days`, `deferred_count`)
- Falls back to deterministic MDPS formula when input lacks required columns
- Deterministic fallback produces valid scores and is used as safety guardrail
- Scoring mode reported in API response: `ml_artifact_available_with_deterministic_guardrail`

---

## Algorithm

**GradientBoostingRegressor** (scikit-learn 1.6.1)  
Random seed: 42

---

## Limitations

1. Zero weather feature importance — needs dataset with real weather-correlated maintenance urgency
2. Row-by-row inference is slow (~370 tasks/sec) — vectorized batch inference recommended
3. Trained on synthetic labels — not validated against actual IR priority records
