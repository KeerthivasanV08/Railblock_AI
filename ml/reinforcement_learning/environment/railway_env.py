"""
Gymnasium-compatible Railway Disruption Simulation Environment — RailBlock AI.

Simulates the operational state of a maintenance block under disruption,
allowing an offline RL agent (PPO) to learn optimal rescheduling policies.
"""

from typing import Dict, Any, Tuple, Optional
import numpy as np

from ml.reinforcement_learning.environment.actions import (
    BlockAction,
    REWARD_MAINTENANCE_COMPLETE,
    REWARD_HIGH_PRIORITY_COMPLETE,
    REWARD_RESOURCE_UTILIZATION,
    PENALTY_TRAIN_DISRUPTION,
    PENALTY_DELAY_MINUTE,
    PENALTY_INFEASIBLE_ACTION,
    PENALTY_SAFETY_VIOLATION,
    PENALTY_EXCESSIVE_RESCHEDULING,
)
from ml.reinforcement_learning.environment.state import BlockPlanState


class Space:
    """Lightweight Gym-like space container to avoid strict external gym dependency."""
    def __init__(self, shape: Tuple[int, ...], dtype=np.float32):
        self.shape = shape
        self.dtype = dtype

    def sample(self):
        return np.random.uniform(0.0, 1.0, size=self.shape).astype(self.dtype)


class DiscreteSpace:
    def __init__(self, n: int):
        self.n = n

    def sample(self):
        return int(np.random.randint(0, self.n))


class RailwayDisruptionEnv:
    """
    Simulation environment for railway block rescheduling under operational disruptions.

    State: 12-dimensional continuous feature vector (BlockPlanState).
    Actions: 5 discrete rescheduling actions (BlockAction).
    """

    def __init__(self, max_steps_per_episode: int = 5, random_seed: Optional[int] = 42):
        self.observation_space = Space(shape=(12,), dtype=np.float32)
        self.action_space = DiscreteSpace(n=5)
        self.max_steps = max_steps_per_episode
        self.current_step = 0
        self.rng = np.random.RandomState(random_seed)
        self.state: Optional[BlockPlanState] = None

    def reset(self, seed: Optional[int] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Resets environment to a new simulated disruption scenario.
        """
        if seed is not None:
            self.rng = np.random.RandomState(seed)

        self.current_step = 0

        # Generate a realistic disruption context
        traffic = float(self.rng.choice([0.25, 0.45, 0.65, 0.85, 0.92]))
        delay_min = float(self.rng.choice([0.0, 30.0, 45.0, 60.0, 90.0]))
        priority = float(self.rng.uniform(40.0, 98.0))
        machine_ok = bool(self.rng.rand() > 0.15)
        crew_ok = bool(self.rng.rand() > 0.12)
        weather_risk = float(self.rng.choice([15.0, 25.0, 38.0, 55.0, 82.0]))
        hour = int(self.rng.randint(0, 24))

        self.state = BlockPlanState(
            traffic_density=traffic,
            remaining_window_min=180.0,
            delay_magnitude_min=delay_min,
            overdue_tasks_count=int(self.rng.randint(0, 5)),
            machine_available=machine_ok,
            crew_available=crew_ok,
            weather_risk_score=weather_risk,
            section_vulnerability=float(self.rng.uniform(0.3, 0.85)),
            asset_type_code=float(self.rng.choice([0.0, 0.5, 1.0])),
            priority_score=priority,
            hour_of_day=hour,
            days_deferred=int(self.rng.randint(0, 3)),
        )

        obs = self.state.to_vector()
        info = {
            "scenario": "disruption_simulation",
            "traffic_density": traffic,
            "delay_min": delay_min,
            "weather_risk": weather_risk,
            "priority": priority,
        }
        return obs, info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """
        Executes an action, evaluates operational constraints, computes reward, and returns transition.
        """
        self.current_step += 1
        terminated = False
        truncated = bool(self.current_step >= self.max_steps)

        reward = 0.0
        feasible = True
        violation_reason = None

        st = self.state

        # Hard Weather Constraint Gate: If weather >= 75, keeping or shortening in same section is a severe hazard
        if st.weather_risk_score >= 75.0 and action in (BlockAction.KEEP_SCHEDULE, BlockAction.SHORTEN_BLOCK):
            reward += PENALTY_SAFETY_VIOLATION
            feasible = False
            violation_reason = "Severe weather hazard (SRS >= 75.0)"
            terminated = True

        elif action == BlockAction.KEEP_SCHEDULE:
            # Only valid if no train delay conflicts and resources available
            if st.delay_magnitude_min > 20.0:
                reward += PENALTY_TRAIN_DISRUPTION - (st.delay_magnitude_min * 0.1)
                feasible = False
                violation_reason = "Train delay timetable conflict"
            elif not st.machine_available or not st.crew_available:
                reward += PENALTY_INFEASIBLE_ACTION
                feasible = False
                violation_reason = "Required resource unavailable"
            else:
                reward += REWARD_MAINTENANCE_COMPLETE
                if st.priority_score > 80.0:
                    reward += REWARD_HIGH_PRIORITY_COMPLETE
            terminated = True

        elif action == BlockAction.DELAY_BLOCK:
            # Shift by delay minutes (+30-60 min)
            if not st.machine_available or not st.crew_available:
                reward += PENALTY_INFEASIBLE_ACTION
                feasible = False
                violation_reason = "Resource unavailable at shifted window"
            elif st.traffic_density > 0.88:
                reward += PENALTY_TRAIN_DISRUPTION
                feasible = False
                violation_reason = "Shifted into peak traffic congestion"
            else:
                reward += REWARD_MAINTENANCE_COMPLETE - (st.delay_magnitude_min * PENALTY_DELAY_MINUTE)
                if st.priority_score > 80.0:
                    reward += REWARD_HIGH_PRIORITY_COMPLETE
            terminated = True

        elif action == BlockAction.MOVE_BLOCK:
            # Shift to low-traffic night slot (00:00 - 04:00)
            # Highly resilient, minimal traffic impact
            reward += REWARD_MAINTENANCE_COMPLETE + REWARD_RESOURCE_UTILIZATION
            if st.priority_score > 80.0:
                reward += REWARD_HIGH_PRIORITY_COMPLETE
            reward -= 2.0  # slight operational rescheduling friction
            terminated = True

        elif action == BlockAction.SHORTEN_BLOCK:
            # Compress window duration
            if st.priority_score > 90.0:
                # Critical work cannot be safely compressed without quality risk
                reward -= 5.0
            reward += (REWARD_MAINTENANCE_COMPLETE * 0.8)
            terminated = True

        elif action == BlockAction.CANCEL_CANDIDATE:
            # Defer / cancel
            if st.priority_score > 85.0:
                reward += PENALTY_INFEASIBLE_ACTION  # Critical task deferral heavily discouraged
                violation_reason = "Deferred high-criticality task"
            else:
                reward -= 2.0  # Low priority deferral is acceptable under pressure
            terminated = True

        obs = st.to_vector()
        info = {
            "feasible": feasible,
            "action_name": BlockAction.describe(action),
            "violation_reason": violation_reason,
            "step": self.current_step,
        }
        return obs, float(reward), terminated, truncated, info


# Backward compatibility alias
RailwayEnvStub = RailwayDisruptionEnv
