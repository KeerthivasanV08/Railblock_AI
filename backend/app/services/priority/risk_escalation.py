"""
Risk escalation rules and triggers for priority ranking.
"""

from typing import Dict, Any


class RiskEscalationService:
    def check_escalation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        overdue = float(task.get("overdue_days", 0))
        sev = str(task.get("severity_class", "C")).upper()
        escalated = (sev == "A" and overdue > 7) or (overdue > 30)
        return {
            "escalated": escalated,
            "reason": "Severe overdue defect" if escalated else "Standard priority band",
        }
