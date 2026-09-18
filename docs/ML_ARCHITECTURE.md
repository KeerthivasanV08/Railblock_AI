# RailBlock AI — Machine Learning & Intelligence Architecture

## Architectural Hierarchy

```
                                  RAILBLOCK AI INTELLIGENCE
                                              │
                    ┌─────────────────────────┴─────────────────────────┐
                    │                                                   │
                    ▼                                                   ▼
         MDPS Priority Engine                                Spatial Translator
       [ML: GradientBoostingRegressor]                    [Linear Referencing Engine]
       (8 features: 4 base + 4 weather)                 (Continuous Chainage Km 0.0-648.2)
                    │                                                   │
                    └─────────────────────────┬─────────────────────────┘
                                              │
                                              ▼
                                 Shadow Block Clustering
                           [Spatial Proximity: 2.0 km Buffer]
                                              │
                                              ▼
                                 Seasonal Risk Engine (SRS)
                        [Layer A: Climatology + Layer B: Telemetry]
                                              │
                                              ▼
                                Tripartite Constraint Engine
                          [Hard Operational & Safety Filters: 6 Gates]
                          (Traffic, Resource, Crew, Duration, Space, Weather)
                                              │
                                              ▼
                                       OR-Tools Solver
                             [Mathematical Optimization: MILP]
                          (Consolidation, Asset Availability, Uptime)
                                              │
                                              ▼
                                  Multi-Horizon Scheduler
                                (Weekly, Monthly, 26-Week Rolling)
                                              │
                                              ▼
                                   Explainable AI (XAI)
                             [Feature Attribution & Reasoning]
                                              │
                                              ▼
                                 Human Controller Governance
                             [Mandatory Operational Decision Gate]
                                  (Approve / Modify / Reject)
                                              │
                                              ▼
                                  Field Execution Monitor
                               (Outcome Recording: COMPLETED/PARTIAL)
                                              │
                                              ▼
                                Disruption Detector & Rescheduler
                           [Self-Healing: PPO Policy Proposal +
                            HardConstraintGuard + Deterministic Fallback]
```

---

## 1. Machine Learning Prioritization Layer (MDPS v2)
- **Model Type:** `GradientBoostingRegressor` (scikit-learn)
- **Artifact:** `backend/app/ml/models/mdps_model.pkl` (scaler: `mdps_scaler.pkl`)
- **Features (8 total):**
  1. `sev_num`: Track defect severity class (A=3, B=2, C=1)
  2. `overdue_days`: Elapsed days past scheduled maintenance window
  3. `traffic_num`: Section traffic density class (1 to 4)
  4. `deferred_count`: Prior deferral count for maintenance demand
  5. `seasonal_risk_score`: Climatological section vulnerability $[0.0, 1.0]$
  6. `live_weather_risk_score`: Normalized live weather telemetry severity $[0.0, 1.0]$
  7. `weather_maintenance_suitability`: Combined weather suitability index $[0.0, 1.0]$
  8. `task_weather_sensitivity`: Asset-specific weather multiplier (Track: 1.0, S&T: 1.1, OHE/TRD: 1.3)
- **Evaluation on Calibrated Synthetic Benchmark:** $R^2 = 0.9756$, $\text{MAE} = 2.2861$, $\text{RMSE} = 2.8938$.
- **Deterministic Guardrail:** Automatic fallback to `deterministic_mdps` rule if artifact is unpickled with runtime version mismatch.

---

