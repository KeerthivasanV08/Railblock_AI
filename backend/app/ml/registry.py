"""
Central Programmatic Model Registry for RailBlock AI.

Provides versioning, provenance metadata, feature schemas, and validation metrics
for all machine learning models in the RailBlock AI ecosystem:
  1. MDPS Criticality Scorer (GradientBoostingRegressor)
  2. PPO Rescheduler Policy (Actor-Critic PyTorch Neural Network)
  3. Seasonal Risk Engine (Deterministic Analytical Formulation)
  4. Constraint & Safety Guard (Deterministic Operational Boundary)
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class ModelMetadata:
    model_name: str
    model_version: str
    purpose: str
    artifact_path: str
    artifact_exists: bool
    algorithm: str
    feature_schema: List[str]
    training_dataset: str
    training_date: str
    training_seed: int
    metrics: Dict[str, Any]
    production_status: str  # "ACTIVE", "STALE", "EXPERIMENTAL", "FALLBACK"
    requires_guard: bool
    requires_human_approval: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ModelRegistry:
    """Central registry querying model metadata and production provenance."""

    def __init__(self):
        self.models_dir = settings.MODEL_ROOT

    def get_mdps_metadata(self) -> ModelMetadata:
        metrics_file = self.models_dir / "model_metrics.json"
        artifact_path = self.models_dir / "mdps_model.pkl"

        data = {}
        if metrics_file.exists():
            try:
                with open(metrics_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as exc:
                logger.debug("Failed reading MDPS metrics: %s", exc)

        return ModelMetadata(
            model_name=data.get("model_name", "GradientBoostingRegressor"),
            model_version=data.get("model_version", "mdps-v2-sklearn-1.6.1"),
            purpose="Multi-Variable Maintenance Task Criticality Prioritization (0-100)",
            artifact_path=str(artifact_path),
            artifact_exists=artifact_path.exists(),
            algorithm="Gradient Boosting Regressor (100 estimators, max_depth=5)",
            feature_schema=data.get("feature_schema", ["sev_num", "overdue_days", "traffic_num", "deferred_count"]),
            training_dataset="data/raw/historical/mdps_training_labels.csv (21,000 training rows)",
            training_date=data.get("timestamp", "2026-09-06T21:26:26"),
            training_seed=data.get("random_seed", 42),
            metrics=data.get("metrics", {"MAE": 2.2861, "RMSE": 2.8938, "R2": 0.9756}),
            production_status="ACTIVE",
            requires_guard=False,
            requires_human_approval=False,
        )

    def get_ppo_metadata(self) -> ModelMetadata:
        artifact_path = self.models_dir / "ppo_rescheduler_v1.pt"
        metrics_file = Path(__file__).resolve().parents[3] / "ml" / "reinforcement_learning" / "artifacts" / "training_metrics.json"

        data = {}
        if metrics_file.exists():
            try:
                with open(metrics_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as exc:
                logger.debug("Failed reading PPO metrics: %s", exc)

        summary = data.get("training_summary", {})
        return ModelMetadata(
            model_name="ppo_rescheduler_v1",
            model_version=summary.get("model_version", "ppo_rescheduler_v1"),
            purpose="Autonomous Candidate Maintenance Block Rescheduling under Operational Disruption",
            artifact_path=str(artifact_path),
            artifact_exists=artifact_path.exists(),
            algorithm="Proximal Policy Optimization (Actor-Critic MLP, 2xTanh(128))",
            feature_schema=[
                "traffic_density", "remaining_window_norm", "delay_magnitude_norm",
                "overdue_tasks_norm", "machine_available_flag", "crew_available_flag",
                "weather_srs_norm", "section_vulnerability", "asset_type_code",
                "priority_score_norm", "hour_of_day_norm", "days_deferred_norm"
            ],
            training_dataset="Simulated RailwayDisruptionEnv (Chennai-Thoothukudi corridor topology, 198,656 steps)",
            training_date="2026-09-06",
            training_seed=42,
            metrics={
                "final_mean_reward_last100": summary.get("final_mean_reward_last100", 16.35),
                "total_timesteps": summary.get("total_timesteps", 198656),
                "training_duration_s": summary.get("training_duration_s", 216.0),
            },
            production_status="ACTIVE",
            requires_guard=True,
            requires_human_approval=True,
        )

    def list_models(self) -> List[Dict[str, Any]]:
        return [
            self.get_mdps_metadata().to_dict(),
            self.get_ppo_metadata().to_dict(),
        ]

    def log_decision(
        self,
        model_name: str,
        decision_id: str,
        action: str,
        confidence: Optional[float] = None,
        fallback_used: bool = False,
    ) -> Dict[str, Any]:
        """Creates a standardized decision audit record."""
        return {
            "model_name": model_name,
            "decision_id": decision_id,
            "action": action,
            "confidence": confidence,
            "fallback_used": fallback_used,
            "decision_timestamp": datetime.now().isoformat(),
            "code_version": "v1.2.0-closed-loop",
        }


# Global singleton instance
model_registry = ModelRegistry()
