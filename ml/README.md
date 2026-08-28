# Top-Level ML Development Area

This directory contains all machine learning research, experimentation, and development code
for RailBlock AI, separated from the runtime backend.

## Structure

```
ml/
├── mdps/                          # Multi-Variable Priority Scoring model
│   ├── preprocessing/             # Feature engineering
│   ├── training/                  # Training scripts + config.yaml
│   ├── evaluation/                # Evaluation scripts
│   ├── artifacts/                 # Serialized model artifacts
│   └── notebooks/                 # Jupyter experimentation
│
├── reinforcement_learning/        # RL Rescheduler Policy (SCAFFOLDING ONLY)
│   ├── environment/               # Gym-compatible railway environment
│   ├── training/                  # PPO/DQN training scripts
│   ├── evaluation/                # Policy evaluation
│   └── artifacts/                 # Trained policy weights (future)
│
└── optimization/                  # OR-Tools experiments
    └── experiments/               # Benchmark comparisons
```

## Key Principle

**ML Dev ≠ ML Runtime**

- Training/evaluation code lives here (`ml/`)
- Trained artifacts are **copied to `backend/app/ml/models/`** for runtime serving
- The backend references `settings.MODEL_ROOT` which resolves to the `backend/app/ml/models/` dir
- Legacy path `data/models/` is kept for backward compatibility with older pipeline scripts
