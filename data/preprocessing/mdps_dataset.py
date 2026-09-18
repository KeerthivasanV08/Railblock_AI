"""
MDPS (Multi-Variable Criticality Matrix) Scorer & Model Trainer for RailBlock AI.

Trains a GradientBoostingRegressor model to predict task criticality scores (0-100),
evaluates metrics without data leakage, saves serialized artifacts, and produces scored_tasks.csv.
"""

import json
import logging
import hashlib
from datetime import datetime
import numpy as np
import pandas as pd
import joblib
import sklearn

from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score

from data.preprocessing.config import RAW_DIR, PROCESSED_DIR, MODELS_DIR
from data.generators.config import RANDOM_SEED
from data.preprocessing.mdps_features import FEATURE_COLUMNS, build_mdps_features, validate_training_frame

logger = logging.getLogger(__name__)


def train_mdps_model_and_score_tasks(seed: int = RANDOM_SEED) -> tuple[pd.DataFrame, dict]:
    """
    Trains MDPS model, computes evaluation metrics, saves model artifacts, and scores unified tasks.
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load Training Labels & Build Features
    labels_df = validate_training_frame(pd.read_csv(RAW_DIR / "historical/mdps_training_labels.csv"))
    feature_cols = FEATURE_COLUMNS
    X = build_mdps_features(labels_df, include_weather=True).to_numpy(dtype=float)
    X_base = build_mdps_features(labels_df, include_weather=False).to_numpy(dtype=float)
    y = labels_df["actual_priority_rank"].to_numpy(dtype=float)

    # Reproducible 70 / 15 / 15 Train-Val-Test Split
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.30, random_state=seed)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.50, random_state=seed)

    X_b_train, X_b_temp, _, _ = train_test_split(X_base, y, test_size=0.30, random_state=seed)
    _, X_b_test, _, _ = train_test_split(X_b_temp, y_temp, test_size=0.50, random_state=seed)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)

    # Baseline Model (without weather features)
    scaler_b = StandardScaler()
    X_b_train_scaled = scaler_b.fit_transform(X_b_train)
    X_b_test_scaled = scaler_b.transform(X_b_test)
    model_base = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=seed)
    model_base.fit(X_b_train_scaled, y_train)
    y_pred_base = model_base.predict(X_b_test_scaled)
    mae_base = float(mean_absolute_error(y_test, y_pred_base))
    rmse_base = float(root_mean_squared_error(y_test, y_pred_base))
    r2_base = float(r2_score(y_test, y_pred_base))

    # Weather-Enabled Model (with weather features)
    model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=seed)
    model.fit(X_train_scaled, y_train)

    # Evaluate on test set
    y_pred_test = model.predict(X_test_scaled)
    mae = float(mean_absolute_error(y_test, y_pred_test))
    rmse = float(root_mean_squared_error(y_test, y_pred_test))
    r2 = float(r2_score(y_test, y_pred_test))

    from scipy.stats import spearmanr
    rho, _ = spearmanr(y_test, y_pred_test)
    k = int(len(y_test) * 0.20)
    top_k_actual = set(np.argsort(y_test)[-k:])
    top_k_pred = set(np.argsort(y_pred_test)[-k:])
    top_k_recall = float(len(top_k_actual.intersection(top_k_pred)) / max(1, len(top_k_actual)))

    # Feature Importance
    importances = {col: float(imp) for col, imp in zip(feature_cols, model.feature_importances_)}

    metrics = {
        "model_name": "GradientBoostingRegressor",
        "random_seed": seed,
        "timestamp": datetime.now().isoformat(),
        "training_rows": len(X_train),
        "validation_rows": len(X_val),
        "test_rows": len(X_test),
        "python_version": __import__("sys").version.split()[0],
        "sklearn_version": sklearn.__version__,
        "target": "actual_priority_rank",
        "data_provenance": "Synthetic training labels grounded in railway planning concepts",
        "feature_schema": feature_cols,
        "dataset_hash": hashlib.sha256((RAW_DIR / "historical/mdps_training_labels.csv").read_bytes()).hexdigest(),
        "feature_schema_hash": hashlib.sha256(json.dumps(feature_cols).encode()).hexdigest(),
        "model_version": "mdps-v2-weather-enabled",
        "status": "validated",
        "metrics": {
            "MAE": round(mae, 4),
            "RMSE": round(rmse, 4),
            "R2": round(r2, 4),
            "spearman_rank_correlation": round(float(rho), 4),
            "top_20pct_critical_recall": round(top_k_recall, 4)
        },
        "ablation_study": {
            "baseline_model": {
                "features": ["sev_num", "overdue_days", "traffic_num", "deferred_count"],
                "MAE": round(mae_base, 4),
                "RMSE": round(rmse_base, 4),
                "R2": round(r2_base, 4),
            },
            "weather_enabled_model": {
                "features": feature_cols,
                "MAE": round(mae, 4),
                "RMSE": round(rmse, 4),
                "R2": round(r2, 4),
            },
            "delta_R2": round(r2 - r2_base, 4),
            "delta_MAE": round(mae - mae_base, 4),
        },
        "feature_importance": importances
    }

    feature_metadata = {
        "model_name": "MDPS",
        "model_version": "v2_weather_enabled",
        "feature_cols": feature_cols,
        "categorical_encodings": {
            "severity_class": {"A": 3, "B": 2, "C": 1},
            "traffic_density_class": {"Low": 1, "Medium": 2, "High": 3, "Critical Peak": 4}
        },
        "sklearn_version": sklearn.__version__,
        "metrics": metrics["metrics"],
        "ablation_study": metrics["ablation_study"]
    }

    # Save artifacts across all canonical and runtime directories
    from data.preprocessing.config import BASE_DIR
    target_dirs = [
        MODELS_DIR,
        BASE_DIR / "backend" / "app" / "ml" / "models",
        BASE_DIR / "backend" / "app" / "ml" / "models" / "mdps_v2",
        BASE_DIR / "ml" / "mdps" / "artifacts"
    ]
    for t_dir in target_dirs:
        t_dir.mkdir(parents=True, exist_ok=True)
        # Standard filenames
        joblib.dump(model, t_dir / "mdps_model.pkl")
        joblib.dump(scaler, t_dir / "mdps_scaler.pkl")
        with open(t_dir / "mdps_feature_metadata.json", "w") as f:
            json.dump(feature_metadata, f, indent=2)
        with open(t_dir / "model_metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)
        with open(t_dir / "mdps_feature_importance.json", "w") as f:
            json.dump(importances, f, indent=2)
        # ml/mdps/artifacts convention
        if t_dir.name == "artifacts":
            joblib.dump(model, t_dir / "model.pkl")
            joblib.dump(scaler, t_dir / "scaler.pkl")
            with open(t_dir / "feature_metadata.json", "w") as f:
                json.dump(feature_metadata, f, indent=2)

    logger.info(f"MDPS Model trained successfully with sklearn {sklearn.__version__}. R2: {r2:.4f}, MAE: {mae:.4f}, Baseline R2: {r2_base:.4f}")

    # 2. Score Unified Maintenance Tasks
    tasks_path = PROCESSED_DIR / "spatially_mapped_tasks.csv"
    if not tasks_path.exists():
        from data.preprocessing.spatial_mapping import map_spatial_locations
        tasks_df = map_spatial_locations()
    else:
        tasks_df = pd.read_csv(tasks_path)

    # Feature extraction for tasks
    X_tasks = build_mdps_features(tasks_df).to_numpy(dtype=float)
    X_tasks_scaled = scaler.transform(X_tasks)
    raw_scores = model.predict(X_tasks_scaled)
    criticality_scores = np.round(np.clip(raw_scores, 0.0, 100.0), 2)

    scored_df = tasks_df.copy()
    scored_df["criticality_score"] = criticality_scores
    
    # Priority Rank & Band
    scored_df["priority_rank"] = scored_df["criticality_score"].rank(ascending=False, method="min").astype(int)

    bands = []
    for sc in criticality_scores:
        if sc >= 75.0:
            bands.append("Critical")
        elif sc >= 50.0:
            bands.append("High")
        elif sc >= 25.0:
            bands.append("Medium")
        else:
            bands.append("Low")
    scored_df["priority_band"] = bands

    # NOTE: Do NOT sort by priority_rank here.
    # Sorting highest-first would cause the API to return only ~99-score tasks on every page,
    # making it appear as if all tasks have priority 99.
    # The original row order (from spatially_mapped_tasks) provides a representative
    # distribution of all priority bands across pages.
    scored_df = scored_df.reset_index(drop=True)

    out_path = PROCESSED_DIR / "scored_tasks.csv"
    scored_df.to_csv(out_path, index=False)
    logger.info(f"Generated {len(scored_df)} scored maintenance tasks at {out_path}")

    return scored_df, metrics


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train_mdps_model_and_score_tasks()

