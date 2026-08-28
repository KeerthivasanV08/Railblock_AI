"""
Tripartite Feasibility & Constraint Engine for RailBlock AI.

Evaluates operational feasibility matching Traffic timetable gaps, Machine inventory positioning,
and Crew shift availability.
"""

import numpy as np
import pandas as pd
from app.core.constants import RejectionReason


class ConstraintEngine:
    def __init__(self, max_resource_dist_km: float = 50.0):
        self.max_resource_dist_km = max_resource_dist_km

    def check_feasibility(
        self,
        tasks_df: pd.DataFrame,
        traffic_df: pd.DataFrame = None,
        resource_df: pd.DataFrame = None
    ) -> pd.DataFrame:
        """
        Evaluates tripartite feasibility for maintenance tasks and block candidates.
        """
        feas_df = tasks_df.copy()

        # Perform fast vectorized matching
        if "traffic_density" in feas_df.columns:
            trf_density = feas_df["traffic_density"].fillna(0.5).values
        elif traffic_df is not None and "section_id" in traffic_df.columns:
            trf_map = traffic_df.set_index("section_id")["traffic_density"].to_dict()
            trf_density = feas_df["section_id"].map(trf_map).fillna(0.5).values
        else:
            trf_density = np.full(len(feas_df), 0.5)

        if "machine_available" in feas_df.columns:
            mch_avail = feas_df["machine_available"].fillna(False).values.astype(bool)
            crew_feasible = feas_df.get("crew_available", pd.Series(False, index=feas_df.index)).fillna(False).values.astype(bool)
        elif resource_df is not None and "task_id" in resource_df.columns:
            mch_map = resource_df.set_index("task_id")["machine_available"].to_dict()
            crew_map = resource_df.set_index("task_id")["crew_available"].to_dict()
            mch_avail = feas_df["task_id"].map(mch_map).fillna(False).values.astype(bool)
            crew_feasible = feas_df["task_id"].map(crew_map).fillna(False).values.astype(bool)
        else:
            mch_avail = np.zeros(len(feas_df), dtype=bool)
            crew_feasible = np.zeros(len(feas_df), dtype=bool)

        traffic_feasible = (trf_density < 0.85)
        time_feasible = (feas_df["estimated_duration_minutes"].fillna(120).values <= 240) if "estimated_duration_minutes" in feas_df.columns else np.ones(len(feas_df), dtype=bool)
        if "mapped_chainage_km" in feas_df.columns:
            spatially_feasible = ~feas_df["mapped_chainage_km"].isna().values
            if "spatial_mapping_status" in feas_df.columns:
                spatially_feasible = spatially_feasible & ~feas_df["spatial_mapping_status"].isin(["LOW_CONFIDENCE", "UNMAPPED", "INVALID"]).values
        else:
            spatially_feasible = np.ones(len(feas_df), dtype=bool)

        overall = traffic_feasible & mch_avail & crew_feasible & time_feasible & spatially_feasible

        reasons = np.full(len(feas_df), RejectionReason.NONE.value, dtype=object)
        reasons[~overall & ~traffic_feasible] = RejectionReason.NO_TRAFFIC_GAP.value
        reasons[~overall & traffic_feasible & ~mch_avail] = RejectionReason.MACHINE_UNAVAILABLE.value
        reasons[~overall & traffic_feasible & mch_avail & ~crew_feasible] = RejectionReason.CREW_UNAVAILABLE.value
        reasons[~overall & traffic_feasible & mch_avail & crew_feasible & ~time_feasible] = RejectionReason.INSUFFICIENT_WINDOW.value
        reasons[~overall & traffic_feasible & mch_avail & crew_feasible & time_feasible & ~spatially_feasible] = RejectionReason.SPATIAL_MAPPING_FAILURE.value

        feas_df["traffic_feasible"] = traffic_feasible
        feas_df["machine_feasible"] = mch_avail
        feas_df["crew_feasible"] = crew_feasible
        feas_df["time_feasible"] = time_feasible
        feas_df["spatially_feasible"] = spatially_feasible
        feas_df["overall_feasible"] = overall
        feas_df["rejection_reason"] = reasons
        feas_df["failed_constraints"] = [
            ";".join([
                name
                for name, ok in {
                    "traffic": bool(traffic_feasible[i]),
                    "machine": bool(mch_avail[i]),
                    "crew": bool(crew_feasible[i]),
                    "duration": bool(time_feasible[i]),
                    "spatial": bool(spatially_feasible[i]),
                }.items()
                if not ok
            ]) or "NONE"
            for i in range(len(feas_df))
        ]
        feas_df["satisfied_constraints"] = [
            ";".join([
                name
                for name, ok in {
                    "traffic": bool(traffic_feasible[i]),
                    "machine": bool(mch_avail[i]),
                    "crew": bool(crew_feasible[i]),
                    "duration": bool(time_feasible[i]),
                    "spatial": bool(spatially_feasible[i]),
                }.items()
                if ok
            ])
            for i in range(len(feas_df))
        ]
        feas_df["feasibility_explanation"] = np.where(
            overall,
            "All deterministic traffic, resource, crew, duration and spatial constraints passed.",
            "Rejected by deterministic constraint checks: " + feas_df["failed_constraints"].astype(str),
        )

        return feas_df

    def check_feasibility_single(self, candidate: dict) -> dict:
        """
        Validate a single rescheduler candidate dict against all hard operational constraints.

        Reuses the same 5-constraint logic as check_feasibility() — no duplicate rules.

        Args:
            candidate: dict with keys:
                section_id, traffic_density, machine_available, crew_available,
                duration_minutes, mapped_chainage_km (optional), spatial_mapping_status (optional)

        Returns:
            dict with:
                feasible (bool)
                failed_constraints (list[str])
                satisfied_constraints (list[str])
                rejection_reason (str)
                feasibility_explanation (str)
        """
        traffic_density = float(candidate.get("traffic_density", 0.5))
        machine_available = bool(candidate.get("machine_available", True))
        crew_available = bool(candidate.get("crew_available", True))
        duration_minutes = float(candidate.get("duration_minutes", 120))
        mapped_chainage = candidate.get("mapped_chainage_km")
        spatial_status = candidate.get("spatial_mapping_status", "MAPPED")

        # Apply identical thresholds as batch check
        traffic_feasible = traffic_density < 0.85
        time_feasible = duration_minutes <= 240
        spatially_feasible = (
            mapped_chainage is not None
            and spatial_status not in ("LOW_CONFIDENCE", "UNMAPPED", "INVALID")
        )

        overall = traffic_feasible and machine_available and crew_available and time_feasible and spatially_feasible

        constraint_map = {
            "traffic": traffic_feasible,
            "machine": machine_available,
            "crew": crew_available,
            "duration": time_feasible,
            "spatial": spatially_feasible,
        }
        failed = [name for name, ok in constraint_map.items() if not ok]
        satisfied = [name for name, ok in constraint_map.items() if ok]

        # Determine rejection reason (priority-ordered, matching batch logic)
        if overall:
            rejection_reason = "NONE"
            explanation = "All deterministic traffic, resource, crew, duration and spatial constraints passed."
        elif not traffic_feasible:
            rejection_reason = "NO_TRAFFIC_GAP"
            explanation = f"Traffic density {traffic_density:.2f} exceeds maximum 0.85 threshold during proposed window."
        elif not machine_available:
            rejection_reason = "MACHINE_UNAVAILABLE"
            explanation = "Required maintenance machine is not available during the proposed rescheduled window."
        elif not crew_available:
            rejection_reason = "CREW_UNAVAILABLE"
            explanation = "Required crew is not available during the proposed rescheduled window."
        elif not time_feasible:
            rejection_reason = "INSUFFICIENT_WINDOW"
            explanation = f"Block duration {duration_minutes:.0f} min exceeds maximum permitted window of 240 min."
        else:
            rejection_reason = "SPATIAL_MAPPING_FAILURE"
            explanation = "Section spatial mapping is insufficient for safe block placement."

        return {
            "feasible": overall,
            "failed_constraints": failed,
            "satisfied_constraints": satisfied,
            "rejection_reason": rejection_reason,
            "feasibility_explanation": explanation,
        }
