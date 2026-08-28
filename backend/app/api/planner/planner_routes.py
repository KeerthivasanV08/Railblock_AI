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


@router.post("/ai/optimize", summary="Solve OR-Tools Block Optimization Problem")
@router.post("/planner/optimize", summary="Solve OR-Tools Block Optimization (Planner)")
def run_optimization():
    """Solves integer program using Google OR-Tools to select optimal block recommendations."""
    selected_df, metrics = opt_service.run_optimization()
    return {"status": "SUCCESS", "metrics": metrics, "selected_blocks": len(selected_df)}


@router.post("/planning/weekly", summary="Generate 7-Day Weekly Block Schedule Plan")
@router.post("/planner/weekly", summary="Generate Weekly Plan (Planner)")
def create_weekly_plan(start_date: Optional[str] = None, section_id: Optional[str] = None):
    """Generates 7-day weekly block schedule plan."""
    plan_df = planning_service.generate_weekly_plan(start_date, section_id)
    return {"status": "SUCCESS", "weekly_plan": plan_df.to_dict("records")}


@router.post("/planning/monthly", summary="Generate 4-to-6 Week Monthly Block Plan")
@router.post("/planner/monthly", summary="Generate Monthly Plan (Planner)")
def create_monthly_plan(start_date: Optional[str] = None):
    """Generates 4-to-6 week monthly block plan."""
    plan_df = planning_service.generate_monthly_plan(start_date)
    return {"status": "SUCCESS", "monthly_plan": plan_df.to_dict("records")}


@router.get("/planning/rolling", summary="Get Rolling 26-Week Block Planning Horizon")
@router.get("/planner/rolling", summary="Get Rolling Horizon (Planner)")
def get_rolling_plan(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=500)):
    """Returns rolling multi-week block planning horizon."""
    repo = CSVRepository(settings.OUTPUT_DATA_ROOT / "monthly_rolling_block_plan.csv")
    return repo.filter_rows({}, page=page, page_size=page_size)
