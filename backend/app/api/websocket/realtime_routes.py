"""
Real-time Live Map and WebSocket API Routes.
"""

import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from app.live.provider import get_live_train_provider

router = APIRouter(tags=["Live & Real-time"])


# -----------------------------------------------------------------------------
# HTTP Live Endpoints
# -----------------------------------------------------------------------------

@router.get("/live/trains", summary="Get Simulated Train Movements")
def get_live_movements():
    provider = get_live_train_provider()
    status = provider.get_status()
    return {"provider_status": status, "source": provider.source, "items": provider.get_train_positions()}


@router.get("/live/trains/{train_id}", summary="Get One Simulated Train Movement")
def get_live_movement(train_id: str):
    provider = get_live_train_provider()
    movement = provider.get_train_positions()
    item = next((row for row in movement if row["train_id"] == train_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Train '{train_id}' not found")
    return {"provider_status": provider.get_status(), "source": provider.source, "data": item}


@router.get("/live/status", summary="Get Live Provider Status")
def get_live_status():
    return get_live_train_provider().get_status()


@router.post("/live/sync", summary="Synchronize Simulated Train Movements")
def sync_live_movements():
    provider = get_live_train_provider()
    items = provider.get_train_positions()
    provider_status = provider.get_status()
    sync_status = "SYNCED" if provider_status["status"] == "available" else "NO_EXTERNAL_DATA"
    return {"status": sync_status, "provider_status": provider_status, "source": provider.source, "count": len(items), "items": items}


# -----------------------------------------------------------------------------
# WebSocket Endpoints
# -----------------------------------------------------------------------------

async def stream(websocket: WebSocket, event_type: str):
    await websocket.accept()
    try:
        while True:
            provider = get_live_train_provider()
            payload = {
                "event_type": event_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": provider.source,
                "data": provider.get_train_positions() if event_type == "TRAIN_POSITION_UPDATED" else {},
            }
            await websocket.send_json(payload)
            await asyncio.sleep(5)
    except (WebSocketDisconnect, RuntimeError):
        return


@router.websocket("/ws/live")
async def live_socket(websocket: WebSocket):
    await stream(websocket, "TRAIN_POSITION_UPDATED")


@router.websocket("/ws/live-trains")
async def live_trains_socket(websocket: WebSocket):
    await stream(websocket, "TRAIN_POSITION_UPDATED")


@router.websocket("/ws/blocks")
async def blocks_socket(websocket: WebSocket):
    await stream(websocket, "BLOCK_STATUS_UPDATED")
