"""
RL Environment State Definition — RailBlock AI

STATUS: SCAFFOLDING ONLY — training not yet implemented.

State vector for the railway maintenance scheduling RL agent.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class BlockPlanState:
    """
    Encodes the current state of the railway maintenance scheduling environment.

    State dimensions (planned):
    - current_block_plan: list of scheduled tasks with their windows
    - train_traffic: traffic density per section per hour
    - live_delays: dict of section_id -> delay_minutes
    - resource_availability: machines and crews available per section
    - maintenance_urgency: criticality scores of pending tasks
    - disruption_state: active disruptions per section
    """
    section_ids: List[str] = field(default_factory=list)
    scheduled_task_ids: List[str] = field(default_factory=list)
    traffic_densities: List[float] = field(default_factory=list)
    live_delays: List[float] = field(default_factory=list)
    available_machines: List[int] = field(default_factory=list)
    available_crews: List[int] = field(default_factory=list)
    maintenance_urgency_scores: List[float] = field(default_factory=list)
    disruption_flags: List[bool] = field(default_factory=list)
    current_hour: int = 0
    current_day: int = 0

    def to_vector(self) -> List[float]:
        """
        Flatten state to a numeric vector for RL input.
        NOT YET IMPLEMENTED — returns empty list.
        """
        raise NotImplementedError(
            "State vectorization not yet implemented. "
            "Implement this once RL training begins."
        )

    @staticmethod
    def dim() -> int:
        """Expected state vector dimension — to be defined during RL design phase."""
        raise NotImplementedError("State dimension not yet finalized.")
