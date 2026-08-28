"""
Decision reasoning and justification service for human controller reviews.
"""

from typing import Dict, Any, List


class DecisionReasoningService:
    def summarize_block_decision(self, block: Dict[str, Any]) -> List[str]:
        reasons = []
        if block.get("priority", 0) >= 75:
            reasons.append("Contains critical-priority defects requiring urgent remediation.")
        if block.get("utilization", 0) >= 0.75:
            reasons.append("High spatial/departmental integration efficiency.")
        if block.get("train_impact") == "LOW":
            reasons.append("Scheduled within minimal timetable traffic conflict window.")
        return reasons or ["Standard routine maintenance allocation."]
