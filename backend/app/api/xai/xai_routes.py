"""
Explainable AI (XAI) API Routes.
"""

from fastapi import APIRouter
from app.services.xai.explanation_service import ExplainabilityService

router = APIRouter(tags=["Explainable AI"])
explain_service = ExplainabilityService()


@router.get("/ai/explain/{block_id}", summary="Get Explainable AI (XAI) Recommendation Explanation")
@router.get("/xai/explain/{block_id}", summary="Get Explanation (XAI)")
def explain_block(block_id: str):
    """Returns natural language explanation and constraint breakdown for a recommended block."""
    return explain_service.explain_block(block_id)