## 2. Seasonal Intelligence & Live Weather Architecture
- **SeasonalRiskEngine (`backend/app/engines/seasonal_risk_engine.py`):**
  - **Layer A (Climatological):** Historical Tamil Nadu seasonal cycles (Winter, Summer, SW Monsoon, NE Cyclone Season) combined with terrain vulnerability profiles for all 68 corridor sections.
  - **Layer B (Live Telemetry):** Ingests real-time/simulated weather metrics (rainfall mm, wind speed km/h, ambient temperature °C) via `LiveWeatherService`.
  - **Task-Aware Formula:**
    $$\text{SRS} = \min\left(100.0, \left(w_s \cdot S_{\text{season}} + w_v \cdot V_{\text{vuln}} + w_l \cdot L_{\text{live}}\right) \times M_{\text{asset}}\right)$$
  - **Hard Safety Exclusion:** Any candidate block with $\text{SRS} \ge 75.0$ is strictly barred by the constraint engine from execution during severe weather conditions.
  - **Resilient Fallback:** If live weather telemetry is unavailable (`UNKNOWN`), weights are rescaled over climatological components ($w_s, w_v$) without defaulting severity to zero.

---

## 3. Mathematical Optimization Layer (OR-Tools MILP)
- **Solvers:** SCIP / CBC via Google OR-Tools `pywraplp`.
- **Objective Function:**
  $$\max \sum_{b \in \mathcal{B}} \left( W_{\text{priority}} \cdot P_b + W_{\text{consol}} \cdot C_b + W_{\text{util}} \cdot U_b - W_{\text{delay}} \cdot D_b - W_{\text{weather}} \cdot \text{SRS}_b \right) \cdot x_b$$
- **Operational Constraints:**
  - Max simultaneous blocks per section / corridor division
  - Track maintenance crew and heavy machine inventory bounds (BCM, Tamping, Tower Wagon)
  - Train headway clearance and passenger timetable protection windows
  - Multi-department consolidation synergy bonus

---

## 4. Multi-Horizon Planning & Dynamic Progression
- **Weekly Horizon:** 7-day tactical operational schedule with hourly slotting.
- **Monthly Horizon:** 4-week dynamic progressive schedule:
  - Cumulative task carry-forward with overdue escalation ($D_0 + 7(w-1)$)
  - Progressive deferral counter incrementing
  - Cyclic ultrasonic flaw testing (USFD) injection at Week 4
  - Seasonal risk modulation across weeks
- **26-Week Rolling Horizon:** Strategic machine overhaul and corridor-wide cyclic possession scheduling.
- **Multi-Horizon Synchronization:** Dual-key matching (`block_id` or `task_ids`) ensures status and version synchronization across Weekly, Monthly, and Rolling plans.

---

## 5. Self-Healing Rescheduling Layer (PPO + Deterministic Fallback)
- **RL Agent:** Proximal Policy Optimization (`ppo_rescheduler_v1.pt`, trained for 198,656 timesteps in offline simulation).
- **Environment:** `RailwayDisruptionEnv` with 12-dimensional continuous state vector and 5 discrete actions (`KEEP_SCHEDULE`, `DELAY_BLOCK`, `MOVE_BLOCK`, `SHORTEN_BLOCK`, `CANCEL_CANDIDATE`).
- **HardConstraintGuard:** Every action proposal is checked against 5 hard operational constraints (traffic density, weather exclusion, duration feasibility, machine availability, crew availability).
- **Deterministic Policy Fallback:** If RL inference is disabled or fails, `PolicyEngine` deterministically generates, scores, and ranks Delay/Shift/Reallocate candidates.
- **Explainability:** `ExplainabilityService` computes feature attribution breakdowns and natural-language justifications for each proposed option.

---

## 6. Human-in-the-Loop Operational Safety Principle

> [!IMPORTANT]
> **No Autonomous Execution:** Neither the MDPS model, the MILP optimizer, nor the PPO rescheduler has the authority to directly execute schedule modifications on railway infrastructure.
> 
> $\text{AI Recommends} \longrightarrow \text{Human Review} \longrightarrow \text{Controller Approves / Modifies / Rejects} \longrightarrow \text{Field Execution Recorded}$
> 
> Direct transition from `PROPOSED` to `EXECUTED` without explicit prior controller authorization is blocked at the API and service layers. All operational decisions are immutably recorded to the append-only audit trail.
