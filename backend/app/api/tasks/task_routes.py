"""
Tasks, Trains, and System API Routes.
"""

from typing import Optional
from fastapi import APIRouter, Query, HTTPException, BackgroundTasks
from app.repositories.task_repository import TaskRepository
from app.repositories.traffic_repository import TrafficRepository
from app.repositories.csv_repository import CSVRepository
from app.config.settings import settings
from app.services.ingestion.ingestion_service import IngestionService
from app.services.priority.mdps_service import PriorityService
from app.services.analytics.system_health_service import SystemHealthService
from app.services.ingestion.validation_service import ValidationService

router = APIRouter(tags=["Tasks, Trains & System"])
task_repo = TaskRepository()
traffic_repo = TrafficRepository()
ingestion_service = IngestionService()
priority_service = PriorityService()
health_service = SystemHealthService()
val_service = ValidationService()


# -----------------------------------------------------------------------------
# System Endpoints
# -----------------------------------------------------------------------------

@router.get("/system/health", summary="Backend System Health Check")
def get_system_health():
    """Returns system status, active data sources, and AI model availability."""
    return health_service.get_system_health()


@router.get("/system/data-status", summary="Dataset Row Counts & Storage Status")
def get_data_status():
    """Returns metadata and row counts for all raw datasets."""
    return health_service.get_data_status()


@router.post("/system/validate-data", summary="Validate Raw CSV Data Integrity")
def validate_data():
    """Validates schemas, primary keys, foreign keys, and constraints across raw CSV files."""
    return val_service.validate_all_datasets()


@router.post("/system/preprocess", summary="Execute Full Data Preprocessing Pipeline")
def preprocess_data(background_tasks: BackgroundTasks):
    """Executes the complete preprocessing pipeline."""
    from data.preprocessing.run_pipeline import run_full_pipeline
    background_tasks.add_task(run_full_pipeline)
    return {
        "status": "PROCESSING_STARTED",
        "message": "Full RailBlock AI preprocessing pipeline execution initiated in background."
    }


# -----------------------------------------------------------------------------
# Tasks Endpoints
# -----------------------------------------------------------------------------

