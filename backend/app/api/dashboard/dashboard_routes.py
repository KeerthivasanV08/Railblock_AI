"""
Dashboard overview API Router.
"""

from fastapi import APIRouter
from app.services.analytics.analytics_service import AnalyticsService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
analytics = AnalyticsService()


@router.get("/summary", summary="Dashboard summary KPIs")
def dashboard_summary():
    return analytics.get_overview_kpis()
