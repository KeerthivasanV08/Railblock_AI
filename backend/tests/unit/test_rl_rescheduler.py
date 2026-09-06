"""
RL Rescheduler Unit Tests — RailBlock AI

Tests:
  1. RailwayDisruptionEnv — reset, step, observation shape, reward bounds
  2. HardConstraintGuard — rejection of unsafe actions, pass of safe candidates
  3. ReschedulingService — deterministic fallback when RL disabled
  4. XAI ExplainabilityService — explain_rescheduled_block structure
  5. PPO policy file (if trained) — load, inference shape, action validity
"""
import sys
from pathlib import Path

import numpy as np
import pytest

# ── Path bootstrap ─────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "backend"))

from ml.reinforcement_learning.environment.railway_env import RailwayDisruptionEnv
from ml.reinforcement_learning.environment.state import BlockPlanState
from ml.reinforcement_learning.environment.actions import BlockAction
from backend.app.services.rescheduler.hard_constraint_guard import HardConstraintGuard


# ═══════════════════════════════════════════════════════════════════
# 1. RailwayDisruptionEnv Tests
# ═══════════════════════════════════════════════════════════════════

class TestRailwayDisruptionEnv:
    def setup_method(self):
        self.env = RailwayDisruptionEnv(random_seed=42)

    def test_reset_returns_correct_shape(self):
        obs, info = self.env.reset()
        assert obs.shape == (12,), f"Expected (12,), got {obs.shape}"
        assert obs.dtype == np.float32

    def test_reset_returns_info_dict(self):
        obs, info = self.env.reset()
        assert isinstance(info, dict)
        assert "traffic_density" in info
        assert "priority" in info

    def test_reset_with_seed(self):
        obs1, _ = self.env.reset(seed=10)
        obs2, _ = RailwayDisruptionEnv(random_seed=10).reset()
        np.testing.assert_array_equal(obs1, obs2)

    def test_step_keep_schedule_feasible(self):
        """KEEP_SCHEDULE should pass for no-delay, resource-available scenario."""
        env = RailwayDisruptionEnv(random_seed=99)
        env.reset()
        # Force a safe state manually
        env.state = BlockPlanState(
            traffic_density=0.3,
            remaining_window_min=180.0,
            delay_magnitude_min=0.0,
            overdue_tasks_count=1,
            machine_available=True,
            crew_available=True,
            weather_risk_score=20.0,
            section_vulnerability=0.4,
            asset_type_code=0.0,
            priority_score=75.0,
            hour_of_day=2,
            days_deferred=0,
        )
        obs, reward, terminated, truncated, info = env.step(BlockAction.KEEP_SCHEDULE)
        assert obs.shape == (12,)
        assert info["feasible"] is True
        assert reward > 0  # should get maintenance complete reward

    def test_step_weather_violation(self):
        """Actions on severe weather (SRS >= 75) should be penalised and terminated."""
        env = RailwayDisruptionEnv(random_seed=0)
        env.reset()
        env.state = BlockPlanState(
            traffic_density=0.3,
            remaining_window_min=180.0,
            delay_magnitude_min=0.0,
            overdue_tasks_count=0,
            machine_available=True,
            crew_available=True,
            weather_risk_score=85.0,  # SEVERE
            section_vulnerability=0.5,
            asset_type_code=0.0,
            priority_score=70.0,
            hour_of_day=2,
            days_deferred=0,
        )
        obs, reward, terminated, truncated, info = env.step(BlockAction.KEEP_SCHEDULE)
        assert info["feasible"] is False
        assert reward <= -50.0  # PENALTY_SAFETY_VIOLATION
        assert terminated is True

    def test_step_all_actions_return_valid_tuple(self):
        """All 5 actions should return a valid (obs, reward, terminated, truncated, info) tuple."""
        for action in range(5):
            env = RailwayDisruptionEnv(random_seed=action + 100)
            env.reset()
            obs, reward, terminated, truncated, info = env.step(action)
            assert obs.shape == (12,)
            assert isinstance(reward, float)
            assert isinstance(terminated, bool)
            assert isinstance(truncated, bool)
            assert isinstance(info, dict)

    def test_reward_bounds_are_reasonable(self):
        """Rewards should fall within known realistic bounds."""
        rewards = []
        env = RailwayDisruptionEnv(random_seed=7)
        env.reset()
        for action in range(5):
            env.reset()
            _, reward, _, _, _ = env.step(action)
            rewards.append(reward)
        # Reward should be in range [-100, +100]
        for r in rewards:
            assert -100.0 <= r <= 100.0, f"Reward {r} out of expected range"

    def test_observation_space_properties(self):
        obs_space = self.env.observation_space
        assert obs_space.shape == (12,)
        sample = obs_space.sample()
        assert sample.shape == (12,)

    def test_action_space_properties(self):
        act_space = self.env.action_space
        assert act_space.n == 5
        sampled = act_space.sample()
        assert 0 <= sampled < 5

    def test_truncation_after_max_steps(self):
        """Episode should truncate after max_steps."""
        env = RailwayDisruptionEnv(max_steps_per_episode=2, random_seed=42)
        env.reset()
        for _ in range(2):
            _, _, terminated, truncated, _ = env.step(BlockAction.DELAY_BLOCK)
            if terminated or truncated:
                break
        assert terminated or truncated


