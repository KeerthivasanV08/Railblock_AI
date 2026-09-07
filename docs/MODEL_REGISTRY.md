# RAILBLOCK AI — PRODUCTION MODEL REGISTRY
**Corridor**: Chennai Egmore → Thoothukudi (Tamil Nadu)  
**Status**: ACTIVE & VERSIONED

---

## 1. Registry Overview
The Model Registry governs machine learning models deployed across RailBlock AI. It ensures that every optimization and rescheduling decision can be traced to a specific algorithm, version, training dataset, feature schema, and validation benchmark.

```python
from app.ml.registry import model_registry

# Inspect all registered models
models = model_registry.list_models()

# Retrieve MDPS metadata
mdps_meta = model_registry.get_mdps_metadata()

# Retrieve PPO Rescheduler metadata
ppo_meta = model_registry.get_ppo_metadata()
```

---

## 2. Registered Model Cards

### Model 1: MDPS Criticality Scorer
- **Model Identifier**: `mdps-v2-sklearn-1.6.1`
- **Algorithm**: Gradient Boosting Regressor (`n_estimators=100`, `learning_rate=0.1`, `max_depth=5`)
- **Artifact Path**: `backend/app/ml/models/mdps_model.pkl` (651 KB)
- **Scaler Path**: `backend/app/ml/models/mdps_scaler.pkl` (711 B)
- **Target Variable**: `actual_priority_rank` $\in [0.0, 100.0]$
- **Feature Schema** (Version: `1358053650c845fc`):
  1. `sev_num`: Numeric severity (A=3, B=2, C=1)
  2. `overdue_days`: Days past maintenance deadline
  3. `traffic_num`: Section traffic density tier (Low=1, Med=2, High=3, Critical Peak=4)
  4. `deferred_count`: Number of prior possession deferrals
- **Training Dataset**: `data/raw/historical/mdps_training_labels.csv` (21,000 training rows, 70/15/15 split)
- **Validation Metrics**:
  - MAE: `2.2861`
  - RMSE: `2.8938`
  - $R^2$: `0.9756`
  - Spearman Rank Correlation: `0.9872`
  - Top 20% Critical Defect Recall: `91.89%`
- **Inference Service**: `app/services/priority/priority_service.py`
- **Production Status**: `ACTIVE`
- **Governance**: Automated priority ranking; human inspection required for final track work permits.

---

### Model 2: PPO Self-Healing Rescheduler
- **Model Identifier**: `ppo_rescheduler_v1`
- **Algorithm**: Proximal Policy Optimization (Actor-Critic Multi-Layer Perceptron)
- **Artifact Path**: `backend/app/ml/models/ppo_rescheduler_v1.pt` (80 KB)
- **Policy Network**:
  - Backbone: `Linear(12, 128) -> Tanh -> Linear(128, 128) -> Tanh`
  - Actor Head: `Linear(128, 5)` (Softmax categorical distribution)
  - Critic Head: `Linear(128, 1)` (State value baseline)
- **Action Space**:
  - 0: `KEEP_SCHEDULE`
  - 1: `DELAY_BLOCK`
  - 2: `SHIFT_TO_LOW_TRAFFIC_WINDOW`
  - 3: `SHORTEN_BLOCK`
  - 4: `CANCEL_CANDIDATE`
- **State Schema** (12-dim continuous normalized vector):
  - `[traffic_density, remaining_window, delay_magnitude, overdue_tasks, machine_available, crew_available, weather_srs, section_vulnerability, asset_type, priority_score, hour_of_day, days_deferred]`
- **Training Environment**: `RailwayDisruptionEnv` (Chennai–Thoothukudi corridor simulation, 198,656 steps)
- **Validation Metrics**:
  - Final Mean Reward (last 100 episodes): `16.345`
  - Inference Latency: `< 1.2 ms` on CPU
- **Inference Service**: `app/services/rescheduler/rescheduler_service.py`
- **Safety Boundary**: **Mandatory HardConstraintGuard validation + mandatory human controller approval**.
- **Production Status**: `ACTIVE`
