"""
Disruption Impact Assessment Engine for RailBlock AI.

Detects operational disruptions (Late Trains, Emergency Defects, Machine Breakdowns)
and evaluates affected block sections, tasks, and remaining window feasibility.
"""

import pandas as pd


class DisruptionEngine:
    def detect_disruptions(
        self,
        disruptions_df: pd.DataFrame,
        delays_df: pd.DataFrame = None,
        active_blocks_df: pd.DataFrame = None
    ) -> list:
        """
        Analyzes live operational feeds to flag critical disruptions affecting block schedules.
        """
        detected = []

        if len(disruptions_df) > 0:
            for idx, row in disruptions_df.iterrows():
                e_type = row.get("event_type", "Late Train")
                sec_id = row.get("section_id", "")
                sev = row.get("severity", "Medium")
                aff_block = row.get("affected_block_id", "")

                impact = "High disruption risk: block window reduced." if e_type == "Late Train" else (
                    "Emergency track access required: scheduled block displaced." if e_type == "Emergency Defect" else
                    "Machine failure: task cannot proceed in assigned block."
                )

                detected.append({
                    "event_id": row.get("event_id", f"DIS_{idx:04d}"),
                    "event_type": e_type,
                    "section_id": sec_id,
                    "severity": sev,
                    "affected_block_id": aff_block,
                    "impact_description": impact,
                    "feasibility_status": "DISRUPTED"
                })

        return detected


ImpactAnalyzer = DisruptionEngine
