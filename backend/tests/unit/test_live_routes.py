"""
Unit tests for Live Operations API routes (/api/live/*).
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_live_trains():
    response = client.get("/api/live/trains")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "provider_status" in data
    assert isinstance(data["items"], list)
    if len(data["items"]) > 0:
        first = data["items"][0]
        assert "train_id" in first
        assert "delay_minutes" in first


def test_get_live_status():
    response = client.get("/api/live/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "provider" in data


def test_post_live_sync():
    response = client.post("/api/live/sync")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "count" in data or "records_available" in data
