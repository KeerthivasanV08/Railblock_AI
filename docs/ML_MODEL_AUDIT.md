# RAILBLOCK AI — MACHINE LEARNING MODEL AUDIT
**Corridor**: Chennai Egmore → Thoothukudi (Tamil Nadu)  
**Author**: RailBlock AI Core Systems Architecture Team  
**Status**: AUDITED & VERIFIED

---

## 1. Model Inventory & Production Status

| Model Name | Version | Purpose | Algorithm | Artifact Path | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MDPS Scorer** | `mdps-v2-sklearn-1.6.1` | Task Criticality Scoring (0-100) | GradientBoostingRegressor | `backend/app/ml/models/mdps_model.pkl` | **ACTIVE** |
| **PPO Rescheduler** | `ppo_rescheduler_v1` | Autonomous Candidate Rescheduling | Actor-Critic MLP (PyTorch) | `backend/app/ml/models/ppo_rescheduler_v1.pt` | **ACTIVE** |
| **Seasonal Risk Engine** | `srs-v1.2` | Weather Risk Scoring & Hazard Gate | Analytical Multi-Factor Formulations | `app/services/engines/seasonal_risk_engine.py` | **ACTIVE** |
| **Hard Constraint Guard** | `guard-v1.1` | Non-Negotiable Operational Safety Boundary | Deterministic Rule Gating | `app/services/rescheduler/hard_constraint_guard.py` | **ACTIVE** |

---

## 2. MDPS (Multi-Variable Criticality Matrix) Model Audit

### Formula & Ground Truth Label Generation
$$\text{MDPS} = \min\left(100, \left(1.2 \cdot S + 8.0 \cdot \ln(1 + D_{\text{overdue}}) + 15.0 \cdot T_{\text{density}}\right) \times (1 + 0.25 \cdot N_{\text{deferred}})\right)$$
Where:
- $S \in \{40 (\text{Class A}), 25 (\text{Class B}), 10 (\text{Class C})\}$
- $D_{\text{overdue}}$: Overdue days
- $T_{\text{density}} \in [0.0, 1.0]$: Corridor traffic density
- $N_{\text{deferred}}$: Prior deferral count

### Verified Baseline Metrics (Zero Data Leakage Split)
- **Training Set**: 21,000 rows (70%)
- **Validation Set**: 4,500 rows (15%)
- **Test Set**: 4,500 rows (15%)
- **MAE**: `2.2861`
- **RMSE**: `2.8938`
- **$R^2$**: `0.9756`
- **Spearman Rank Correlation**: `0.9872`
- **Top 20% Critical Recall**: `91.89%`

### Feature Importance
1. `sev_num` (Severity Class): 42.88%
2. `overdue_days` (Overdue Days): 36.13%
3. `deferred_count` (Prior Deferrals): 16.34%
4. `traffic_num` (Section Density): 4.65%

---

## 3. PPO Rescheduler Policy Audit

### Architecture & Training
- **Framework**: PyTorch (CPU-optimized inference, weights_only compatible)
- **Network**: Shared MLP Backbone (`Linear(12, 128) -> Tanh -> Linear(128, 128) -> Tanh`)
  - Actor Head: `Linear(128, 5)` (Softmax categorical distribution)
  - Critic Head: `Linear(128, 1)` (State value baseline)
- **Training Steps**: 198,656 timesteps in `RailwayDisruptionEnv`
- **Final Mean Reward (last 100 episodes)**: `16.345`
- **Latency**: `< 1.2 ms` per inference step on standard CPU.

### Feature Schema Compatibility
Verified exact matching of 12-dimensional continuous features between environment (`state.py`) and inference (`rescheduler_service.py`):
1. `traffic_density`: $[0.0, 1.0]$
2. `remaining_window / 240.0`: $[0.0, 1.5]$
3. `delay_magnitude / 120.0`: $[0.0, 2.0]$
4. `overdue_tasks / 10.0`: $[0.0, 2.0]$
5. `machine_available`: $\{0.0, 1.0\}$
6. `crew_available`: $\{0.0, 1.0\}$
7. `weather_risk_score / 100.0`: $[0.0, 1.0]$
8. `section_vulnerability`: $[0.0, 1.0]$
9. `asset_type_code`: $\{0.0 (\text{Track}), 0.5 (\text{Signal}), 1.0 (\text{OHE})\}$
10. `priority_score / 100.0`: $[0.0, 1.0]$
11. `hour_of_day / 24.0`: $[0.0, 1.0]$
12. `days_deferred / 5.0`: $[0.0, 2.0]$
