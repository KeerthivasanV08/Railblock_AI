"""
Disruption Rescheduling Service for RailBlock AI.

Orchestrates the complete adaptive self-healing pipeline (Hybrid: PPO + Hard Constraint Guard + Deterministic Fallback):
  1. Ingest disruption event & compute multi-dimensional impact assessment
  2. Extract PPO policy distribution across action space
  3. Validate candidates through HardConstraintGuard (multi-candidate ranked evaluation)
  4. Augment candidates with transparent Explainability (XAI) breakdown
  5. Fall back safely to deterministic engine if all RL proposals fail guard
  6. Return ranked candidates, constraint audit, XAI reasoning, and impact metrics
  7. Enforce mandatory human approval and apply schedule modifications upon confirmation.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from app.config.settings import settings
from app.services.rescheduler.policy_engine import ReschedulerEngine
from app.services.rescheduler.hard_constraint_guard import HardConstraintGuard
from app.services.rescheduler.impact_analyzer import DisruptionEngine, DisruptionImpactAssessment
from app.services.xai.explanation_service import ExplainabilityService
from app.repositories.csv_repository import CSVRepository
from app.repositories.disruption_repository import DisruptionRepository
from app.services.analytics.audit_service import AuditService

logger = logging.getLogger(__name__)

# ── RL configuration ────────────────────────────────────────────────────────
RL_ENABLED = os.environ.get("RL_ENABLED", "true").lower() == "true"
_MODEL_PATH = Path(__file__).resolve().parents[2] / "ml" / "models" / "ppo_rescheduler_v1.pt"
if not _MODEL_PATH.exists():
    _ALT_PATH = Path(__file__).resolve().parents[4] / "ml" / "reinforcement_learning" / "artifacts" / "ppo_rescheduler_v1.pt"
    if _ALT_PATH.exists():
        _MODEL_PATH = _ALT_PATH

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
        checkpoint = torch.load(_MODEL_PATH, map_location="cpu", weights_only=False)
        cfg = checkpoint["config"]
        _ppo_config = cfg

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

            def predict_all(self, obs_vec):
                import torch
                obs_t = torch.tensor(obs_vec, dtype=torch.float32).unsqueeze(0)
                with torch.no_grad():
                    shared = self.backbone(obs_t)
                    logits = self.actor(shared)
                    probs = torch.softmax(logits, dim=-1)
                    ranked_indices = torch.argsort(probs, descending=True).squeeze(0).tolist()
                    all_probs = probs[0].numpy().tolist()
                return ranked_indices, all_probs

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
    """Build the canonical 12-dim state vector for PPO neural inference."""
    traffic_val = affected_block.get("traffic_density", 0.6)
    traffic = float(traffic_val) if traffic_val is not None else 0.6

    win_val = affected_block.get("duration_minutes", 120.0)
    window_min = float(win_val) if win_val is not None else 120.0

    delay_val = disruption_event.get("delay_minutes", disruption_event.get("delay_min", 0.0))
    delay_min = float(delay_val) if delay_val is not None else 0.0

    overdue_val = affected_block.get("overdue_tasks_count", 1)
    overdue = int(overdue_val) if overdue_val is not None else 1

    machine_ok = bool(affected_block.get("machine_available", True))
    crew_ok = bool(affected_block.get("crew_available", True))

    weather_val = disruption_event.get("weather_risk_score", affected_block.get("weather_risk_score", 30.0))
    weather = float(weather_val) if weather_val is not None else 30.0

    vuln_val = affected_block.get("section_vulnerability", 0.5)
    vuln = float(vuln_val) if vuln_val is not None else 0.5

    asset_val = affected_block.get("asset_type_code", 0.0)
    asset = float(asset_val) if asset_val is not None else 0.0

    prio_val = affected_block.get("criticality_score", affected_block.get("priority_score", 70.0))
    priority = float(prio_val) if prio_val is not None else 70.0

    hour_val = affected_block.get("hour_of_day", 12)
    hour = int(hour_val) if hour_val is not None else 12

    def_val = affected_block.get("days_deferred", 0)
    deferred = int(def_val) if def_val is not None else 0

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
        self.disruption_engine = DisruptionEngine()
        self.xai_service = ExplainabilityService()
        self.log_repo = CSVRepository(settings.OUTPUT_DATA_ROOT / "disruption_reschedule_log.csv")
        self.weekly_repo = CSVRepository(settings.OUTPUT_DATA_ROOT / "weekly_block_plan.csv")
        self.version_repo = CSVRepository(settings.OUTPUT_DATA_ROOT / "plan_versions.csv")
        self.audit_service = AuditService()
        self.disruption_repo = DisruptionRepository()
        _try_load_rl_model()

    def _project_time_window(
        self,
        action_type: str,
        affected_block: Dict[str, Any],
        delay_min: float
    ) -> Tuple[datetime, datetime, float, str, str]:
        """
        Projects concrete operational start/end timestamps from an action type.
        """
        raw_start = affected_block.get("start_time")
        base_dt = datetime.now()
        if raw_start:
            try:
                base_dt = datetime.fromisoformat(str(raw_start).replace(" ", "T"))
            except Exception:
                pass

        orig_dur = float(affected_block.get("duration_minutes", 120.0))

        if action_type == "keep":
            new_start = base_dt
            dur = orig_dur
            shift_hours = 0.0
            suffix = "KEEP"
        elif action_type == "delay":
            shift_m = max(30.0, delay_min if delay_min > 0 else 60.0)
            new_start = base_dt + timedelta(minutes=shift_m)
            dur = orig_dur
            shift_hours = round(shift_m / 60.0, 2)
            suffix = f"D{int(shift_m)}"
        elif action_type == "shift":
            # Shift to next early morning / low-traffic window (01:00 AM)
            target = base_dt.replace(hour=1, minute=0, second=0, microsecond=0)
            if target <= base_dt:
                target += timedelta(days=1)
            new_start = target
            dur = orig_dur
            shift_hours = round((new_start - base_dt).total_seconds() / 3600.0, 2)
            suffix = "NIGHT-SLOT"
        elif action_type == "shorten":
            new_start = base_dt + timedelta(minutes=max(15.0, delay_min * 0.5))
            dur = max(30.0, round(orig_dur * 0.65, 0))
            shift_hours = round(delay_min * 0.5 / 60.0, 2)
            suffix = f"SHORT-{int(dur)}M"
        else:  # cancel / defer
            new_start = base_dt + timedelta(days=1)
            dur = orig_dur
            shift_hours = 24.0
            suffix = "DEFERRED"

        new_end = new_start + timedelta(minutes=dur)
        window_str = f"{new_start.strftime('%H:%M')} – {new_end.strftime('%H:%M')}"
        return new_start, new_end, shift_hours, window_str, suffix

    def generate_reschedule_options(
        self,
        event_id: str,
        affected_block_id: str,
        affected_block_metadata: dict | None = None,
    ) -> dict[str, Any]:
        """
        Generate, validate, explain, and rank rescheduling candidates for a disrupted block.

        Pipeline:
            Disruption Assessment -> Multi-Candidate PPO -> HardConstraintGuard ->
            Deterministic Fallback (if needed) -> XAI Explanation -> Human Approval Queue
        """
        # Resolve disruption event context
        disruption_event: dict[str, Any] = {
            "event_id": event_id,
            "section_id": "SEC_001",
            "event_type": "Late Train",
            "severity": "Medium",
            "delay_minutes": 35.0,
        }
        try:
            disruptions_df = self.disruption_repo.get_disruptions()
            if len(disruptions_df) > 0:
                matching = disruptions_df[disruptions_df.get("event_id", pd.Series()) == event_id]
                if len(matching) > 0:
                    row = matching.iloc[0]
                    disruption_event["section_id"] = row.get("section_id", "SEC_001")
                    disruption_event["event_type"] = row.get("event_type", "Late Train")
                    disruption_event["severity"] = row.get("severity", "Medium")
                    disruption_event["delay_minutes"] = float(row.get("delay_minutes", 35.0))
        except Exception as exc:
            logger.debug("Could not resolve disruption from repo: %s", exc)

        affected_block: dict[str, Any] = {
            "block_id": affected_block_id,
            "section_id": disruption_event.get("section_id", "SEC_001"),
            "duration_minutes": 120.0,
            "criticality_score": 75.0,
            "traffic_density": 0.55,
            "machine_available": True,
            "crew_available": True,
        }
        if affected_block_metadata:
            affected_block.update(affected_block_metadata)

        # 1. Multi-dimensional disruption impact assessment
        impact_assessment: DisruptionImpactAssessment = self.disruption_engine.assess_impact(
            event=disruption_event,
            affected_block=affected_block,
            traffic_density=float(affected_block.get("traffic_density", 0.55)),
        )

        # 2. Multi-candidate PPO inference with Hard Constraint Filtering
        rl_candidates: List[Dict[str, Any]] = []
        rl_metadata: dict[str, Any] = {
            "rl_enabled": RL_ENABLED,
            "rl_used": False,
            "model_version": getattr(_ppo_config, "get", lambda k, d=None: "ppo_rescheduler_v1")("model_version", "ppo_rescheduler_v1") if _ppo_config else "ppo_rescheduler_v1",
        }

        if _ppo_model is not None:
            try:
                state_vec = _build_rl_state_vector(affected_block, disruption_event)
                ranked_actions, action_probs = _ppo_model.predict_all(state_vec)

                delay_m = impact_assessment.schedule_delay_min

                for rank_idx, action_id in enumerate(ranked_actions[:3]):  # evaluate top 3 candidates
                    act_type = _ACTION_TO_TYPE.get(action_id, "delay")
                    conf = float(action_probs[action_id])
                    prob_dict = {
                        _ACTION_TO_TYPE[i]: round(float(p), 4)
                        for i, p in enumerate(action_probs)
                    }

                    st_dt, end_dt, shift_h, win_str, suffix = self._project_time_window(
                        act_type, affected_block, delay_m
                    )

                    candidate = {
                        "option_id": f"{affected_block_id}-RL-PPO-{chr(65 + rank_idx)}",
                        "action_type": act_type,
                        "original_block_id": affected_block_id,
                        "new_block_id": f"{affected_block_id}-{suffix}",
                        "section_id": affected_block.get("section_id", "SEC_001"),
                        "date": st_dt.strftime("%Y-%m-%d"),
                        "start_time": st_dt.strftime("%Y-%m-%d %H:%M:%S"),
                        "end_time": end_dt.strftime("%Y-%m-%d %H:%M:%S"),
                        "recommended_window": win_str,
                        "duration_minutes": (end_dt - st_dt).total_seconds() / 60.0,
                        "shift_from_original_hours": shift_h,
                        "rl_action_id": action_id,
                        "rl_confidence": round(conf, 4),
                        "rl_action_probs": prob_dict,
                        "traffic_density": float(affected_block.get("traffic_density", 0.55)),
                        "weather_risk_score": float(disruption_event.get("weather_risk_score", 30.0)),
                        "machine_available": bool(affected_block.get("machine_available", True)),
                        "crew_available": bool(affected_block.get("crew_available", True)),
                        "priority_score": float(affected_block.get("criticality_score", 75.0)),
                        "required_machine_type": str(affected_block.get("required_machine_type", "MANUAL_GANG")),
                        "original_criticality_score": float(affected_block.get("criticality_score", 75.0)),
                        "scoring_mode": "ppo_reinforcement_learning",
                        "reason": (
                            f"PPO Rescheduler v1 proposes '{act_type.upper()}' (rank #{rank_idx+1}, "
                            f"confidence={conf:.1%}). Projected window {win_str} with "
                            f"shift={shift_h:.1f}h. Requires human approval."
                        ),
                    }

                    # Guard check
                    guard_res = self.guard.validate(candidate)
                    candidate["feasible"] = guard_res.feasible
                    candidate["failed_constraints"] = guard_res.violated_constraints
                    candidate["rejection_reason"] = guard_res.rejection_reason
                    candidate["guard_warnings"] = guard_res.warnings
                    candidate["guard_constraint_checks"] = guard_res.constraint_checks
                    candidate["optimization_score"] = round(conf * 100.0, 2) if guard_res.feasible else 0.0

                    # Attach XAI explanation
                    candidate["xai"] = self.xai_service.explain_rescheduled_block(
                        candidate,
                        trigger_event=disruption_event,
                        constraints_checked=guard_res.constraint_checks,
                    )

                    rl_candidates.append(candidate)

                feasible_rl = [c for c in rl_candidates if c["feasible"]]
                rl_metadata["rl_used"] = len(feasible_rl) > 0
                rl_metadata["rl_evaluated_count"] = len(rl_candidates)
                rl_metadata["rl_feasible_count"] = len(feasible_rl)
                if not feasible_rl:
                    rl_metadata["fallback_reason"] = "All evaluated PPO candidates rejected by HardConstraintGuard."

            except Exception as exc:
                logger.warning("PPO inference error for %s: %s. Using deterministic.", affected_block_id, exc)
                rl_metadata["rl_error"] = str(exc)
                rl_metadata["fallback_reason"] = f"Inference error: {exc}"
        else:
            rl_metadata["fallback_reason"] = _rl_load_error or "Model not loaded"

        # 3. Always run deterministic engine (provides reliable baseline + alternatives)
        det_options = self.engine.generate_reschedule_options(disruption_event, affected_block)
        for opt in det_options:
            opt.setdefault("scoring_mode", "deterministic_prototype")
            if "proposed_start_time" in opt and "start_time" not in opt:
                opt["start_time"] = opt["proposed_start_time"]
            if "proposed_end_time" in opt and "end_time" not in opt:
                opt["end_time"] = opt["proposed_end_time"]
            if "recommended_window" not in opt and "proposed_start_time" in opt:
                st = opt["proposed_start_time"][-8:-3] if len(opt["proposed_start_time"]) >= 16 else ""
                et = opt["proposed_end_time"][-8:-3] if len(opt["proposed_end_time"]) >= 16 else ""
                opt["recommended_window"] = f"{st} – {et}"
            if "new_block_id" not in opt:
                opt["new_block_id"] = opt["option_id"]

            # Attach XAI explanation to deterministic candidates too
            opt["xai"] = self.xai_service.explain_rescheduled_block(
                opt,
                trigger_event=disruption_event,
                constraints_checked=opt.get("guard_constraint_checks", {}),
            )

        # Merge options: Feasible RL options first, then deterministic options, then rejected RL options for audit
        all_options = []
        feasible_rl_opts = [c for c in rl_candidates if c["feasible"]]
        infeasible_rl_opts = [c for c in rl_candidates if not c["feasible"]]

        all_options.extend(feasible_rl_opts)
        all_options.extend(det_options)
        all_options.extend(infeasible_rl_opts)

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
            "impact_assessment": impact_assessment.to_dict(),
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
        Record human approval of a rescheduling candidate and actively update the operational plan.
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

        original_block_id = option_id.split("-")[0] if "-" in option_id else option_id
        plan_updated = False
        new_start = None
        new_end = None

        # Actively update weekly_block_plan.csv upon approval
        try:
            if self.weekly_repo.file_exists():
                df = self.weekly_repo.read_csv()
                if "block_id" in df.columns and len(df) > 0:
                    matches = df[df["block_id"] == original_block_id]
                    if len(matches) > 0:
                        row_idx = matches.index[0]
                        current_ver = int(float(df.at[row_idx, "plan_version"] if "plan_version" in df.columns else 1))
                        df.at[row_idx, "status"] = "RESCHEDULED"
                        df.at[row_idx, "plan_version"] = current_ver + 1
                        df.at[row_idx, "reschedule_option_id"] = option_id
                        df.at[row_idx, "rescheduled_at"] = datetime.now().isoformat()
                        self.weekly_repo.write_csv(df)
                        plan_updated = True

                        # Log plan version transition
                        self.version_repo.append_rows([{
                            "plan_run_id": df.at[row_idx, "plan_run_id"] if "plan_run_id" in df.columns else f"RUN-{datetime.now().strftime('%Y%m%d')}",
                            "block_id": original_block_id,
                            "plan_version": current_ver + 1,
                            "horizon": "WEEKLY",
                            "status": "RESCHEDULED",
                            "start_time": df.at[row_idx, "start_time"] if "start_time" in df.columns else "",
                            "end_time": df.at[row_idx, "end_time"] if "end_time" in df.columns else "",
                            "created_at": datetime.now().isoformat(),
                            "source": "rescheduler_approval",
                            "source_record_id": option_id,
                            "reason": f"Approved rescheduling candidate {option_id} by {actor}",
                        }])
        except Exception as exc:
            logger.warning("Could not update weekly block plan during reschedule approval: %s", exc)

        log_entry = {
            "reschedule_id": option_id,
            "disruption_event_id": original_block_id,
            "original_block_id": original_block_id,
            "new_block_id": option_id,
            "status": "ACCEPTED",
            "accepted_by": actor,
            "plan_updated": plan_updated,
            "timestamp": datetime.now().isoformat(),
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
            new_value=f"ACCEPTED (plan_updated={plan_updated})",
        )
        return log_entry


# Backward compatibility alias
ReschedulerService = ReschedulingService