# ═══════════════════════════════════════════════════════════════════
# 2. HardConstraintGuard Tests
# ═══════════════════════════════════════════════════════════════════

class TestHardConstraintGuard:
    def setup_method(self):
        self.guard = HardConstraintGuard()

    def _safe_candidate(self, **overrides):
        base = {
            "action_type": "delay",
            "traffic_density": 0.4,
            "weather_risk_score": 25.0,
            "duration_minutes": 120.0,
            "machine_available": True,
            "crew_available": True,
            "priority_score": 70.0,
            "required_machine_type": "TAMPING_MACHINE",
            "crew_shift_hours": 8.0,
        }
        base.update(overrides)
        return base

    def test_safe_candidate_passes(self):
        result = self.guard.validate(self._safe_candidate())
        assert result.feasible is True
        assert len(result.violated_constraints) == 0

    def test_high_traffic_rejected(self):
        cand = self._safe_candidate(traffic_density=0.90)
        result = self.guard.validate(cand)
        assert result.feasible is False
        assert any("traffic" in v.lower() for v in result.violated_constraints)

    def test_severe_weather_rejected(self):
        cand = self._safe_candidate(weather_risk_score=80.0)
        result = self.guard.validate(cand)
        assert result.feasible is False
        assert any("weather" in v.lower() or "srs" in v.lower() for v in result.violated_constraints)

    def test_short_window_rejected(self):
        cand = self._safe_candidate(duration_minutes=15.0)
        result = self.guard.validate(cand)
        assert result.feasible is False
        assert any("window" in v.lower() for v in result.violated_constraints)

    def test_machine_unavailable_rejected(self):
        cand = self._safe_candidate(machine_available=False)
        result = self.guard.validate(cand)
        assert result.feasible is False
        assert any("machine" in v.lower() for v in result.violated_constraints)

    def test_crew_unavailable_rejected(self):
        cand = self._safe_candidate(crew_available=False)
        result = self.guard.validate(cand)
        assert result.feasible is False
        assert any("crew" in v.lower() for v in result.violated_constraints)

    def test_crew_shift_hours_violation(self):
        cand = self._safe_candidate(crew_shift_hours=14.0)
        result = self.guard.validate(cand)
        assert result.feasible is False
        assert any("shift" in v.lower() for v in result.violated_constraints)

    def test_high_priority_cancel_rejected(self):
        cand = self._safe_candidate(action_type="cancel", priority_score=90.0)
        result = self.guard.validate(cand)
        assert result.feasible is False
        assert any("defer" in v.lower() or "cancel" in v.lower() or "priority" in v.lower()
                   for v in result.violated_constraints)

    def test_low_priority_cancel_passes(self):
        cand = self._safe_candidate(action_type="cancel", priority_score=60.0)
        result = self.guard.validate(cand)
        assert result.feasible is True

    def test_multiple_violations_collected(self):
        cand = self._safe_candidate(traffic_density=0.91, weather_risk_score=82.0)
        result = self.guard.validate(cand)
        assert result.feasible is False
        assert len(result.violated_constraints) >= 2

    def test_validate_batch_annotates_candidates(self):
        candidates = [self._safe_candidate(), self._safe_candidate(traffic_density=0.92)]
        result = self.guard.validate_batch(candidates)
        assert result[0]["guard_feasible"] is True
        assert result[1]["guard_feasible"] is False

    def test_rejection_reason_populated_on_fail(self):
        cand = self._safe_candidate(traffic_density=0.92)
        result = self.guard.validate(cand)
        assert result.rejection_reason is not None
        assert len(result.rejection_reason) > 0

    def test_warnings_on_elevated_traffic(self):
        cand = self._safe_candidate(traffic_density=0.75)
        result = self.guard.validate(cand)
        assert result.feasible is True
        assert len(result.warnings) > 0


# ═══════════════════════════════════════════════════════════════════
# 3. PPO Policy Artifact Tests (if artifact exists)
# ═══════════════════════════════════════════════════════════════════

_POLICY_PATH = _REPO_ROOT / "ml" / "reinforcement_learning" / "artifacts" / "ppo_rescheduler_v1.pt"


