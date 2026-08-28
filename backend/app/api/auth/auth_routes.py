"""
Authentication API Router stub for RailBlock AI.

STATUS: NOT CONNECTED / FUTURE INTEGRATION
"""

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/status", summary="Authentication status")
def auth_status():
    return {"status": "NOT_CONNECTED", "message": "Authentication is not enabled in prototype mode."}
