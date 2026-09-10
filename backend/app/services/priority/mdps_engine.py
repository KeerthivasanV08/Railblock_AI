"""
MDPS (Multi-Variable Criticality Matrix) Priority Scoring Engine for RailBlock AI.

Calculates deterministic and ML-enhanced criticality scores (0-100), component breakdowns,
and natural language explainability reasons.
"""

import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
import sklearn

from app.config.settings import settings
from app.core.constants import MDPS_WEIGHTS
from app.services.priority.feature_builder import build_mdps_features

logger = logging.getLogger(__name__)


class MDPSEngine:
    def __init__(self):
        self.weights = MDPS_WEIGHTS
        self.model = None
        self.scaler = None
        self.metadata = None
        self.model_status = {
            "model_available": False,
            "model_version": None,
            "runtime_library_version": sklearn.__version__,
            "fallback": True,
            "fallback_reason": "Model artifacts have not been loaded.",
            "scoring_mode": "deterministic_mdps",
            "feature_schema": [],
        }
        self._load_ml_model()

    def _load_ml_model(self):
        # Look in settings.MODEL_ROOT first (backend/app/ml/models/)
        # with fallback to data/models/ or ml/mdps/artifacts/
        model_paths = [
            settings.MODEL_ROOT / "mdps_model.pkl",
            settings.DATA_ROOT / "models" / "mdps_model.pkl",
            settings.BASE_DIR / "ml" / "mdps" / "artifacts" / "model.pkl",
        ]
        scaler_paths = [
            settings.MODEL_ROOT / "mdps_scaler.pkl",
            settings.DATA_ROOT / "models" / "mdps_scaler.pkl",
            settings.BASE_DIR / "ml" / "mdps" / "artifacts" / "scaler.pkl",
        ]
        meta_paths = [
            settings.MODEL_ROOT / "mdps_feature_metadata.json",
            settings.DATA_ROOT / "models" / "mdps_feature_metadata.json",
            settings.BASE_DIR / "ml" / "mdps" / "artifacts" / "feature_metadata.json",
        ]

        model_path = next((p for p in model_paths if p.exists()), model_paths[0])
        scaler_path = next((p for p in scaler_paths if p.exists()), scaler_paths[0])
        meta_path = next((p for p in meta_paths if p.exists()), meta_paths[0])

        if model_path.exists() and scaler_path.exists():
            try:
                self.model = joblib.load(model_path)
                self.scaler = joblib.load(scaler_path)
                if meta_path.exists():
                    with open(meta_path, "r") as f:
                        self.metadata = json.load(f)
                self.model_status = {
                    "model_available": True,
                    "model_version": self.metadata.get("model_name", "GradientBoostingRegressor") if self.metadata else "GradientBoostingRegressor",
                    "runtime_library_version": sklearn.__version__,
                    "fallback": False,
                    "fallback_reason": "",
                    "scoring_mode": "ml_artifact_available_with_deterministic_guardrail",
                    "feature_schema": self.metadata.get("feature_cols", []) if self.metadata else [],
                }
                logger.info("Loaded ML-enhanced MDPS priority model successfully.")
            except Exception as exc:
                self.model_status.update({
                    "model_available": False,
                    "model_version": "mdps_model.pkl",
                    "fallback": True,
                    "fallback_reason": f"{type(exc).__name__}: {exc}",
                    "scoring_mode": "deterministic_mdps",
                })
                logger.warning(f"Failed to load ML MDPS model: {exc}. Falling back to deterministic MDPS.")
                self.model = None
                self.scaler = None
        else:
            missing = [
                str(path.name)
                for path in (model_path, scaler_path)
                if not path.exists()
            ]
            self.model_status.update({
                "fallback_reason": f"Missing artifacts: {', '.join(missing)}",
            })

    def get_model_status(self) -> dict:
        return dict(self.model_status)

    def calculate_priority(self, task: dict) -> dict:
        """
        Calculates priority score (0-100), 6 component values, priority band, and priority reason.
        """
        sev = str(task.get("severity_class", "C")).upper()
        overdue_days = float(task.get("overdue_days", 0))
        def_count = float(task.get("deferred_count", 0))
        t_density = float(task.get("traffic_density", 0.5))

        # The persisted model predicts the same bounded priority target used in training.
        model_score = None
        if self.model is not None and self.scaler is not None:
            try:
                features = build_mdps_features(pd.DataFrame([task]))
                model_score = float(self.model.predict(self.scaler.transform(features.to_numpy(dtype=float)))[0])
                if not np.isfinite(model_score):
                    model_score = None
            except (KeyError, TypeError, ValueError, RuntimeError) as exc:
                logger.warning("MDPS model inference failed; using deterministic score: %s", exc)

        # 1. Severity component (0-100)
        sev_comp = 100.0 if sev == "A" else (60.0 if sev == "B" else 25.0)

        # 2. Overdue component (0-100)
        overdue_comp = min(100.0, overdue_days * 3.33)

        # 3. Traffic component (0-100)
        traffic_comp = min(100.0, t_density * 100.0)

        # 4. Criticality component (0-100 based on defect type)
        d_type = str(task.get("defect_type", ""))
        if "Fracture" in d_type or "Interlocking" in d_type or "Substation" in d_type:
            crit_comp = 90.0
        elif "Failure" in d_type or "Catenary" in d_type or "Circuit" in d_type:
            crit_comp = 70.0
        else:
            crit_comp = 45.0

        # 5. Deferral component (0-100)
        deferral_comp = min(100.0, def_count * 25.0)

        # 6. Historical risk component (0-100)
        hist_comp = min(100.0, (overdue_days * 0.5 + def_count * 10.0))

        # Weighted sum formula
        w = self.weights
        det_score = (
            sev_comp * w["severity_weight"] +
            overdue_comp * w["overdue_weight"] +
            traffic_comp * w["traffic_weight"] +
            crit_comp * w["criticality_weight"] +
            deferral_comp * w["deferral_weight"] +
            hist_comp * w["historical_weight"]
        )

        final_score = round(max(0.0, min(100.0, model_score if model_score is not None else det_score)), 2)

        # Priority Band
        if final_score >= 75.0:
            band = "Critical"
        elif final_score >= 50.0:
            band = "High"
        elif final_score >= 25.0:
            band = "Medium"
        else:
            band = "Low"

        # Generate Explainable Natural Language Reason
        reasons = []
        if sev == "A":
            reasons.append("high severity class A defect")
        if overdue_days > 7:
            reasons.append(f"overdue by {int(overdue_days)} days")
        if def_count >= 2:
            reasons.append(f"deferred {int(def_count)} times previously")
        if t_density > 0.7:
            reasons.append("located on high-utilization traffic section")
        srs_val = float(task.get("srs", task.get("seasonal_risk_score", 0.0)))
        if srs_val > 50.0:
            reasons.append(f"elevated seasonal weather risk ({srs_val:.1f})")

        reason_str = f"{band} priority due to " + (", ".join(reasons) if reasons else "routine maintenance schedule") + "."

        return {
            "criticality_score": final_score,
            "priority_band": band,
            "components": {
                "severity_component": round(sev_comp, 2),
                "overdue_component": round(overdue_comp, 2),
                "traffic_component": round(traffic_comp, 2),
                "criticality_component": round(crit_comp, 2),
                "deferral_component": round(deferral_comp, 2),
                "historical_component": round(hist_comp, 2)
            },
            "priority_reason": reason_str,
            "model_status": self.get_model_status()
        }

    def score_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Scores an entire DataFrame of maintenance tasks."""
        scores, ranks, bands, reasons = [], [], [], []

        for idx, row in df.iterrows():
            res = self.calculate_priority(row.to_dict())
            scores.append(res["criticality_score"])
            bands.append(res["priority_band"])
            reasons.append(res["priority_reason"])

        scored_df = df.copy()
        scored_df["criticality_score"] = scores
        scored_df["priority_rank"] = pd.Series(scores).rank(ascending=False, method="min").astype(int)
        scored_df["priority_band"] = bands
        scored_df["priority_reason"] = reasons
        scored_df["scoring_mode"] = self.model_status["scoring_mode"]
        scored_df["model_available"] = self.model_status["model_available"]

        return scored_df.sort_values("priority_rank").reset_index(drop=True)
