# Reinforcement Learning — Rescheduler Policy Agent

STATUS: SCAFFOLDING ONLY — RL training not yet implemented.

## Planned Architecture

| Component | Description |
|-----------|-------------|
| `environment/` | Custom Gym-compatible `RailwayEnv` (state space: corridor conditions, traffic slots, resource locations) |
| `training/` | PPO/DQN training scripts using Stable-Baselines3 |
| `evaluation/` | Policy evaluation, rollout simulation, comparison with deterministic baseline |
| `artifacts/` | Serialized trained policy weights |

## Current State

The deterministic rescheduler in `backend/app/services/rescheduler/policy_engine.py` provides
Option A/B/C fallback windows. When an RL policy artifact is placed in `ml/reinforcement_learning/artifacts/rl_policy.pkl`,
the engine will load and use it.

## Training Roadmap

1. Define state/action/reward space aligned with `data/processed/feasibility_checked_tasks.csv`
2. Train PPO policy with Stable-Baselines3 
3. Evaluate against held-out disruption scenarios in `data/synthetic/disruptions/`
4. Deploy artifact to `backend/app/ml/models/rl_rescheduler_policy.pkl`
