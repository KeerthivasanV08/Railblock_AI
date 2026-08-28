"""
Analytics, KPIs, Simulation Impact, and Audit Trail API Routes.
"""

from fastapi import APIRouter, Query
from app.services.analytics.analytics_service import AnalyticsService
from app.services.analytics.audit_service import AuditService

router = APIRouter(tags=["Analytics & Audit"])
analytics_service = AnalyticsService()
audit_service = AuditService()


@router.get("/analytics/overview", summary="Get Operational Overview KPI Metrics")
def get_analytics_overview():
    """Returns dashboard operational KPI metrics calculated directly from CSV datasets."""
    return analytics_service.get_overview_kpis()


@router.get("/analytics/impact", summary="Get Before vs. After RailBlock AI Simulation Impact Analysis")
def get_analytics_impact():
    """Returns simulated performance improvements comparing manual baseline vs RailBlock AI."""
    return analytics_service.get_before_after_impact()


@router.get("/analytics/department-workload", summary="Get Department Workload Breakdown")
def get_department_workload():
    """Returns task count distribution across Engineering, S&T, and TRD."""
    return analytics_service.get_department_workload()


@router.get("/audit", summary="Get Append-Only Audit Events")
def get_audit(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100)):
    """Returns paginated audit trail events."""
    return audit_service.get_audit_logs(page=page, page_size=page_size)
