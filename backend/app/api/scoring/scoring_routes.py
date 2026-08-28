"""
MDPS Priority & Criticality Scoring API Routes.
"""

import time
import uuid
from typing import Optional, Dict, Any
from fastapi import APIRouter, Body
from app.services.priority.mdps_service import PriorityService
from app.services.xai.explanation_service import ExplainabilityService

router = APIRouter(tags=["Scoring & Priority"])
priority_service = PriorityService()
xai_service = ExplainabilityService()


@router.post("/ai/priority", summary="Calculate Task Criticality Scores via MDPS Engine")
@router.post("/scoring/priority", summary="Calculate Task Criticality Scores (Scoring)")
def calculate_priority(task: Optional[Dict[str, Any]] = Body(default=None)):
    """
    Scores unified maintenance tasks using the Multi-Variable Criticality Matrix (0-100).
    If a specific task payload is passed, scores and explains that single task.
    Otherwise runs batch scoring over unified maintenance tasks.
    """
    t0 = time.perf_counter()
    request_id = uuid.uuid4().hex[:12]
    model_status = priority_service.engine.get_model_status()

    if task and isinstance(task, dict) and "severity_class" in task:
        # Single task scoring with XAI
        result = priority_service.engine.calculate_priority(task)
        explanation = xai_service.explain_task_priority(task, result)
        timing_ms = round((time.perf_counter() - t0) * 1000, 1)
        return {
            "status": "SUCCESS",
            "request_id": request_id,
            "model_version": model_status.get("model_version", "GradientBoostingRegressor"),
            "scoring_mode": model_status.get("scoring_mode"),
            "timing_ms": timing_ms,
            "data": result,
            "explanation": explanation,
        }

    # Batch scoring
    scored_df = priority_service.run_priority_scoring()
    timing_ms = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "status": "SUCCESS",
        "request_id": request_id,
        "model_version": model_status.get("model_version", "GradientBoostingRegressor"),
        "scoring_mode": model_status.get("scoring_mode"),
        "timing_ms": timing_ms,
        "tasks_scored": len(scored_df),
        "model_status": model_status,
    }


@router.post("/ai/train-mdps", summary="Train ML MDPS Priority Model")
@router.post("/scoring/train", summary="Train ML MDPS Priority Model (Scoring)")
def train_mdps_model():
    """Trains GradientBoostingRegressor model on historical MDPS labels and saves model artifacts."""
    t0 = time.perf_counter()
    from data.preprocessing.mdps_dataset import train_mdps_model_and_score_tasks
    scored_df, metrics = train_mdps_model_and_score_tasks()
    timing_ms = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "status": "SUCCESS",
        "timing_ms": timing_ms,
        "metrics": metrics,
        "model_version": "GradientBoostingRegressor",
    }

