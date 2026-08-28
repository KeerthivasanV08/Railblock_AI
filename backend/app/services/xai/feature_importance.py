"""
Feature importance inspection helper for MDPS model explanations.
"""

from typing import Dict, Any, List
import json
from app.config.settings import settings


class FeatureImportanceService:
    def get_importance_report(self) -> List[Dict[str, Any]]:
        # Read from model_metrics or feature_importance if exists
        metrics_path = settings.MODEL_ROOT / "model_metrics.json"
        if metrics_path.exists():
            try:
                data = json.loads(metrics_path.read_text())
                fi = data.get("feature_importance", {})
                return [
                    {"feature": k, "importance": v, "rank": idx + 1}
                    for idx, (k, v) in enumerate(sorted(fi.items(), key=lambda x: x[1], reverse=True))
                ]
            except Exception:
                pass
        return []
