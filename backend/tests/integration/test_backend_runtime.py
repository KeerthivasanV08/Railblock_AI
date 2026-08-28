from fastapi.testclient import TestClient

from app.main import app
from app.services.validation_service import ValidationService
from app.engines.mdps_engine import MDPSEngine
from app.live.provider import get_live_train_provider


client = TestClient(app)


def test_backend_routes_are_registered():
    paths = {route.path for route in app.routes if hasattr(route, "path")}
    assert "/health" in paths
    assert "/api/system/validate-data" in paths
    assert "/api/ai/priority" in paths
    assert "/api/planning/weekly" in paths
    assert "/ws/live" in paths


def test_validation_service_reports_structured_status():
    status = ValidationService().validate_all_datasets()
    assert status["status"] in {"PASS", "WARNING", "ERROR"}
    assert "datasets" in status
    assert "summary" in status
    assert status["summary"]["total_rows"] >= 0


def test_mdps_engine_loads_valid_artifact_or_falls_back_cleanly():
    status = MDPSEngine().get_model_status()
    assert "fallback_reason" in status
    assert status["fallback"] is (not status["model_available"])
    assert status["scoring_mode"] in {
        "deterministic_mdps",
        "ml_artifact_available_with_deterministic_guardrail",
    }


def test_live_provider_is_healthy_and_simulated():
    provider = get_live_train_provider()
    status = provider.get_status()
    assert status["provider"] == "simulation"
    assert provider.source == "SIMULATED"
    assert isinstance(provider.get_train_positions(), list)


def test_core_endpoints_respond_successfully():
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"

    validate = client.post("/api/system/validate-data")
    assert validate.status_code == 200
    assert "datasets" in validate.json()

    live = client.get("/api/live/status")
    assert live.status_code == 200
    assert live.json()["provider"] == "simulation"
