"""
Reinforcement Learning Environment interface stub for RailBlock AI rescheduler.

STATUS: RL prototype/scaffolding — training not yet implemented.
"""

from typing import Dict, Any, List


class RailwayRLEnvironmentStub:
    """Scaffolding interface for future RL environment integration."""
    def __init__(self):
        self.status = "NOT_IMPLEMENTED"
        self.message = "RL prototype/scaffolding — training not yet implemented."

    def reset(self) -> Dict[str, Any]:
        raise NotImplementedError("RL training/environment is not yet implemented.")

    def step(self, action: int) -> tuple[Dict[str, Any], float, bool, Dict[str, Any]]:
        raise NotImplementedError("RL training/environment is not yet implemented.")
