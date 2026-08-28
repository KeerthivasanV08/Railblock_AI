# MDPS ML Development Area

This directory contains the full development pipeline for the **Multi-Variable Criticality Matrix Priority Scoring (MDPS)** model.

## Structure

```
mdps/
├── preprocessing/     # Feature engineering, data cleaning utilities
├── training/          # Training scripts and configuration
├── evaluation/        # Model evaluation and benchmark scripts
├── artifacts/         # Serialized model artifacts (copied to backend for runtime)
└── notebooks/         # Jupyter notebooks for experimentation
```

## Artifacts

| File | Description |
|------|-------------|
| `artifacts/model.pkl` | Serialized `GradientBoostingRegressor` |
| `artifacts/scaler.pkl` | `StandardScaler` fitted on training distribution |
| `artifacts/feature_metadata.json` | Feature schema and class mappings |
| `artifacts/model_metrics.json` | Evaluation metrics (MAE, RMSE, R²) |

## Runtime

Model artifacts are **copied to `backend/app/ml/models/`** before deployment. The backend loads from there at runtime.

## Training

```bash
python ml/mdps/training/train.py
```
