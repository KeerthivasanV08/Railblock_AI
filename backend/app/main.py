"""FastAPI application entrypoint for the RailBlock AI decision-support backend."""

import logging
import sys
from pathlib import Path

# Keep the existing app.* imports usable when launched from either the repo root
# (backend.app.main) or the backend directory (app.main).
BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.api.websocket.realtime_routes import router as websocket_router
from app.config.settings import settings
from app.config.logging import configure_logging
from app.core.exceptions import RailBlockException, railblock_exception_handler

configure_logging(settings.LOG_LEVEL)

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "CSV-first railway maintenance planning and disruption decision support. "
        "Recommendations require human controller approval and do not authorize railway operations."
    ),
    version="0.1.0",
)

raw_origins = f"{settings.CORS_ORIGINS or ''},{settings.FRONTEND_URL or ''}"
configured_origins = [
    origin.strip()
    for origin in raw_origins.split(",")
    if origin.strip()
]
default_dev_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]
cors_origins = list(dict.fromkeys(configured_origins + default_dev_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|.*\.vercel\.app)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include central API router with /api prefix
app.include_router(api_router, prefix=settings.API_PREFIX)

# Include root-level websocket routes (/ws/*)
app.include_router(websocket_router)

app.add_exception_handler(RailBlockException, railblock_exception_handler)


@app.middleware("http")
async def request_context(request: Request, call_next):
    import time
    from uuid import uuid4

    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = str(round((time.perf_counter() - started) * 1000, 2))
    return response


@app.exception_handler(FileNotFoundError)
async def handle_missing_data(request: Request, exc: FileNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"error": "DATA_FILE_NOT_FOUND", "message": str(exc)},
    )


@app.exception_handler(ValueError)
async def handle_data_error(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"error": "INVALID_DATA", "message": str(exc)},
    )


@app.get("/", tags=["System"], summary="RailBlock AI service information")
def root() -> dict[str, str]:
    return {
        "service": settings.APP_NAME,
        "status": "healthy",
        "data_source": "csv",
        "safety_notice": "Decision support only; human approval required.",
    }


@app.get("/healthz", include_in_schema=False)
def healthz() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/health", tags=["Health"], summary="Backend liveness health check")
def health() -> dict[str, str]:
    return {"status": "healthy", "data_source": "csv"}


@app.get("/health/live", tags=["Health"], summary="Backend process liveness")
def health_live() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/health/ready", tags=["Health"], summary="Backend readiness check")
def health_ready() -> dict[str, str]:
    return {"status": "ready", "data_source": "csv"}