@pytest.mark.skipif(not _POLICY_PATH.exists(), reason="PPO artifact not yet trained")
class TestPPOPolicyArtifact:
    def test_policy_loads_without_error(self):
        import torch
        checkpoint = torch.load(_POLICY_PATH, map_location="cpu", weights_only=False)
        assert "model_state_dict" in checkpoint
        assert "config" in checkpoint
        assert "training_summary" in checkpoint

    def test_policy_config_correct(self):
        import torch
        checkpoint = torch.load(_POLICY_PATH, map_location="cpu", weights_only=False)
        cfg = checkpoint["config"]
        assert cfg["obs_dim"] == 12
        assert cfg["n_actions"] == 5
        assert cfg["hidden"] == 128

    def test_policy_training_completed(self):
        import torch
        checkpoint = torch.load(_POLICY_PATH, map_location="cpu", weights_only=False)
        summary = checkpoint["training_summary"]
        assert summary["total_episodes"] > 0
        assert summary["total_timesteps"] > 0

    def test_policy_inference_output_valid(self):
        """Policy should produce valid action in [0, 4] for a random state."""
        import torch
        import torch.nn as nn

        checkpoint = torch.load(_POLICY_PATH, map_location="cpu", weights_only=False)
        cfg = checkpoint["config"]
        obs_dim, n_actions, hidden = cfg["obs_dim"], cfg["n_actions"], cfg["hidden"]

        backbone = nn.Sequential(
            nn.Linear(obs_dim, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(),
        )
        actor = nn.Linear(hidden, n_actions)

        class MinimalPolicy(nn.Module):
            def __init__(self):
                super().__init__()
                self.backbone = backbone
                self.actor = actor
                self.critic = nn.Linear(hidden, 1)

        model = MinimalPolicy()
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()

        # 10 random observations
        for seed in range(10):
            env = RailwayDisruptionEnv(random_seed=seed)
            obs, _ = env.reset()
            obs_t = torch.tensor(obs, dtype=torch.float32).unsqueeze(0)
            with torch.no_grad():
                logits = model.actor(model.backbone(obs_t))
                action = int(torch.argmax(logits, dim=-1).item())
            assert 0 <= action <= 4, f"Invalid action {action} for obs seed {seed}"

    def test_runtime_copy_exists(self):
        runtime_path = _REPO_ROOT / "backend" / "app" / "ml" / "models" / "ppo_rescheduler_v1.pt"
        assert runtime_path.exists(), f"Runtime copy missing at {runtime_path}"


# ═══════════════════════════════════════════════════════════════════
# 4. XAI — explain_rescheduled_block
# ═══════════════════════════════════════════════════════════════════

class TestXAIExplainRescheduledBlock:
    def setup_method(self):
        sys.path.insert(0, str(_REPO_ROOT / "backend"))
        from app.services.xai.explanation_service import ExplainabilityService
        self.svc = ExplainabilityService()

    def _sample_candidate(self, **overrides):
        base = {
            "option_id": "BLK-001-RESCHED-A-ABCDEF",
            "action_type": "delay",
            "scoring_mode": "deterministic_prototype",
            "traffic_density": 0.45,
            "weather_risk_score": 28.0,
            "original_criticality_score": 75.0,
            "proposed_start_time": "2026-09-07 01:00:00",
            "feasible": True,
            "failed_constraints": [],
            "guard_constraint_checks": {
                "traffic_conflict": "PASS",
                "weather_srs": "PASS",
                "window_feasibility": "PASS",
                "machine_availability": "PASS",
                "crew_availability": "PASS",
                "priority_deferral": "PASS",
            },
            "guard_warnings": [],
        }
        base.update(overrides)
        return base

    def test_returns_required_keys(self):
        explanation = self.svc.explain_rescheduled_block(self._sample_candidate())
        required = [
            "option_id", "feasible", "decision_source", "triggering_event",
            "action_type", "action_rationale", "traffic_density", "weather_risk_score",
            "constraint_guard_checks", "human_approval_required",
        ]
        for key in required:
            assert key in explanation, f"Missing key: {key}"

    def test_deterministic_fallback_label(self):
        cand = self._sample_candidate(scoring_mode="deterministic_prototype")
        explanation = self.svc.explain_rescheduled_block(cand)
        assert "Deterministic" in explanation["decision_source"]

    def test_ppo_label_with_confidence(self):
        cand = self._sample_candidate(
            scoring_mode="ppo_reinforcement_learning",
            rl_confidence=0.72,
            rl_action_probs={"keep": 0.1, "delay": 0.72, "shift": 0.1, "shorten": 0.05, "cancel": 0.03},
        )
        explanation = self.svc.explain_rescheduled_block(cand)
        assert "PPO" in explanation["decision_source"]
        assert explanation["rl_explanation"] is not None

    def test_trigger_event_included(self):
        trigger = {"event_type": "Rail Fracture", "severity": "HIGH", "section_id": "SEC_012", "delay_minutes": 45}
        explanation = self.svc.explain_rescheduled_block(self._sample_candidate(), trigger_event=trigger)
        assert "Rail Fracture" in explanation["triggering_event"]

    def test_constraint_breakdown_has_all_checks(self):
        explanation = self.svc.explain_rescheduled_block(self._sample_candidate())
        checks = {c["constraint"]: c["result"] for c in explanation["constraint_guard_checks"]}
        assert len(checks) == 6  # all 6 constraints present

    def test_human_approval_always_required(self):
        explanation = self.svc.explain_rescheduled_block(self._sample_candidate())
        assert explanation["human_approval_required"] is True

    def test_high_weather_risk_assessment(self):
        cand = self._sample_candidate(weather_risk_score=78.0)
        explanation = self.svc.explain_rescheduled_block(cand)
        assert "SEVERE" in explanation["weather_assessment"]
