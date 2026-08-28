"""
Reinforcement Learning Environment Scaffolding for RailBlock AI.

STATUS: SCAFFOLDING ONLY — not yet implemented.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class RailwayState:
    section_id: str
    traffic_density: float
    available_machines: int
    available_crews: int
    active_block_minutes: float
    overdue_critical_count: int


class RailwayEnvStub:
    """
    Stub Gym-compatible environment for the railway maintenance block rescheduler.

    Expected state dimensions (future implementation):
    - section_id (one-hot encoded)
    - traffic_density (float 0..1)
    - available_machines (int)
    - available_crews (int)
    - active_block_minutes (float)
    - overdue_critical_count (int)

    Expected action space:
    - 0: Accept Option A (immediate shift)
    - 1: Accept Option B (night window)
    - 2: Accept Option C (next-day consolidation)
    - 3: Defer to next planning cycle

    Expected reward signal:
    - +10 if block completes successfully
    - -5 per passenger train delay minute
    - -20 if block is abandoned due to constraint violation
    """

    def __init__(self):
        self.status = "NOT_IMPLEMENTED"
        self.observation_space_dim = 6
        self.action_space_n = 4

    def reset(self) -> Dict[str, Any]:
        raise NotImplementedError(
            "RL Environment is not yet implemented. "
            "Use the deterministic rescheduler in services/rescheduler/policy_engine.py instead."
        )

    def step(self, action: int):
        raise NotImplementedError(
            "RL Environment is not yet implemented. "
            "Use the deterministic rescheduler in services/rescheduler/policy_engine.py instead."
        )

    def render(self):
        raise NotImplementedError("RL Environment not yet implemented.")
