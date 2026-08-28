"""
KPI calculation helper service.
"""

from typing import Dict, Any
from app.services.analytics.analytics_service import AnalyticsService


class KPIService:
    def __init__(self):
        self.analytics = AnalyticsService()

    def get_summary(self) -> Dict[str, Any]:
        return self.analytics.get_overview_kpis()
