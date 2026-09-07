"""
End-to-End Workflow Verification for RailBlock AI Intelligence Pipeline.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_e2e_health_and_system():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"

    r_val = client.post("/api/system/validate-data")
    assert r_val.status_code == 200
    assert "summary" in r_val.json()


def test_e2e_spatial_translation():
    payload = {
        "task_id": "T001",
        "section_id": "SEC_001",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "chainage": 10.5,
    }
    r = client.post("/api/ai/spatial-map", json=payload)
    assert r.status_code == 200
    assert "mapped_chainage_km" in r.json() or "status" in r.json()


def test_e2e_mdps_priority_with_xai():
    payload = {
        "severity_class": "A",
        "overdue_days": 14,
        "deferred_count": 2,
        "traffic_density": 0.85,
        "defect_type": "Rail Fracture",
    }
    r = client.post("/api/ai/priority", json=payload)
    assert r.status_code == 200
    res = r.json()
    assert res["status"] == "SUCCESS"
    assert "data" in res
    assert "explanation" in res
    assert res["data"]["criticality_score"] > 0


def test_e2e_shadow_block_clustering():
    payload = {
        "tasks": [
            {
                "task_id": "T001",
                "section_id": "SEC_001",
                "severity_class": "A",
                "defect_type": "Rail Fracture",
                "logged_date": "2024-01-01",
                "target_completion_date": "2024-01-15",
                "deferred_count": 2,
                "chainage_start": 10.0,
                "chainage_end": 10.5,
                "criticality_score": 80.0,
                "traffic_density": 0.8,
            }
        ]
    }
    r = client.post("/api/ai/cluster", json=payload)
    assert r.status_code == 200


def test_e2e_constraint_feasibility():
    payload = {
        "tasks": [
            {
                "task_id": "T001",
                "section_id": "SEC_001",
                "severity_class": "A",
                "defect_type": "Rail Fracture",
                "logged_date": "2024-01-01",
                "target_completion_date": "2024-01-15",
                "deferred_count": 2,
                "chainage_start": 10.0,
                "chainage_end": 10.5,
                "criticality_score": 80.0,
                "traffic_density": 0.8,
                "cluster_id": "CL_001",
            }
        ]
    }
    r = client.post("/api/ai/check-feasibility", json=payload)
    assert r.status_code == 200


def test_e2e_rescheduler_and_approval_workflow():
    # 1. Request rescheduling options
    r = client.post("/api/ai/reschedule?event_id=EV_101&affected_block_id=BLK_101")
    assert r.status_code == 200
    res = r.json()
    assert res["status"] == "SUCCESS"
    assert "constraint_validation_summary" in res
    assert len(res["options"]) >= 3
    assert res["approval_required"] is True

    # 2. Reject unconfirmed approval
    r_unconfirmed = client.post("/api/disruptions/approve?option_id=OPT_101&confirmed_feasible=false")
    assert r_unconfirmed.status_code == 200
    assert r_unconfirmed.json()["status"] == "REJECTED"

    # 3. Accept confirmed feasible approval
    r_confirmed = client.post("/api/disruptions/approve?option_id=OPT_101&confirmed_feasible=true")
    assert r_confirmed.status_code == 200
    assert r_confirmed.json()["status"] == "APPROVED"