@router.get("/tasks", summary="Get Paginated Maintenance Tasks")
def get_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    department: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    section_id: Optional[str] = None,
    min_priority: Optional[float] = Query(None, ge=0, le=100),
    overdue_only: Optional[bool] = Query(None),
    recommended_only: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
):
    """Returns paginated maintenance tasks with optional department, severity, status, priority, overdue, and recommendation filtering."""
    import pandas as pd
    from datetime import datetime
    from app.utils.csv_utils import sanitize_for_json

    repo = CSVRepository(settings.PROCESSED_DATA_ROOT / "scored_tasks.csv")
    if not repo.file_exists():
        repo = CSVRepository(settings.PROCESSED_DATA_ROOT / "unified_maintenance_tasks.csv")

    df = repo.read_csv()
    if df.empty:
        return {"items": [], "page": page, "page_size": page_size, "total": 0, "pages": 0}

    # Department filter (supports comma-separated list or single value)
    if department:
        depts = [d.strip().lower() for d in department.split(",") if d.strip()]
        if "department" in df.columns:
            df = df[df["department"].astype(str).str.lower().isin(depts)]

    # Severity filter
    if severity:
        sevs = [s.strip().upper() for s in severity.split(",") if s.strip()]
        sev_col = "severity_class" if "severity_class" in df.columns else "severity"
        if sev_col in df.columns:
            df = df[df[sev_col].astype(str).str.upper().isin(sevs)]

    # Status filter
    if status:
        stats = [s.strip().lower() for s in status.split(",") if s.strip()]
        if "status" in df.columns:
            df = df[df["status"].astype(str).str.lower().isin(stats)]

    # Section ID filter
    if section_id and "section_id" in df.columns:
        df = df[df["section_id"].astype(str).str.lower() == section_id.strip().lower()]

    # Min Priority filter
    if min_priority is not None:
        prio_col = "criticality_score" if "criticality_score" in df.columns else "priority_score"
        if prio_col in df.columns:
            df = df[pd.Series(pd.to_numeric(df[prio_col], errors="coerce")).fillna(0.0) >= float(min_priority)]

    # Overdue Only filter
    if overdue_only is True:
        if "overdue_days" in df.columns:
            df = df[pd.Series(pd.to_numeric(df["overdue_days"], errors="coerce")).fillna(0) > 0]
        elif "target_completion_date" in df.columns:
            today_str = datetime.now().strftime("%Y-%m-%d")
            df = df[df["target_completion_date"].astype(str) < today_str]

    # Recommended Only filter
    if recommended_only is True:
        feas_file = settings.PROCESSED_DATA_ROOT / "feasibility_checked_tasks.csv"
        if feas_file.exists():
            feas_df = CSVRepository(feas_file).read_csv()
            if "task_id" in feas_df.columns and "overall_feasible" in feas_df.columns:
                rec_task_ids = set(feas_df.loc[feas_df["overall_feasible"].fillna(False).astype(bool), "task_id"].astype(str))
                df = df[df["task_id"].astype(str).isin(rec_task_ids)]
        else:
            prio_col = "criticality_score" if "criticality_score" in df.columns else "priority_score"
            if prio_col in df.columns:
                df = df[pd.Series(pd.to_numeric(df[prio_col], errors="coerce")).fillna(0.0) >= 70.0]

    # Search filter
    if search and search.strip():
        q = search.strip().lower()
        search_cols = [c for c in ["task_id", "section_id", "defect_type", "location_reference_id", "required_resource_type"] if c in df.columns]
        if search_cols:
            mask = pd.Series(False, index=df.index)
            for c in search_cols:
                mask = mask | df[c].astype(str).str.lower().str.contains(q, na=False)
            df = df[mask]

    df_out: pd.DataFrame = df if isinstance(df, pd.DataFrame) else pd.DataFrame(df)
    total = len(df_out)
    start = (page - 1) * page_size
    end = start + page_size
    slice_df = pd.DataFrame(df_out.iloc[start:end])
    items = sanitize_for_json(slice_df.to_dict("records"))
    pages = (total + page_size - 1) // page_size if page_size > 0 else 1

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": pages
    }



@router.get("/tasks/{task_id}", summary="Get Single Task Details")
def get_task_by_id(task_id: str):
    """Fetches details for a single task by ID."""
    task = task_repo.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return task


@router.get("/tasks/{task_id}/priority", summary="Get Task Priority Score Breakdown")
def get_task_priority(task_id: str):
    """Calculates MDPS priority score breakdown and natural language reason for a task."""
    p_info = priority_service.get_task_priority(task_id)
    if not p_info:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return p_info


@router.post("/tasks/unify", summary="Unify TMS, SMMS & TDMS Maintenance Tasks")
def unify_tasks(planning_date: Optional[str] = None):
    """Merges departmental defect datasets into unified_maintenance_tasks.csv."""
    unified_df = ingestion_service.unify_maintenance_tasks(planning_date)
    return {
        "status": "SUCCESS",
        "message": f"Successfully unified {len(unified_df)} maintenance tasks across Engineering, S&T, and TRD.",
        "task_count": len(unified_df)
    }


# -----------------------------------------------------------------------------
# Trains Endpoints
# -----------------------------------------------------------------------------

@router.get("/trains", summary="Get Train Timetable Schedules")
def get_trains(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=500), train_type: Optional[str] = None):
    """Returns train timetable schedules."""
    filters = {"train_type": train_type} if train_type else {}
    return traffic_repo.timetable_repo.filter_rows(filters, page=page, page_size=page_size)


@router.get("/trains/live", summary="Get Simulated Train Delays & Operational Status")
def get_live_trains(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=500)):
    """Returns live train delays, actual arrival/departure times, and delay reasons."""
    return traffic_repo.delays_repo.filter_rows({}, page=page, page_size=page_size)


@router.get("/trains/timetable", summary="Get Section Train Timetables")
def get_timetable(section_id: Optional[str] = None, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=500)):
    """Returns timetable records filtered by section."""
    filters = {"section_id": section_id} if section_id else {}
    return traffic_repo.timetable_repo.filter_rows(filters, page=page, page_size=page_size)

