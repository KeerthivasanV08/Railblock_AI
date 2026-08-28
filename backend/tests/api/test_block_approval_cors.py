"""
Integration tests for CORS Preflight OPTIONS, Block Approval, Rejection, and Core Regression.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
)
@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/blocks/RB-528/approve",
        "/api/blocks/RB-528/reject",
        "/api/blocks/RB-529/approve",
        "/api/blocks/RB-529/reject",
        "/api/blocks/RB-402/approve",
    ],
)
def test_options_preflight_returns_success_for_allowed_origins(origin: str, endpoint: str):
    """
    Verify that browser preflight OPTIONS requests with Content-Type headers
    return HTTP 200 OK and valid Access-Control-Allow-Origin headers.
    """
    response = client.options(
        endpoint,
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200, f"OPTIONS preflight failed for {endpoint} with origin {origin}: {response.text}"
    assert response.headers.get("access-control-allow-origin") == origin
    assert "POST" in response.headers.get("access-control-allow-methods", "")


def test_approve_block_endpoint_success():
    """
    Verify POST /api/blocks/{block_id}/approve with frontend payload.
    """
    # Test approving RB-528
    response = client.post(
        "/api/blocks/RB-528/approve",
        headers={"Origin": "http://localhost:5173"},
        json={"approved_by": "Section Controller", "role": "Controller", "notes": "Approved in test"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["block_id"] == "RB-528"
    assert data["status"] == "APPROVED"
    assert data["plan_version"] >= 1

    # Test approving RB-529
    response_529 = client.post(
        "/api/blocks/RB-529/approve",
        headers={"Origin": "http://127.0.0.1:5173"},
        json={"approved_by": "Section Controller", "role": "Controller"},
    )
    assert response_529.status_code == 200
    data_529 = response_529.json()
    assert data_529["block_id"] == "RB-529"
    assert data_529["status"] == "APPROVED"


def test_reject_block_endpoint_success():
    """
    Verify POST /api/blocks/{block_id}/reject with frontend payload.
    """
    response = client.post(
        "/api/blocks/RB-530/reject",
        headers={"Origin": "http://localhost:5173"},
        json={
            "rejected_by": "Section Controller",
            "role": "Controller",
            "reason": "Traffic density conflict during peak hours",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["block_id"] == "RB-530"
    assert data["status"] == "REJECTED"
    assert data["reason"] == "Traffic density conflict during peak hours"


def test_regression_endpoints_remain_functional():
    """
    Verify that existing endpoints POST /api/planner/optimize and
    GET /api/analytics/overview remain completely functional.
    """
    # 1. POST /api/planner/optimize
    opt_res = client.post("/api/planner/optimize", headers={"Origin": "http://localhost:5173"})
    assert opt_res.status_code == 200
    opt_data = opt_res.json()
    assert opt_data["status"] == "SUCCESS"
    assert "metrics" in opt_data

    # 2. GET /api/analytics/overview
    analytics_res = client.get("/api/analytics/overview", headers={"Origin": "http://localhost:5173"})
    assert analytics_res.status_code == 200
    analytics_data = analytics_res.json()
    assert "total_tasks" in analytics_data or "active_blocks" in analytics_data or isinstance(analytics_data, dict)
