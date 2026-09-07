"""
Disruption Impact Assessment Engine for RailBlock AI.

Detects, classifies, and assesses operational disruptions affecting maintenance blocks:
  - LATE_TRAIN, EMERGENCY_DEFECT, RESOURCE_UNAVAILABLE, BLOCK_OVERRUN,
    CREW_DELAY, MACHINE_DELAY, WEATHER_DISRUPTION, TRAFFIC_SURGE,
    BLOCK_CANCELLATION, INFRASTRUCTURE_FAILURE.

Computes multi-dimensional impact scores:
  - Schedule impact (delay minutes, timetable conflict risk)
  - Resource impact (crew/machine unavailability, travel delay)
  - Maintenance impact (aggregate MDPS exposure of affected tasks)
  - Network impact (corridor congestion, section vulnerability)
  - Composite impact score [0.0, 100.0]
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DisruptionEventType(str, Enum):
    LATE_TRAIN = "LATE_TRAIN"
    EMERGENCY_DEFECT = "EMERGENCY_DEFECT"
    RESOURCE_UNAVAILABLE = "RESOURCE_UNAVAILABLE"
    BLOCK_OVERRUN = "BLOCK_OVERRUN"
    CREW_DELAY = "CREW_DELAY"
    MACHINE_DELAY = "MACHINE_DELAY"
    WEATHER_DISRUPTION = "WEATHER_DISRUPTION"
    TRAFFIC_SURGE = "TRAFFIC_SURGE"
    BLOCK_CANCELLATION = "BLOCK_CANCELLATION"
    INFRASTRUCTURE_FAILURE = "INFRASTRUCTURE_FAILURE"


# Normalized string mapper for backward compatibility with raw text types
_EVENT_TYPE_MAP = {
    "late train": DisruptionEventType.LATE_TRAIN,
    "train delay": DisruptionEventType.LATE_TRAIN,
    "emergency defect": DisruptionEventType.EMERGENCY_DEFECT,
    "rail fracture": DisruptionEventType.EMERGENCY_DEFECT,
    "machine failure": DisruptionEventType.MACHINE_DELAY,
    "machine breakdown": DisruptionEventType.MACHINE_DELAY,
    "resource unavailable": DisruptionEventType.RESOURCE_UNAVAILABLE,
    "crew delay": DisruptionEventType.CREW_DELAY,
    "block overrun": DisruptionEventType.BLOCK_OVERRUN,
    "weather disruption": DisruptionEventType.WEATHER_DISRUPTION,
    "traffic surge": DisruptionEventType.TRAFFIC_SURGE,
    "block cancellation": DisruptionEventType.BLOCK_CANCELLATION,
    "infrastructure failure": DisruptionEventType.INFRASTRUCTURE_FAILURE,
}


@dataclass
class DisruptionImpactAssessment:
    """Structured impact assessment for a disruption event affecting a block possession."""
    event_id: str
    event_type: str
    severity: str
    section_id: str
    affected_block_id: str
    schedule_delay_min: float = 0.0
    train_conflicts_count: int = 0
    resource_impact_score: float = 0.0      # [0, 100]
    maintenance_mdps_exposure: float = 0.0  # [0, 100]
    network_impact_score: float = 0.0       # [0, 100]
    composite_impact_score: float = 0.0     # [0, 100]
    impact_summary: str = ""
    requires_immediate_reschedule: bool = False
    affected_tasks: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DisruptionEngine:
    """
    Analyzes live operational feeds and evaluates multi-dimensional disruption impact.
    """

    SEVERITY_WEIGHTS = {
        "LOW": 0.25,
        "MEDIUM": 0.50,
        "HIGH": 0.75,
        "CRITICAL": 1.00,
    }

    def classify_event_type(self, raw_type: str) -> DisruptionEventType:
        cleaned = raw_type.strip().lower()
        if cleaned in _EVENT_TYPE_MAP:
            return _EVENT_TYPE_MAP[cleaned]
        try:
            return DisruptionEventType(raw_type.upper().replace(" ", "_"))
        except ValueError:
            return DisruptionEventType.LATE_TRAIN

    def assess_impact(
        self,
        event: Dict[str, Any],
        affected_block: Optional[Dict[str, Any]] = None,
        traffic_density: float = 0.5,
    ) -> DisruptionImpactAssessment:
        """
        Calculates a structured multi-dimensional impact assessment.
        """
        block = affected_block or {}
        event_id = str(event.get("event_id", "EVT-UNKNOWN"))
        raw_type = str(event.get("event_type", "Late Train"))
        classified_type = self.classify_event_type(raw_type)
        severity_str = str(event.get("severity", "Medium")).upper()
        severity_factor = self.SEVERITY_WEIGHTS.get(severity_str, 0.5)

        section_id = str(event.get("section_id") or block.get("section_id") or "SEC_001")
        affected_block_id = str(event.get("affected_block_id") or block.get("block_id") or "")
        delay_val = event.get("delay_minutes", event.get("delay_min", 0.0))
        delay_min = float(delay_val) if delay_val is not None else 0.0
        if delay_min == 0.0 and classified_type == DisruptionEventType.LATE_TRAIN:
            delay_min = 35.0  # default expected delay for uncalibrated late train

        # 1. Schedule impact
        window_duration = float(block.get("duration_minutes", 120.0))
        schedule_ratio = min(delay_min / max(30.0, window_duration), 2.0)
        train_conflicts = int(np.ceil(delay_min / 30.0)) if classified_type == DisruptionEventType.LATE_TRAIN else 0

        # 2. Resource impact score (0-100)
        machine_ok = bool(block.get("machine_available", True))
        crew_ok = bool(block.get("crew_available", True))
        resource_score = 0.0
        if classified_type in (DisruptionEventType.RESOURCE_UNAVAILABLE, DisruptionEventType.MACHINE_DELAY):
            resource_score = 85.0
        elif classified_type == DisruptionEventType.CREW_DELAY:
            resource_score = 75.0
        elif not machine_ok or not crew_ok:
            resource_score = 70.0
        else:
            resource_score = 20.0 * severity_factor

        # 3. Maintenance / MDPS exposure (0-100)
        mdps_val = block.get("priority_score", block.get("criticality_score", 70.0))
        mdps_exposure = float(mdps_val) if mdps_val is not None else 70.0
        overdue_cnt = int(block.get("overdue_tasks_count", 1))
        if overdue_cnt > 2:
            mdps_exposure = min(100.0, mdps_exposure * 1.15)

        # 4. Network impact score (0-100)
        traffic = float(block.get("traffic_density", traffic_density))
        weather_val = event.get("weather_risk_score", block.get("weather_risk_score", 30.0))
        weather_srs = float(weather_val) if weather_val is not None else 30.0
        network_score = float(np.clip(
            (traffic * 50.0) + (weather_srs * 0.3) + (20.0 * severity_factor),
            0.0, 100.0
        ))

        # Composite impact score [0, 100]:
        # Weighted combination of schedule, resource, maintenance criticality, and network pressure
        composite_score = float(np.clip(
            (schedule_ratio * 30.0) +
            (resource_score * 0.25) +
            (mdps_exposure * 0.25) +
            (network_score * 0.20),
            0.0, 100.0
        ))

        # Immediate reschedule triggered if composite score > 60 or emergency defect or block overrun
        requires_immediate = (
            composite_score >= 60.0
            or classified_type in (DisruptionEventType.EMERGENCY_DEFECT, DisruptionEventType.BLOCK_OVERRUN)
            or not machine_ok
        )

        summary = (
            f"{classified_type.value} on section {section_id} with severity {severity_str}. "
            f"Impact Score: {composite_score:.1f}/100 (Schedule delay: {delay_min:.0f}m, "
            f"MDPS exposure: {mdps_exposure:.1f}, Network pressure: {network_score:.1f}). "
            f"{'Immediate rescheduling required.' if requires_immediate else 'Monitor for possible adjustment.'}"
        )

        tasks = block.get("task_ids", [])
        if isinstance(tasks, str):
            tasks = [t.strip() for t in tasks.split(";") if t.strip()]

        return DisruptionImpactAssessment(
            event_id=event_id,
            event_type=classified_type.value,
            severity=severity_str,
            section_id=section_id,
            affected_block_id=affected_block_id,
            schedule_delay_min=delay_min,
            train_conflicts_count=train_conflicts,
            resource_impact_score=round(resource_score, 1),
            maintenance_mdps_exposure=round(mdps_exposure, 1),
            network_impact_score=round(network_score, 1),
            composite_impact_score=round(composite_score, 1),
            impact_summary=summary,
            requires_immediate_reschedule=requires_immediate,
            affected_tasks=tasks,
        )

    def detect_disruptions(
        self,
        disruptions_df: pd.DataFrame,
        delays_df: Optional[pd.DataFrame] = None,
        active_blocks_df: Optional[pd.DataFrame] = None
    ) -> list:
        """
        Analyzes live operational feeds and logs structured disruption events with assessments.
        """
        detected = []

        if disruptions_df is not None and len(disruptions_df) > 0:
            for idx, row in disruptions_df.iterrows():
                e_type = str(row.get("event_type", "Late Train"))
                sec_id = str(row.get("section_id", "SEC_001"))
                sev = str(row.get("severity", "Medium"))
                aff_block = str(row.get("affected_block_id", ""))
                event_id = str(row.get("event_id", f"DIS_{idx:04d}"))

                event_dict = {
                    "event_id": event_id,
                    "event_type": e_type,
                    "section_id": sec_id,
                    "severity": sev,
                    "affected_block_id": aff_block,
                    "delay_minutes": float(row.get("delay_minutes", 0.0)),
                    "weather_risk_score": float(row.get("weather_risk_score", 30.0)),
                }

                assessment = self.assess_impact(event_dict)

                detected.append({
                    "event_id": event_id,
                    "event_type": assessment.event_type,
                    "section_id": sec_id,
                    "severity": sev,
                    "affected_block_id": aff_block,
                    "impact_description": assessment.impact_summary,
                    "feasibility_status": "DISRUPTED",
                    "impact_assessment": assessment.to_dict(),
                })

        # Also detect from delays_df if present
        if delays_df is not None and len(delays_df) > 0 and "delay_minutes" in delays_df.columns:
            critical_delays = delays_df[delays_df["delay_minutes"] >= 30.0]
            for idx, row in critical_delays.iterrows():
                sec_id = str(row.get("section_id", "SEC_001"))
                d_min = float(row.get("delay_minutes", 30.0))
                train_num = str(row.get("train_number", "EXP-UNKNOWN"))
                evt_id = f"DEL_{train_num}_{idx:03d}"

                event_dict = {
                    "event_id": evt_id,
                    "event_type": DisruptionEventType.LATE_TRAIN.value,
                    "section_id": sec_id,
                    "severity": "High" if d_min >= 60.0 else "Medium",
                    "delay_minutes": d_min,
                }
                assessment = self.assess_impact(event_dict)

                detected.append({
                    "event_id": evt_id,
                    "event_type": DisruptionEventType.LATE_TRAIN.value,
                    "section_id": sec_id,
                    "severity": event_dict["severity"],
                    "affected_block_id": str(row.get("affected_block_id", "")),
                    "impact_description": f"Train {train_num} delayed {d_min:.0f}m on {sec_id}. {assessment.impact_summary}",
                    "feasibility_status": "DISRUPTED",
                    "impact_assessment": assessment.to_dict(),
                })

        return detected


ImpactAnalyzer = DisruptionEngine
