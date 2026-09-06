"""
Disruption Rescheduling Service for RailBlock AI.

Orchestrates the full rescheduler pipeline (Hybrid: PPO + Deterministic Fallback):
  1. Accept disruption event + affected block metadata
  2. Try PPO policy inference (if RL_ENABLED and model artifact exists)
  3. Pass RL candidate through HardConstraintGuard
  4. If guard fails or RL disabled/unavailable: deterministic fallback
  5. Return ranked candidates + constraint guard summary + XAI
  6. Enforce human approval before any plan modification

Human approval is mandatory. This service never modifies plans directly.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from app.config.settings import settings
from app.services.rescheduler.policy_engine import ReschedulerEngine
from app.services.rescheduler.hard_constraint_guard import HardConstraintGuard
from app.repositories.csv_repository import CSVRepository
from app.repositories.disruption_repository import DisruptionRepository
from app.services.analytics.audit_service import AuditService

logger = logging.getLogger(__name__)

# ── RL configuration ────────────────────────────────────────────────────────
RL_ENABLED = os.environ.get("RL_ENABLED", "true").lower() == "true"
_MODEL_PATH = Path(__file__).resolve().parents[3] / "ml" / "models" / "ppo_rescheduler_v1.pt"

# Lazy-load torch only if RL is enabled
_ppo_model = None
_ppo_config = None
_rl_load_error: Optional[str] = None


def _try_load_rl_model():
    """Attempt to load PPO model once. Caches result globally."""
    global _ppo_model, _ppo_config, _rl_load_error
    if _ppo_model is not None or _rl_load_error is not None:
        return
    if not RL_ENABLED:
        _rl_load_error = "RL_ENABLED=false"
        return
    if not _MODEL_PATH.exists():
        _rl_load_error = f"Model artifact not found at {_MODEL_PATH}"
        logger.warning("PPO model not found: %s. Using deterministic fallback.", _MODEL_PATH)
        return
    try:
        import torch
        import torch.nn as nn
        from torch.distributions import Categorical
        checkpoint = torch.load(_MODEL_PATH, map_location="cpu", weights_only=False)
        cfg = checkpoint["config"]
        _ppo_config = cfg

        # Rebuild model architecture inline (avoid circular import)
        hidden = cfg["hidden"]
        obs_dim = cfg["obs_dim"]
        n_actions = cfg["n_actions"]

        backbone = nn.Sequential(
            nn.Linear(obs_dim, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(),
        )
        actor = nn.Linear(hidden, n_actions)
        critic = nn.Linear(hidden, 1)

        class _AC(nn.Module):
            def __init__(self):
                super().__init__()
                self.backbone = backbone
                self.actor = actor
                self.critic = critic

            def predict(self, obs_vec):
                import torch
                obs_t = torch.tensor(obs_vec, dtype=torch.float32).unsqueeze(0)
                with torch.no_grad():
                    shared = self.backbone(obs_t)
                    logits = self.actor(shared)
                    probs = torch.softmax(logits, dim=-1)
                    action = int(torch.argmax(probs).item())
                    confidence = float(probs[0, action].item())
                return action, confidence, probs[0].numpy().tolist()

        model = _AC()
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()
        _ppo_model = model

        summary = checkpoint.get("training_summary", {})
        logger.info(
            "PPO model loaded: version=%s, mean_reward=%.2f, episodes=%d",
            summary.get("model_version", "unknown"),
            summary.get("final_mean_reward_last100", 0.0),
            summary.get("total_episodes", 0),
        )
    except Exception as exc:
        _rl_load_error = str(exc)
        logger.warning("Failed to load PPO model (%s). Using deterministic fallback.", exc)


def _build_rl_state_vector(affected_block: dict, disruption_event: dict) -> list:
    """Build the 12-dim state vector from block/event metadata for PPO inference."""
    import numpy as np
    traffic = float(affected_block.get("traffic_density", 0.6))
    window_min = float(affected_block.get("duration_minutes", 120.0))
    delay_min = float(disruption_event.get("delay_minutes", 0.0))
    overdue = int(affected_block.get("overdue_tasks_count", 1))
    machine_ok = bool(affected_block.get("machine_available", True))
    crew_ok = bool(affected_block.get("crew_available", True))
    weather = float(disruption_event.get("weather_risk_score", affected_block.get("weather_risk_score", 30.0)))
    vuln = float(affected_block.get("section_vulnerability", 0.5))
    asset = float(affected_block.get("asset_type_code", 0.0))
    priority = float(affected_block.get("criticality_score", affected_block.get("priority_score", 70.0)))
    hour = int(affected_block.get("hour_of_day", 12))
    deferred = int(affected_block.get("days_deferred", 0))

    vec = np.array([
        np.clip(traffic, 0.0, 1.0),
        np.clip(window_min / 240.0, 0.0, 1.5),
        np.clip(delay_min / 120.0, 0.0, 2.0),
        np.clip(overdue / 10.0, 0.0, 2.0),
        1.0 if machine_ok else 0.0,
        1.0 if crew_ok else 0.0,
        np.clip(weather / 100.0, 0.0, 1.0),
        np.clip(vuln, 0.0, 1.0),
        np.clip(asset, 0.0, 1.0),
        np.clip(priority / 100.0, 0.0, 1.0),
        np.clip(hour / 24.0, 0.0, 1.0),
        np.clip(deferred / 5.0, 0.0, 2.0),
    ], dtype=np.float32)
    return vec.tolist()


_ACTION_TO_TYPE = {
    0: "keep",
    1: "delay",
    2: "shift",
    3: "shorten",
    4: "cancel",
}


class ReschedulingService:
    def __init__(self):
        self.engine = ReschedulerEngine()
        self.guard = HardConstraintGuard()
        self.log_repo = CSVRepository(settings.OUTPUT_DATA_ROOT / "disruption_reschedule_log.csv")
        self.audit_service = AuditService()
        self.disruption_repo = DisruptionRepository()
        _try_load_rl_model()

    def generate_reschedule_options(
        self,
        event_id: str,
        affected_block_id: str,
        affected_block_metadata: dict | None = None,
    ) -> dict[str, Any]:
        """
        Generate, validate, and rank rescheduling candidates for a disrupted block.

        Pipeline:
            PPO inference (if available) -> HardConstraintGuard -> human approval queue
            If PPO unavailable/fails/guard rejects: deterministic fallback.

        Returns dict with options, constraint_validation_summary, rl_metadata, approval_required.
        """
        # Resolve disruption event context
        disruption_event: dict[str, Any] = {"event_id": event_id, "section_id": "SEC_001"}
        try:
            disruptions_df = self.disruption_repo.get_disruptions()
            if len(disruptions_df) > 0:
                matching = disruptions_df[disruptions_df.get("event_id", pd.Series()) == event_id]
                if len(matching) > 0:
                    row = matching.iloc[0]
                    disruption_event["section_id"] = row.get("section_id", "SEC_001")
                    disruption_event["event_type"] = row.get("event_type", "Disruption")
                    disruption_event["severity"] = row.get("severity", "Medium")
        except Exception as exc:
            logger.debug("Could not resolve disruption from repo: %s", exc)

        affected_block: dict[str, Any] = {
            "block_id": affected_block_id,
            "section_id": disruption_event.get("section_id", "SEC_001"),
        }
        if affected_block_metadata:
            affected_block.update(affected_block_metadata)

        # Try PPO inference
        rl_candidate = None
        rl_metadata: dict[str, Any] = {"rl_enabled": RL_ENABLED, "rl_used": False}

        if _ppo_model is not None:
            try:
                state_vec = _build_rl_state_vector(affected_block, disruption_event)
                action_id, confidence, action_probs = _ppo_model.predict(state_vec)
                action_type = _ACTION_TO_TYPE.get(action_id, "delay")

                rl_candidate = {
                    "option_id": f"{affected_block_id}-RL-PPO-A",
                    "action_type": action_type,
                    "original_block_id": affected_block_id,
                    "section_id": affected_block.get("section_id", "SEC_001"),
                    "rl_action_id": action_id,
                    "rl_confidence": round(confidence, 4),
                    "rl_action_probs": {
                        _ACTION_TO_TYPE[i]: round(float(p), 4)
                        for i, p in enumerate(action_probs)
                    },
                    "traffic_density": float(affected_block.get("traffic_density", 0.6)),
                    "weather_risk_score": float(disruption_event.get("weather_risk_score", 30.0)),
                    "duration_minutes": float(affected_block.get("duration_minutes", 120.0)),
                    "machine_available": bool(affected_block.get("machine_available", True)),
                    "crew_available": bool(affected_block.get("crew_available", True)),
                    "priority_score": float(affected_block.get("criticality_score", 70.0)),
                    "required_machine_type": str(affected_block.get("required_machine_type", "MANUAL_GANG")),
                    "original_criticality_score": float(affected_block.get("criticality_score", 70.0)),
                    "scoring_mode": "ppo_reinforcement_learning",
                    "reason": (
                        f"PPO Rescheduler v1 recommends action '{action_type.upper()}' "
                        f"(confidence={confidence:.1%}). Based on current traffic={state_vec[0]:.2f}, "
                        f"weather_risk={disruption_event.get('weather_risk_score', 30):.1f}, "
                        f"priority={state_vec[9]:.2f}. "
                        "This is a CANDIDATE proposal requiring human approval."
                    ),
                }

                # Guard check
                guard_result = self.guard.validate(rl_candidate)
                rl_candidate["feasible"] = guard_result.feasible
                rl_candidate["failed_constraints"] = guard_result.violated_constraints
                rl_candidate["rejection_reason"] = guard_result.rejection_reason
                rl_candidate["guard_warnings"] = guard_result.warnings
                rl_candidate["guard_constraint_checks"] = guard_result.constraint_checks
                rl_candidate["feasibility_explanation"] = (
                    "PPO candidate passed all hard constraint checks."
                    if guard_result.feasible
                    else f"PPO candidate rejected by guard: {guard_result.rejection_reason}"
                )
                rl_candidate["optimization_score"] = round(confidence * 100.0, 2) if guard_result.feasible else 0.0

                rl_metadata["rl_used"] = True
                rl_metadata["rl_action"] = action_type
                rl_metadata["rl_confidence"] = round(confidence, 4)
                rl_metadata["guard_passed"] = guard_result.feasible
                rl_metadata["guard_violations"] = guard_result.violated_constraints

                if not guard_result.feasible:
                    logger.info(
                        "PPO candidate for %s REJECTED by HardConstraintGuard — falling back to deterministic.",
                        affected_block_id,
                    )
                    rl_metadata["fallback_reason"] = f"Guard rejected: {guard_result.rejection_reason}"
                    rl_candidate = None  # Exclude from options; still logged in metadata

            except Exception as exc:
                logger.warning("PPO inference error for %s: %s. Using deterministic.", affected_block_id, exc)
                rl_metadata["rl_error"] = str(exc)
                rl_metadata["fallback_reason"] = f"Inference error: {exc}"
        else:
            rl_metadata["fallback_reason"] = _rl_load_error or "Model not loaded"

        # Always run deterministic engine (provides alternatives + fallback)
        det_options = self.engine.generate_reschedule_options(disruption_event, affected_block)
        for opt in det_options:
            opt.setdefault("scoring_mode", "deterministic_prototype")

        # Merge: RL candidate first (if guard passed), then deterministic
        all_options = []
        if rl_candidate is not None:
            all_options.append(rl_candidate)
        all_options.extend(det_options)

        # Sort: feasible first, then by optimization score descending
        all_options.sort(key=lambda c: (not c.get("feasible", False), -c.get("optimization_score", 0.0)))

        feasible = [o for o in all_options if o.get("feasible")]
        infeasible = [o for o in all_options if not o.get("feasible")]

        constraint_summary = {
            "total_candidates": len(all_options),
            "feasible_count": len(feasible),
            "infeasible_count": len(infeasible),
            "rejected_candidates": [
                {
                    "option_id": o["option_id"],
                    "action_type": o["action_type"],
                    "rejection_reason": o.get("rejection_reason"),
                    "failed_constraints": o.get("failed_constraints", []),
                }
                for o in infeasible
            ],
        }

        self.audit_service.log_event(
            entity="DISRUPTION_RESCHEDULE",
            entity_id=affected_block_id,
            action="GENERATE_OPTIONS",
            actor="system",
            new_value=f"feasible={len(feasible)}, infeasible={len(infeasible)}, rl_used={rl_metadata['rl_used']}",
        )

        return {
            "event_id": event_id,
            "affected_block_id": affected_block_id,
            "engine_version": self.engine.ENGINE_VERSION,
            "scoring_mode": "hybrid_ppo_deterministic" if rl_metadata["rl_used"] else "deterministic_prototype",
            "rl_metadata": rl_metadata,
            "options": all_options,
            "constraint_validation_summary": constraint_summary,
            "approval_required": True,
            "approval_note": (
                "All candidates have been validated by HardConstraintGuard. "
                "A human controller must approve before any plan modification."
            ),
        }

    def accept_reschedule_option(
        self,
        option_id: str,
        actor: str = "Controller",
        confirmed_feasible: bool = False,
    ) -> dict:
        """
        Record human approval of a rescheduling candidate and log the plan update.

        IMPORTANT: This method does NOT directly modify the operational plan.
        It records the approval decision in the audit log and reschedule log.
        The operational plan update must be performed separately by the planning service.
        """
        if not confirmed_feasible:
            return {
                "reschedule_id": option_id,
                "status": "REJECTED_PENDING_VALIDATION",
                "error": (
                    "Cannot accept a rescheduling option without confirmed constraint validation. "
                    "Ensure feasible=True before calling accept_reschedule_option."
                ),
            }

        log_entry = {
            "reschedule_id": option_id,
            "disruption_event_id": option_id.split("-")[0] if "-" in option_id else option_id,
            "original_block_id": option_id.split("-")[0] if "-" in option_id else option_id,
            "new_block_id": option_id,
            "status": "ACCEPTED",
            "accepted_by": actor,
        }
        try:
            self.log_repo.append_rows([log_entry])
        except Exception as exc:
            logger.warning("Could not append reschedule log: %s", exc)

        self.audit_service.log_event(
            entity="DISRUPTION_RESCHEDULE",
            entity_id=option_id,
            action="ACCEPT_RESCHEDULE",
            actor=actor,
            new_value="ACCEPTED",
        )
        return log_entry


# Backward compatibility alias
ReschedulerService = ReschedulingService
