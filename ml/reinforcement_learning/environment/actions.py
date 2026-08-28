"""
RL Environment Action Definitions — RailBlock AI

STATUS: SCAFFOLDING ONLY — training not yet implemented.
"""
from enum import IntEnum


class BlockAction(IntEnum):
    """
    Discrete action space for the block rescheduling RL agent.

    Actions:
        KEEP_SCHEDULE      (0): Accept the current block window as-is.
        DELAY_BLOCK        (1): Shift block start by +1 traffic window.
        MOVE_BLOCK         (2): Relocate block to the next available low-traffic window.
        SHORTEN_BLOCK      (3): Reduce block duration to fit within constraint window.
        CANCEL_CANDIDATE   (4): Remove this block candidate from the plan entirely.

    These map to the three deterministic options in the current prototype
    (policy_engine.py) plus explicit cancel/shorten actions.
    """
    KEEP_SCHEDULE = 0
    DELAY_BLOCK = 1
    MOVE_BLOCK = 2
    SHORTEN_BLOCK = 3
    CANCEL_CANDIDATE = 4

    @staticmethod
    def describe(action: int) -> str:
        descriptions = {
            0: "Keep current schedule unchanged",
            1: "Delay block by one traffic window",
            2: "Move block to next low-traffic window",
            3: "Shorten block duration to fit constraint window",
            4: "Cancel/reject this block candidate",
        }
        return descriptions.get(action, "Unknown action")


# Reward shaping constants (conceptual — not yet used in training)
REWARD_MAINTENANCE_COMPLETE = +10.0
REWARD_HIGH_PRIORITY_COMPLETE = +15.0
REWARD_RESOURCE_UTILIZATION = +2.0
PENALTY_TRAIN_DISRUPTION = -5.0
PENALTY_DELAY_MINUTE = -0.1
PENALTY_INFEASIBLE_ACTION = -20.0
PENALTY_SAFETY_VIOLATION = -50.0
PENALTY_EXCESSIVE_RESCHEDULING = -3.0
