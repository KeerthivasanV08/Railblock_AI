# Top-Level ML Development Area

This directory contains all machine learning research, experimentation, and training pipelines
for RailBlock AI, separated from the runtime backend serving layer.

## Structure

```
ml/
├── mdps/                          # Multi-Variable Priority Scoring model
│   ├── preprocessing/             # Feature engineering (8 features: 4 base + 4 weather)
│   ├── training/                  # Training scripts + config.yaml
│   ├── evaluation/                # Evaluation & validation scripts
│   ├── artifacts/                 # Serialized model artifacts (model.pkl, scaler.pkl)
│   └── notebooks/                 # Experimentation & EDA
│
├── reinforcement_learning/        # RL Rescheduler Policy (Offline Trained Simulation)
│   ├── environment/               # Gymnasium-compatible RailwayDisruptionEnv (12-dim state, 5 actions)
│   ├── training/                  # PPO Actor-Critic training pipeline
│   ├── evaluation/                # Policy evaluation & reward convergence
│   └── artifacts/                 # Trained policy checkpoint (ppo_rescheduler_v1.pt, training_metrics.json)
│
└── optimization/                  # OR-Tools experiments
    └── experiments/               # Benchmark comparisons & solver tuning
```

## Key Principle

**ML Dev ≠ ML Runtime**

- Training/evaluation pipelines execute here (`ml/`).
- Verified artifacts are copied to `backend/app/ml/models/` for runtime serving.
- The backend references `settings.MODEL_ROOT` which resolves to `backend/app/ml/models/`.
- Offline Simulation Disclosure: All reinforcement learning policies are trained in offline simulation environments based on Chennai–Thoothukudi corridor topology, NOT on live Indian Railways intranet systems. All actions require deterministic `HardConstraintGuard` verification and mandatory human controller approval.

