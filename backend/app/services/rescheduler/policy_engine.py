"""
Self-Healing Hybrid Rescheduler — Policy Engine for RailBlock AI.

Generates typed candidate actions (Delay / Shift / Reallocate), validates EVERY candidate
against the operational ConstraintEngine, rejects infeasible candidates, scores the
feasible set, and returns a ranked list.

IMPORTANT:
- RL model is not yet trained. Rescheduler is deterministic/prototype.
- Scoring is clearly labelled as deterministic scoring, not RL.
- No candidate is returned as "valid" without passing all hard constraints.
- Human approval is required before any plan update (enforced in rescheduler_service.py).
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from app.services.optimization.constraints import ConstraintEngine

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Traffic density thresholds per time window (deterministic estimates)
# These approximate section traffic loads based on time-of-day.
# Real values should come from the traffic timetable in production.
# ─────────────────────────────────────────────────────────────
_TRAFFIC_BY_HOUR = {
    range(0, 5): 0.15,    # midnight–early morning: very low
    range(5, 8): 0.55,    # early morning peak build-up
    range(8, 12): 0.82,   # morning peak
    range(12, 15): 0.60,  # midday moderate
    range(15, 20): 0.85,  # afternoon/evening peak
    range(20, 23): 0.45,  # late evening
    range(23, 24): 0.20,  # late night
}


def _estimate_traffic_density(dt: datetime) -> float:
    """Return estimated traffic density for a given datetime based on hour-of-day."""
    hour = dt.hour
    for hour_range, density in _TRAFFIC_BY_HOUR.items():
        if hour in hour_range:
            return density
    return 0.5


def _score_candidate(candidate: dict, feasibility_result: dict) -> float:
    """
    Deterministic scoring for feasible rescheduler candidates.

    Scoring considers (all deterministic — no RL):
        - Traffic impact: lower traffic density → higher score
        - Time deviation: smaller shift from original → higher score
        - Priority preservation: based on how far the maintenance urgency is preserved
        - Spatial feasibility: confirmed mappable section adds bonus

    Returns a score in [0, 100].

    This is labelled DETERMINISTIC_PROTOTYPE — not RL inference.
    """
    action_type = candidate.get("action_type", "delay")
    traffic_density = candidate.get("traffic_density", 0.5)
    shift_hours = candidate.get("shift_from_original_hours", 24.0)
    criticality = candidate.get("original_criticality_score", 70.0)

    # Traffic component: reward low-traffic windows
    traffic_score = max(0.0, (1.0 - traffic_density) * 40.0)

    # Delay penalty: penalize longer delays from original planned time
    delay_penalty = min(shift_hours / 48.0, 1.0) * 20.0

    # Criticality preservation: high-criticality tasks should be rescheduled quickly
    criticality_component = min(criticality / 100.0, 1.0) * 25.0

    # Action type bonus: Delay is cheapest, Shift is moderate, Reallocate is expensive
    action_bonuses = {"delay": 15.0, "shift": 10.0, "reallocate": 5.0}
    action_bonus = action_bonuses.get(action_type, 5.0)

    raw = traffic_score - delay_penalty + criticality_component + action_bonus
    return round(max(0.0, min(100.0, raw)), 2)


class ReschedulerEngine:
    """
    Deterministic rescheduler engine.

    Generates candidate actions, validates each against the ConstraintEngine,
    scores only feasible candidates, and returns a ranked list.

    No candidate is returned as valid without passing all hard constraints.

    RL status: NOT IMPLEMENTED — deterministic scoring used.
    """

    ENGINE_VERSION = "1.1.0-deterministic-prototype"
    SCORING_MODE = "deterministic_prototype"

    def __init__(self):
        self.constraint_engine = ConstraintEngine()

    def generate_reschedule_options(
        self,
        disruption_event: dict,
        affected_block: dict,
    ) -> list:
        """
        Full rescheduler pipeline for a disrupted block:

            1. Generate 3 typed candidates (delay / shift / reallocate)
            2. Validate each candidate against the ConstraintEngine
            3. Reject infeasible candidates (include them in response with feasible=False)
            4. Score feasible candidates
            5. Rank feasible candidates by score (descending)
            6. Return all candidates with feasibility status — frontend shows only feasible

        Args:
            disruption_event: dict with event_id, section_id, severity, event_type
            affected_block: dict with block_id, section_id, criticality_score,
                            original_start_time, duration_minutes, traffic_density,
                            department, required_machine_type

        Returns:
            list of candidate dicts, sorted feasible-first then by score
        """
        now_dt = datetime.now()
        sec_id = disruption_event.get("section_id", affected_block.get("section_id", "SEC_001"))
        block_id = affected_block.get("block_id", "BLOCK_UNKNOWN")
        criticality = float(affected_block.get("criticality_score", 70.0))
        orig_duration = float(affected_block.get("duration_minutes", 180.0))
        base_traffic = float(affected_block.get("traffic_density", 0.6))

        candidates = self._generate_candidates(
            now_dt, block_id, sec_id, criticality, orig_duration, base_traffic, affected_block
        )

        validated = []
        for cand in candidates:
            feasibility = self.constraint_engine.check_feasibility_single(cand)
            cand["feasibility_check"] = feasibility
            cand["feasible"] = feasibility["feasible"]
            cand["failed_constraints"] = feasibility["failed_constraints"]
            cand["rejection_reason"] = feasibility["rejection_reason"]
            cand["feasibility_explanation"] = feasibility["feasibility_explanation"]

            if feasibility["feasible"]:
                cand["optimization_score"] = _score_candidate(cand, feasibility)
            else:
                cand["optimization_score"] = 0.0
                logger.info(
                    "Rescheduler: candidate %s REJECTED — failed constraints: %s",
                    cand["option_id"],
                    feasibility["failed_constraints"],
                )

            validated.append(cand)

        # Sort: feasible candidates first, then by score descending
        validated.sort(key=lambda c: (not c["feasible"], -c["optimization_score"]))

        feasible_count = sum(1 for c in validated if c["feasible"])
        logger.info(
            "Rescheduler: %d/%d candidates feasible for block %s",
            feasible_count, len(validated), block_id,
        )

        return validated

    def _generate_candidates(
        self,
        now_dt: datetime,
        block_id: str,
        sec_id: str,
        criticality: float,
        orig_duration: float,
        base_traffic: float,
        affected_block: dict,
    ) -> list[dict]:
        """
        Build the 3 typed rescheduler candidates with full constraint-evaluable fields.

        Action types:
            delay      — shift start by 2 hours, same section, same resources
            shift      — shift to night window (low traffic), same section
            reallocate — move to next day, allows machine reallocation

        Each candidate includes all fields required by check_feasibility_single().
        """
        req_machine = affected_block.get("required_machine_type", "TAMPING_MACHINE")
        req_crew_count = int(affected_block.get("required_crew_count", 2))
        spatial_status = affected_block.get("spatial_mapping_status", "MAPPED")
        chainage_km = affected_block.get("mapped_chainage_km", 12.5)

        # ── Option A: Delay — immediate +2hr shift ──────────────────────────
        a_start = now_dt + timedelta(hours=2)
        a_end = a_start + timedelta(minutes=orig_duration)
        a_traffic = _estimate_traffic_density(a_start)
        # Machine/crew: assume same resources carry over (conservative: not always available)
        a_machine = a_traffic < 0.80  # machines tied to traffic windows
        a_crew = req_crew_count <= 3

        option_a: dict[str, Any] = {
            "option_id": f"{block_id}-RESCHED-A-{uuid.uuid4().hex[:6].upper()}",
            "action_type": "delay",
            "original_block_id": block_id,
            "section_id": sec_id,
            "proposed_start_time": a_start.strftime("%Y-%m-%d %H:%M:%S"),
            "proposed_end_time": a_end.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_minutes": orig_duration,
            "shift_from_original_hours": 2.0,
            "traffic_density": a_traffic,
            "machine_available": a_machine,
            "crew_available": a_crew,
            "mapped_chainage_km": chainage_km,
            "spatial_mapping_status": spatial_status,
            "required_machine_type": req_machine,
            "required_crew_count": req_crew_count,
            "original_criticality_score": criticality,
            "reason": (
                f"Option A (Delay): Shift block start by 2 hours. "
                f"Estimated traffic density: {a_traffic:.2f}. "
                f"Machine available: {a_machine}. Crew available: {a_crew}."
            ),
            "scoring_mode": self.SCORING_MODE,
        }

        # ── Option B: Shift — night maintenance window ──────────────────────
        # Find the next hour-of-day with traffic < 0.30 (night window ~01:00)
        b_start = now_dt.replace(hour=1, minute=0, second=0, microsecond=0) + timedelta(days=1)
        if b_start < now_dt + timedelta(hours=3):
            b_start += timedelta(days=1)
        b_end = b_start + timedelta(minutes=orig_duration)
        b_traffic = _estimate_traffic_density(b_start)
        b_machine = True   # Night windows typically have machine availability
        b_crew = req_crew_count <= 4  # Night shift crews have higher limit

        option_b: dict[str, Any] = {
            "option_id": f"{block_id}-RESCHED-B-{uuid.uuid4().hex[:6].upper()}",
            "action_type": "shift",
            "original_block_id": block_id,
            "section_id": sec_id,
            "proposed_start_time": b_start.strftime("%Y-%m-%d %H:%M:%S"),
            "proposed_end_time": b_end.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_minutes": orig_duration,
            "shift_from_original_hours": round((b_start - now_dt).total_seconds() / 3600, 1),
            "traffic_density": b_traffic,
            "machine_available": b_machine,
            "crew_available": b_crew,
            "mapped_chainage_km": chainage_km,
            "spatial_mapping_status": spatial_status,
            "required_machine_type": req_machine,
            "required_crew_count": req_crew_count,
            "original_criticality_score": criticality,
            "reason": (
                f"Option B (Shift): Move block to night maintenance window "
                f"({b_start.strftime('%Y-%m-%d %H:%M')}). "
                f"Estimated traffic density: {b_traffic:.2f}. Minimises passenger train impact."
            ),
            "scoring_mode": self.SCORING_MODE,
        }

        # ── Option C: Reallocate — next-day consolidated window ─────────────
        c_start = (now_dt + timedelta(days=1)).replace(hour=2, minute=0, second=0, microsecond=0)
        c_end = c_start + timedelta(minutes=orig_duration)
        c_traffic = _estimate_traffic_density(c_start)
        # Reallocate allows machine repositioning — machine always available with 24hr notice
        c_machine = True
        # Crew: larger window allows planning, but overtime rules apply after 12hr
        c_crew = True

        option_c: dict[str, Any] = {
            "option_id": f"{block_id}-RESCHED-C-{uuid.uuid4().hex[:6].upper()}",
            "action_type": "reallocate",
            "original_block_id": block_id,
            "section_id": sec_id,
            "proposed_start_time": c_start.strftime("%Y-%m-%d %H:%M:%S"),
            "proposed_end_time": c_end.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_minutes": orig_duration,
            "shift_from_original_hours": round((c_start - now_dt).total_seconds() / 3600, 1),
            "traffic_density": c_traffic,
            "machine_available": c_machine,
            "crew_available": c_crew,
            "mapped_chainage_km": chainage_km,
            "spatial_mapping_status": spatial_status,
            "required_machine_type": req_machine,
            "required_crew_count": req_crew_count,
            "original_criticality_score": criticality,
            "reason": (
                f"Option C (Reallocate): Next-day consolidated mega-block at "
                f"{c_start.strftime('%Y-%m-%d %H:%M')}. "
                f"Allows machine repositioning and multi-department consolidation. "
                f"Estimated traffic density: {c_traffic:.2f}."
            ),
            "scoring_mode": self.SCORING_MODE,
        }

        return [option_a, option_b, option_c]
