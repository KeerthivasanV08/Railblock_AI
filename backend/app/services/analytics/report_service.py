"""
Reporting and analytics generation service.
"""

from typing import Dict, Any
from app.services.analytics.analytics_service import AnalyticsService


class ReportService:
    def __init__(self):
        self.analytics = AnalyticsService()

    def generate_impact_report(self) -> Dict[str, Any]:
        return self.analytics.get_before_after_impact()
