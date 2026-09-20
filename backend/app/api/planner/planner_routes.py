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


@router.post("/planning/rolling", summary="Generate Strategic 26-Week Rolling Block Plan (Legacy)", deprecated=True)
@router.post("/planner/rolling", summary="Generate Strategic 26-Week Rolling Block Plan (Canonical)")
def create_rolling_plan(start_date: Optional[str] = None, horizon_weeks: int = Query(26, ge=1, le=52)):
    """Generates dynamic multi-week rolling block plan across the full planning horizon."""
    plan_df = planning_service.generate_rolling_plan(start_date=start_date, horizon_weeks=horizon_weeks, persist=True)
    return {
        "status": "SUCCESS",
        "horizon_weeks": horizon_weeks,
        "total_blocks": len(plan_df),
        "rolling_plan": plan_df.to_dict("records"),
    }


@router.get("/planning/rolling", summary="Get Rolling Block Planning Horizon (Legacy)", deprecated=True)
@router.get("/planner/rolling", summary="Get Rolling 26-Week Block Planning Horizon (Canonical)")
def get_rolling_plan(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    week_number: Optional[int] = Query(None, ge=1, le=52),
    department: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    min_priority: Optional[float] = Query(None, ge=0, le=100),
    section_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
):
    """Returns rolling multi-week block planning horizon from canonical 26-week plan with full query parameter filtering."""
    import pandas as pd
    from datetime import datetime, timedelta
    from app.utils.csv_utils import sanitize_for_json

    canonical_file = settings.OUTPUT_DATA_ROOT / "rolling_26week_block_plan.csv"
    should_generate = not canonical_file.exists()
    if not should_generate:
        try:
            repo_check = CSVRepository(canonical_file)
            existing_df = repo_check.read_csv()
            if existing_df.empty or "week_number" not in existing_df.columns or existing_df["week_number"].max() < 26:
                should_generate = True
        except Exception:
            pass

    if should_generate:
        try:
            planning_service.generate_rolling_plan(horizon_weeks=26, persist=True)
        except Exception:
            pass

    repo = CSVRepository(canonical_file if canonical_file.exists() else settings.OUTPUT_DATA_ROOT / "monthly_rolling_block_plan.csv")
    df = repo.read_csv()

    if df.empty:
        return {"items": [], "page": page, "page_size": page_size, "total": 0, "pages": 0}

    # Normalize missing date columns if needed
    if "plan_date" in df.columns:
        if "start_date" not in df.columns:
            df["start_date"] = df["plan_date"]
        else:
            df["start_date"] = df["start_date"].fillna(df["plan_date"])
        if "end_date" not in df.columns:
            df["end_date"] = df["plan_date"]
        else:
            df["end_date"] = df["end_date"].fillna(df["plan_date"])

    # 1. Week number filter
    if week_number is not None and "week_number" in df.columns:
        df = df[pd.Series(pd.to_numeric(df["week_number"], errors="coerce")).fillna(0).astype(int) == week_number]

    # 2. Department filter
    if department and department.strip() and department.lower() != "all":
        target_dept = department.strip().lower()
        if "departments" in df.columns:
            if target_dept == "engineering":
                df = df[df["departments"].astype(str).str.lower().str.contains("eng|p-way|track", regex=True, na=False)]
            else:
                df = df[df["departments"].astype(str).str.lower().str.contains(target_dept, na=False)]

    # 3. Status filter
    if status and status.strip() and status.lower() != "all":
        st_upper = status.strip().upper()
        if "status" in df.columns:
            s_series = df["status"].astype(str).str.upper()
            if st_upper == "PLANNED":
                df = df[s_series.isin(["PLANNED", "PROPOSED", "SCHEDULED"])]
            elif st_upper == "PENDING APPROVAL":
                df = df[s_series.isin(["PENDING APPROVAL", "PROPOSED", "AI RECOMMENDED"])]
            elif st_upper == "CANCELLED":
                df = df[s_series.isin(["CANCELLED", "REJECTED"])]
            else:
                df = df[s_series == st_upper]

    # 4. Priority filter
    prio_col = "priority" if "priority" in df.columns else "priority_score"
    if prio_col in df.columns:
        num_prio = pd.Series(pd.to_numeric(df[prio_col], errors="coerce")).fillna(0.0)
        if min_priority is not None:
            df = df[num_prio >= float(min_priority)]
        elif priority and priority.strip() and priority.lower() != "all":
            p_val = priority.strip().lower()
            if p_val == "critical":
                df = df[num_prio >= 85.0]
            elif p_val == "high":
                df = df[(num_prio >= 70.0) & (num_prio < 85.0)]
            elif p_val == "medium":
                df = df[(num_prio >= 50.0) & (num_prio < 70.0)]
            elif p_val == "low":
                df = df[num_prio < 50.0]

    # 5. Section ID filter
    if section_id and section_id.strip() and "section_id" in df.columns:
        df = df[df["section_id"].astype(str).str.lower() == section_id.strip().lower()]

    # 6. Date Range filter
    date_col = "start_date" if "start_date" in df.columns else "plan_date"
    if start_date and start_date.strip() and date_col in df.columns:
        df = df[df[date_col].astype(str) >= start_date.strip()[:10]]
    if end_date and end_date.strip() and date_col in df.columns:
        df = df[df[date_col].astype(str) <= end_date.strip()[:10]]

    # 7. Search filter
    if search and search.strip():
        q = search.strip().lower()
        search_cols = [c for c in ["block_id", "section_id", "task_ids", "departments", "resources", "crew", "xai_reason"] if c in df.columns]
        if search_cols:
            mask = pd.Series(False, index=df.index)
            for c in search_cols:
                mask = mask | df[c].astype(str).str.lower().str.contains(q, na=False)
            df = df[mask]

    # Ensure DataFrame type for linter
    df_out: pd.DataFrame = df if isinstance(df, pd.DataFrame) else pd.DataFrame(df)

    # 8. Sorting
    if sort_by:
        if sort_by == "week_asc" and "week_number" in df_out.columns:
            df_out = df_out.sort_values(by="week_number", ascending=True)
        elif sort_by == "date_asc" and date_col in df_out.columns:
            df_out = df_out.sort_values(by=date_col, ascending=True)
        elif sort_by == "priority_desc" and prio_col in df_out.columns:
            df_out = df_out.sort_values(by=prio_col, ascending=False)
        elif sort_by == "duration_desc" and "duration_minutes" in df_out.columns:
            df_out = df_out.sort_values(by="duration_minutes", ascending=False)
        elif sort_by == "block_id_asc" and "block_id" in df_out.columns:
            df_out = df_out.sort_values(by="block_id", ascending=True)

    total = len(df_out)
    start = (page - 1) * page_size
    end = start + page_size
    slice_df = pd.DataFrame(df_out.iloc[start:end])
    items = sanitize_for_json(slice_df.to_dict("records"))
    pages = (total + page_size - 1) // page_size if page_size > 0 else 1

    return {
        "items": items,
        "records": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": pages
    }


