"""
Hard Constraint Guard — RailBlock AI

Intercepts RL candidate actions before human presentation.
Validates candidates against non-negotiable operational constraints.

Guard Architecture:
  RL Agent -> Candidate Proposal -> HardConstraintGuard -> XAI -> Human Approval -> Execution

If guard PASSES: candidate is marked feasible=True and queued for human approval.
If guard FAILS:  candidate is rejected with explicit rejection_reason and the system
                 triggers deterministic fallback.

This module NEVER executes plan modifications.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Constraint thresholds ────────────────────────────────────────────────────
_TRAFFIC_HARD_LIMIT = 0.85           # Above this: passenger conflict risk
_WEATHER_SRS_EXCLUSION = 75.0        # Above this: severe weather exclusion
_MIN_WINDOW_MINUTES = 30.0           # Minimum viable possession window
_MAX_CREW_SHIFT_HOURS = 12.0         # Maximum crew consecutive hours
_MAX_DEFERRED_HIGH_PRIORITY = 0      # High-priority (MDPS>85) tasks CANNOT be deferred
_SUPPORTED_MACHINE_TYPES = {
    "TAMPING_MACHINE", "RAIL_GRINDING_MACHINE", "BCM",
    "OHE_TOWER_WAGON", "TRACK_RECORDING_CAR", "WEED_KILLING_TRAIN",
    "ULTRASONIC_TEST_CAR", "MANUAL_GANG",
}


@dataclass
class ConstraintCheckResult:
    feasible: bool
    violated_constraints: List[str] = field(default_factory=list)
    rejection_reason: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    constraint_checks: Dict[str, str] = field(default_factory=dict)  # "PASS" / "FAIL" / "WARN"


class HardConstraintGuard:
    """
    Non-negotiable constraint validator for RL-proposed rescheduling actions.

    Validates:
        1. Traffic density < 0.85 (train conflict avoidance)
        2. Weather SRS < 75.0 (severe weather exclusion)
        3. Possession window >= 30 minutes (minimum operational viability)
        4. Machine availability (required machine must be available)
        5. Crew availability and shift hour limits
        6. High-priority task deferral prohibition (MDPS > 85 cannot be cancelled)

    Usage:
        guard = HardConstraintGuard()
        result = guard.validate(candidate)
        if result.feasible:
            # proceed to XAI + human approval queue
        else:
            # trigger deterministic fallback
    """

    def validate(self, candidate: Dict[str, Any]) -> ConstraintCheckResult:
        """
        Validate an RL rescheduling candidate against all hard constraints.

        Parameters
        ----------
        candidate : dict
            Rescheduling candidate dict. Expected keys (all optional with safe defaults):
                traffic_density (float), weather_risk_score (float),
                duration_minutes (float), machine_available (bool),
                crew_available (bool), priority_score (float),
                action_type (str — "delay"|"shift"|"reallocate"|"cancel"|"shorten"),
                required_machine_type (str), crew_shift_hours (float)

        Returns
        -------
        ConstraintCheckResult
        """
        checks: Dict[str, str] = {}
        violations: List[str] = []
        warnings: List[str] = []

        action_type = str(candidate.get("action_type", "delay")).lower()
        traffic = float(candidate.get("traffic_density", 0.5))
        weather_srs = float(candidate.get("weather_risk_score", 0.0))
        window_min = float(candidate.get("duration_minutes", 120.0))
        machine_avail = bool(candidate.get("machine_available", True))
        crew_avail = bool(candidate.get("crew_available", True))
        priority = float(candidate.get("priority_score", candidate.get("original_criticality_score", 70.0)))
        req_machine = str(candidate.get("required_machine_type", "MANUAL_GANG"))
        crew_shift_hours = float(candidate.get("crew_shift_hours", 8.0))

        # ── Constraint 1: Train timetable conflict (traffic density) ─────────
        if traffic >= _TRAFFIC_HARD_LIMIT:
            checks["traffic_conflict"] = "FAIL"
            violations.append(
                f"Traffic density {traffic:.2f} >= {_TRAFFIC_HARD_LIMIT} hard limit "
                f"(passenger train conflict risk)"
            )
        elif traffic >= 0.70:
            checks["traffic_conflict"] = "WARN"
            warnings.append(f"Traffic density {traffic:.2f} is elevated — monitor for delays")
        else:
            checks["traffic_conflict"] = "PASS"

        # ── Constraint 2: Severe weather exclusion (SRS gate) ────────────────
        if weather_srs >= _WEATHER_SRS_EXCLUSION:
            checks["weather_srs"] = "FAIL"
            violations.append(
                f"Seasonal Risk Score {weather_srs:.1f} >= {_WEATHER_SRS_EXCLUSION} "
                f"exclusion threshold (severe weather hazard)"
            )
        elif weather_srs >= 55.0:
            checks["weather_srs"] = "WARN"
            warnings.append(f"SRS {weather_srs:.1f} — elevated weather risk, monitor forecast")
        else:
            checks["weather_srs"] = "PASS"

        # ── Constraint 3: Minimum possession window ──────────────────────────
        if window_min < _MIN_WINDOW_MINUTES:
            checks["window_feasibility"] = "FAIL"
            violations.append(
                f"Proposed possession window {window_min:.0f} min < {_MIN_WINDOW_MINUTES:.0f} min minimum"
            )
        else:
            checks["window_feasibility"] = "PASS"

        # ── Constraint 4: Machine availability ──────────────────────────────
        if not machine_avail:
            checks["machine_availability"] = "FAIL"
            violations.append(
                f"Required machine ({req_machine}) not available at proposed window"
            )
        elif req_machine not in _SUPPORTED_MACHINE_TYPES:
            checks["machine_availability"] = "WARN"
            warnings.append(f"Machine type '{req_machine}' not in canonical type list — verify")
        else:
            checks["machine_availability"] = "PASS"

        # ── Constraint 5: Crew availability and shift limits ────────────────
        if not crew_avail:
            checks["crew_availability"] = "FAIL"
            violations.append("Gang crew not available at proposed window (shift conflict or shortage)")
        elif crew_shift_hours > _MAX_CREW_SHIFT_HOURS:
            checks["crew_availability"] = "FAIL"
            violations.append(
                f"Crew shift {crew_shift_hours:.1f}h exceeds {_MAX_CREW_SHIFT_HOURS:.0f}h safety limit"
            )
        else:
            checks["crew_availability"] = "PASS"

        # ── Constraint 6: High-priority task deferral prohibition ────────────
        if action_type in ("cancel", "defer", "cancel_candidate") and priority >= 85.0:
            checks["priority_deferral"] = "FAIL"
            violations.append(
                f"Cannot defer/cancel high-priority task (MDPS={priority:.1f} >= 85.0). "
                f"Defect escalation risk."
            )
        else:
            checks["priority_deferral"] = "PASS"

        feasible = len(violations) == 0

        rejection_reason = None
        if not feasible:
            rejection_reason = "; ".join(violations[:2])  # top 2 reasons for brevity
            logger.info(
                "HardConstraintGuard REJECT | action=%s | violations=%s",
                action_type, violations,
            )
        else:
            if warnings:
                logger.info("HardConstraintGuard PASS (with warnings) | action=%s | %s", action_type, warnings)
            else:
                logger.debug("HardConstraintGuard PASS | action=%s", action_type)

        return ConstraintCheckResult(
            feasible=feasible,
            violated_constraints=violations,
            rejection_reason=rejection_reason,
            warnings=warnings,
            constraint_checks=checks,
        )

    def validate_batch(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate a list of candidates. Each candidate dict is augmented in-place
        with guard_result fields and returned.

        Returns
        -------
        list of candidates annotated with guard validation results
        """
        for cand in candidates:
            result = self.validate(cand)
            cand["guard_feasible"] = result.feasible
            cand["guard_violations"] = result.violated_constraints
            cand["guard_rejection_reason"] = result.rejection_reason
            cand["guard_warnings"] = result.warnings
            cand["guard_constraint_checks"] = result.constraint_checks
        return candidates
