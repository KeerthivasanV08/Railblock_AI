"""
Planning & Optimization API Router for Weekly, Monthly, and Rolling Block Plans.
"""

from typing import Optional
from fastapi import APIRouter, Query
from app.services.optimization.planning_service import PlanningService
from app.services.optimization.planner_service import OptimizationService
from app.repositories.csv_repository import CSVRepository
from app.config.settings import settings

router = APIRouter(tags=["Planning & Optimization"])
planning_service = PlanningService()
opt_service = OptimizationService()


@router.post("/ai/optimize", summary="Solve OR-Tools Block Optimization Problem (Legacy)", deprecated=True)
@router.post("/planner/optimize", summary="Solve OR-Tools Block Optimization (Canonical)")
def run_optimization():
    """Solves integer program using Google OR-Tools to select optimal block recommendations."""
    selected_df, metrics = opt_service.run_optimization()
    return {"status": "SUCCESS", "metrics": metrics, "selected_blocks": len(selected_df)}


@router.post("/planning/weekly", summary="Generate Weekly Block Schedule Plan (Legacy)", deprecated=True)
@router.post("/planner/weekly", summary="Generate 7-Day Weekly Block Schedule Plan (Canonical)")
def create_weekly_plan(start_date: Optional[str] = None, section_id: Optional[str] = None):
    """Generates 7-day weekly block schedule plan."""
    plan_df = planning_service.generate_weekly_plan(start_date, section_id)
    return {"status": "SUCCESS", "weekly_plan": plan_df.to_dict("records")}


@router.post("/planning/monthly", summary="Generate Monthly Block Plan (Legacy)", deprecated=True)
@router.post("/planner/monthly", summary="Generate 4-Week Dynamic Monthly Block Plan (Canonical)")
def create_monthly_plan(start_date: Optional[str] = None):
    """Generates 4-week dynamic monthly block plan."""
    plan_df = planning_service.generate_monthly_plan(start_date)
    return {"status": "SUCCESS", "monthly_plan": plan_df.to_dict("records")}


@router.get("/planning/rolling", summary="Get Rolling Block Planning Horizon (Legacy)", deprecated=True)
@router.get("/planner/rolling", summary="Get Rolling 26-Week Block Planning Horizon (Canonical)")
def get_rolling_plan(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    week_number: Optional[int] = Query(None, ge=1, le=52),
    department: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    section_id: Optional[str] = Query(None),
):
    """Returns rolling multi-week block planning horizon from canonical 26-week plan."""
    canonical_file = settings.OUTPUT_DATA_ROOT / "rolling_26week_block_plan.csv"
    if not canonical_file.exists():
        try:
            planning_service.generate_rolling_plan(horizon_weeks=26)
        except Exception:
            pass

    repo = CSVRepository(canonical_file if canonical_file.exists() else settings.OUTPUT_DATA_ROOT / "monthly_rolling_block_plan.csv")
    filters = {}
    if week_number is not None:
        filters["week_number"] = week_number
    if department:
        filters["departments"] = department
    if status:
        filters["status"] = status
    if section_id:
        filters["section_id"] = section_id

    return repo.filter_rows(filters, page=page, page_size=page_size)

