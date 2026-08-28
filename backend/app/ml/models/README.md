# ML Runtime Artifacts

This directory holds serialized model artifacts loaded at runtime by the FastAPI backend.

- `mdps_model.pkl`: Serialized `GradientBoostingRegressor` model
- `mdps_scaler.pkl`: `StandardScaler` fitted on training feature distributions
- `mdps_feature_metadata.json`: Feature columns and categorical value mappings
- `model_metrics.json`: Evaluated test metrics (MAE, RMSE, R2) and training metadata

NOTE: For offline training, experimentation, and notebooks, see `ml/mdps/`.
