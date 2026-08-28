"""
Score explanation helper for priority breakdown.
"""

from typing import Dict, Any, List


class ScoreExplainer:
    def explain_score(self, priority_result: Dict[str, Any], feature_importance: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        score = priority_result.get("criticality_score", 50.0)
        band = priority_result.get("priority_band", "Medium")
        reason = priority_result.get("priority_reason", "Deterministic priority assignment.")
        task = priority_result.get("task", {})

        severity = task.get("severity_class", "C")
        overdue_days = task.get("overdue_days", 0)
        deferred_count = task.get("deferred_count", 0)
        traffic_density = task.get("traffic_density", 0.5)

        factor_contributions = {
            "severity_impact": f"Class {severity} defect contributes significantly to risk level.",
            "overdue_urgency": f"Overdue by {overdue_days} days; urgency escalation applied." if overdue_days > 0 else "Task is within nominal schedule target window.",
            "deferral_risk": f"Deferred {deferred_count} times; compounding maintenance risk." if deferred_count > 0 else "First-time scheduling with no prior deferrals.",
            "traffic_pressure": f"Traffic density {traffic_density:.2f} increases track occupancy criticality."
        }

        return {
            "criticality_score": score,
            "priority_band": band,
            "summary_reason": reason,
            "factor_contributions": factor_contributions,
            "feature_importance_ranks": feature_importance or [
                {"feature": "sev_num", "rank": 1},
                {"feature": "overdue_days", "rank": 2},
                {"feature": "traffic_num", "rank": 3},
                {"feature": "deferred_count", "rank": 4}
            ]
        }
