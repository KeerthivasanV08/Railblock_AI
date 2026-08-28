"""
Central API Router for RailBlock AI.

Aggregates all domain route modules into unified routers.
"""

from fastapi import APIRouter

from app.api.auth.auth_routes import router as auth_router
from app.api.dashboard.dashboard_routes import router as dashboard_router
from app.api.tasks.task_routes import router as tasks_router
from app.api.assets.asset_routes import router as assets_router
from app.api.spatial.spatial_routes import router as spatial_router
from app.api.scoring.scoring_routes import router as scoring_router
from app.api.blocks.block_routes import router as blocks_router
from app.api.planner.planner_routes import router as planner_router
from app.api.resources.resource_routes import router as resources_router
from app.api.execution.execution_routes import router as execution_router
from app.api.disruptions.disruption_routes import router as disruptions_router
from app.api.xai.xai_routes import router as xai_router
from app.api.analytics.analytics_routes import router as analytics_router
from app.api.websocket.realtime_routes import router as realtime_router

# Central router for HTTP API endpoints (mounted under /api)
api_router = APIRouter()

for r in [
    spatial_router,
    scoring_router,
    blocks_router,
    planner_router,
    tasks_router,
    assets_router,
    resources_router,
    disruptions_router,
    xai_router,
    analytics_router,
    auth_router,
    dashboard_router,
    execution_router,
    realtime_router,
]:
    api_router.include_router(r)

__all__ = ["api_router", "realtime_router"]
