"""
Blocks API Router for Candidate Generation, Clustering, Feasibility, and Approvals.
"""

from typing import Optional
import pandas as pd
from fastapi import APIRouter, Query, HTTPException, Body
from app.repositories.csv_repository import CSVRepository
from app.config.settings import settings
from app.services.approval.approval_service import ApprovalService
from app.services.optimization.planning_service import PlanningService
from app.services.clustering.shadow_block_service import ClusteringService
from app.services.optimization.schedule_validator import FeasibilityService
from app.models.block_models import BlockApprovalRequest, BlockModificationRequest, BlockRejectionRequest, BlockExecutionOutcomeRequest
from app.utils.csv_utils import sanitize_for_json
from app.utils.id_utils import generate_block_id

router = APIRouter(tags=["Blocks"])
approval_service = ApprovalService()
planning_service = PlanningService()
clustering_service = ClusteringService()
feasibility_service = FeasibilityService()


@router.post("/ai/cluster", summary="Discover Shadow-Blocks & Integrated Mega-Blocks")
@router.post("/blocks/cluster", summary="Discover Shadow-Blocks (Blocks)")
def run_clustering():
    """Discovers spatial-temporal overlap across departments to form integrated mega-blocks."""
    clustered_df = clustering_service.run_clustering()
    return {"status": "SUCCESS", "clusters_generated": len(clustered_df)}


@router.post("/ai/check-feasibility", summary="Run Tripartite Constraint Feasibility Engine")
@router.post("/blocks/check-feasibility", summary="Run Constraint Feasibility (Blocks)")
def check_feasibility():
    """Evaluates timetable traffic gaps, machinery distance, and crew shift availability."""
    feas_df = feasibility_service.run_feasibility_check()
    return {"status": "SUCCESS", "feasible_tasks": int(feas_df["overall_feasible"].sum())}


@router.get("/blocks", summary="Get Generated Block Plans")
def get_blocks(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=500), status: Optional[str] = None):
    """Returns block recommendations from the weekly plan."""
    repo = CSVRepository(settings.OUTPUT_DATA_ROOT / "weekly_block_plan.csv")
    filters = {"status": status} if status else {}
    return repo.filter_rows(filters, page=page, page_size=page_size)


@router.get("/blocks/{block_id}", summary="Get Single Block Details")
def get_block_by_id(block_id: str):
    """Returns details for a specific block plan."""
    repo = CSVRepository(settings.OUTPUT_DATA_ROOT / "weekly_block_plan.csv")
    item = repo.get_by_id("block_id", block_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Block '{block_id}' not found.")
    return item


@router.post("/blocks/candidates", summary="Generate Feasible Candidate Block Windows")
def generate_candidates():
    """Generates candidate maintenance block windows matching traffic, resources, and spatial bounds."""
    feas_repo = CSVRepository(settings.PROCESSED_DATA_ROOT / "feasibility_checked_tasks.csv")
    df = feas_repo.read_csv()
    candidates = df.loc[df["overall_feasible"]].head(100).copy()
    feasible_items = []
    for idx, row in candidates.reset_index(drop=True).iterrows():
        task_id = str(row.get("task_id", f"TASK_{idx:04d}"))
        sec = str(row.get("section_id", "UNKNOWN"))
        duration = int(float(row.get("estimated_duration_minutes", 120) or 120))
        primary_task = task_id if bool(row.get("is_primary_task", True)) else str(row.get("cluster_id", task_id))
        feasible_items.append({
            "block_id": generate_block_id(sec, idx + 1),
            "primary_task": primary_task,
            "shadow_tasks": [] if primary_task == task_id else [task_id],
            "departments": str(row.get("departments_involved", row.get("department", ""))).split(";"),
            "corridor": sec,
            "start_time": None,
            "end_time": None,
            "duration": duration,
            "utilization": round(float(row.get("spatial_overlap_score", 0.0) or 0.0), 2),
            "priority": round(float(row.get("criticality_score", row.get("priority_score", 0.0)) or 0.0), 2),
            "required_resources": [str(row.get("required_resource_type", ""))],
            "train_impact": "LOW" if float(row.get("traffic_density", 0.5) or 0.5) < 0.6 else "MEDIUM",
            "feasibility": {
                "feasible": bool(row.get("overall_feasible", False)),
                "failed_constraints": str(row.get("failed_constraints", "NONE")),
                "satisfied_constraints": str(row.get("satisfied_constraints", "")),
                "explanation": str(row.get("feasibility_explanation", "Feasible task-level candidate.")),
            },
            "constraint_summary": {
                "traffic": bool(row.get("traffic_feasible", False)),
                "machine": bool(row.get("machine_feasible", False)),
                "crew": bool(row.get("crew_feasible", False)),
                "duration": bool(row.get("time_feasible", False)),
                "spatial": bool(row.get("spatially_feasible", False)),
            },
            "xai_reasons": [
                str(row.get("priority_reason", "Selected by deterministic priority and feasibility checks.")),
                str(row.get("feasibility_explanation", "All hard constraints passed.")),
            ],
            "source": "csv",
            "source_record_id": task_id,
            "dataset_name": "feasibility_checked_tasks.csv",
            "raw_task": row.to_dict(),
        })
    return sanitize_for_json({"candidate_count": len(feasible_items), "candidates": feasible_items})


@router.post("/blocks/generate", summary="Trigger Full Block Recommendation Plan Generation")
def generate_block_plan(start_date: Optional[str] = None):
    """Generates optimal block plan recommendations."""
    plan_df = planning_service.generate_weekly_plan(start_date)
    return {"status": "SUCCESS", "blocks_generated": len(plan_df)}


@router.post("/blocks/{block_id}/approve", summary="Human Controller Approval of Recommended Block")
def approve_block(block_id: str, request: BlockApprovalRequest):
    """Human controller approves a recommended block plan."""
    return approval_service.approve_block(block_id, request.model_dump())


@router.post("/blocks/{block_id}/modify", summary="Human Controller Modification of Block Window")
def modify_block(block_id: str, request: BlockModificationRequest):
    """Human controller modifies block start/end window time."""
    return approval_service.modify_block(block_id, request.model_dump())


@router.post("/blocks/{block_id}/reject", summary="Human Controller Rejection of Block Recommendation")
def reject_block(block_id: str, request: BlockRejectionRequest):
    """Human controller rejects a block recommendation with explicit reason."""
    return approval_service.reject_block(block_id, request.model_dump())


@router.post("/blocks/{block_id}/execute", summary="Record Block Execution Outcome")
def execute_block(block_id: str, request: BlockExecutionOutcomeRequest):
    """Records planned-vs-actual execution outcome after human-approved field execution."""
    return approval_service.record_execution_outcome(block_id, request.model_dump())
