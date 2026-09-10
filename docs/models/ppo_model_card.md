# PPO Rescheduler Model Card — RailBlock AI

**Model Name:** PPO Rescheduler  
**Model Version:** `ppo_rescheduler_v1`  
**Artifact:** `ml/reinforcement_learning/artifacts/ppo_rescheduler_v1.pt`  
**Also at:** `backend/app/ml/models/ppo_rescheduler_v1.pt`  
**SHA256 (first 16):** `1af9f66acb6988d6`  
**Size:** 80,359 bytes  
**Training Duration:** 216 seconds (~3.6 minutes)

---

## Model Purpose

Learns an optimal rescheduling policy for railway maintenance blocks under operational disruptions. Proposes one of 5 discrete actions given a 12-dimensional state vector representing current block context.

**Critical Safety Constraint:** This model only **proposes** actions. All proposals pass through `HardConstraintGuard` before presentation, and require **human controller approval** before any plan modification. The model cannot directly execute changes.

---

## Data Provenance

> **⚠️ Training Environment:** Policy trained entirely in **offline simulation** using `RailwayDisruptionEnv` — a custom Gymnasium-compatible environment. NOT trained on live Indian Railways operational data or historical block execution records.

---

## Environment Specification

**Class:** `RailwayDisruptionEnv` (`ml/reinforcement_learning/environment/railway_env.py`)  
**Observation Space:** Continuous 12-dimensional vector  
**Action Space:** 5 discrete actions

### State Dimensions (12-dim vector)

| Dim | Feature | Range | Source |
|-----|---------|-------|--------|
| 0 | `traffic_density` | [0.0, 1.0] | Section traffic density |
| 1 | `remaining_window_min` | [0.0, 1.5] (÷240) | Remaining possession window |
| 2 | `delay_magnitude_min` | [0.0, 2.0] (÷120) | Train delay in minutes |
| 3 | `overdue_tasks_count` | [0.0, 2.0] (÷10) | Number of overdue tasks |
| 4 | `machine_available` | {0.0, 1.0} | Machine resource availability |
| 5 | `crew_available` | {0.0, 1.0} | Crew resource availability |
| 6 | `weather_risk_score` | [0.0, 1.0] (÷100) | **Live weather + seasonal SRS** |
| 7 | `section_vulnerability` | [0.0, 1.0] | Section terrain vulnerability |
| 8 | `asset_type_code` | {0.0, 0.5, 1.0} | Track / Signal / OHE |
| 9 | `priority_score` | [0.0, 1.0] (÷100) | MDPS criticality score |
| 10 | `hour_of_day` | [0.0, 1.0] (÷24) | Current hour |
| 11 | `days_deferred` | [0.0, 2.0] (÷5) | Times task deferred |

### Action Space (5 actions)

| Action ID | Name | Description |
|-----------|------|-------------|
| 0 | `KEEP_SCHEDULE` | Proceed with planned window |
| 1 | `DELAY_BLOCK` | Shift start by delay duration (30–60 min) |
| 2 | `MOVE_BLOCK` | Move to low-traffic night slot (01:00) |
| 3 | `SHORTEN_BLOCK` | Compress window to 65% duration |
| 4 | `CANCEL_CANDIDATE` | Defer/cancel block |

---

## Training Configuration

| Parameter | Value |
|-----------|-------|
| Algorithm | PPO (Actor-Critic MLP) |
| Total timesteps | 198,656 |
| Total episodes | 198,656 |
| Parallel environments | 8 |
| Steps per update | 256 |
| Learning rate | 3×10⁻⁴ |
| Epochs per update | 8 |
| Batch size | 64 |
| Gamma | 0.99 |
| GAE Lambda | 0.95 |
| Clip epsilon | 0.2 |
| Entropy coefficient | 0.02 |

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| Final mean reward (last 100 eps) | 16.345 |
| Training FPS | ~920 |
| Policy type | PPO Actor-Critic MLP (2×hidden layers, Tanh) |

### Reward Convergence

| Update | Steps | Mean Reward (last 50) |
|--------|-------|----------------------|
| 10 | 20,480 | 13.18 |
| 20 | 40,960 | 18.70 |
| 40 | 81,920 | 18.52 |
| 70 | 143,360 | 17.38 |
| 97 (final) | 198,656 | 17.89 |

---

## Safety Architecture

```
Disruption Event
      ↓
PPO Policy → ranked action proposals (top 3)
      ↓
HardConstraintGuard (mandatory) → validate each candidate
      ↓
XAI Explanation attached to each option
      ↓
Human Controller (MUST approve/reject)
      ↓
Audit Log
```

**RL_ENABLED kill switch:** `RL_ENABLED=false` environment variable disables PPO and forces deterministic rescheduler.

---

## Runtime Behavior (Verified)

- PPO model loads on `ReschedulingService` init
- Live test result: `scoring_mode: "hybrid_ppo_deterministic"`, `rl_used: True`
- 6 options returned: 3 PPO (feasible), 3 deterministic — all pass guard
- `approval_required: True` always returned

---

## Limitations

1. Trained entirely on synthetic simulation — not validated on real IR disruption data
2. 5-action space is simplified — real rescheduling may need more granular actions
3. Episode max_steps=5 — policy designed for short horizon decisions
4. Weather in state comes from simulated distribution `[15, 25, 38, 55, 82]` — not actual IMD data
5. No A/B comparison vs. deterministic baseline conducted in this audit (planned)
