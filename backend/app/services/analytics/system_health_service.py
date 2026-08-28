"""
System Health & Dataset Status Service for RailBlock AI.
"""

from typing import Dict, Any
from app.config.settings import settings
from app.repositories.csv_repository import CSVRepository
from app.services.priority.mdps_engine import MDPSEngine


class SystemHealthService:
    def get_system_health(self) -> Dict[str, Any]:
        rl_avail = (settings.MODEL_ROOT / "rl_rescheduler_policy.pkl").exists()
        mdps_status = MDPSEngine().get_model_status()

        return {
            "backend": "healthy",
            "data_source": "csv",
            "database": False,
            "authentication": False,
            "models": {
                "mdps": mdps_status,
                "rl": "available" if rl_avail else "fallback_optimization"
            },
            "live_provider": {
                "configured_provider": settings.LIVE_TRAIN_PROVIDER,
                "external_configured": bool(settings.EXTERNAL_LIVE_API_BASE_URL and settings.EXTERNAL_LIVE_API_TOKEN),
            },
        }

    def get_data_status(self) -> Dict[str, Any]:
        raw_files = [
            "network/stations.csv", "network/block_sections.csv", "network/track_geometry.csv",
            "network/ohe_mast_reference.csv", "network/signal_reference.csv",
            "defects/tms_defects.csv", "defects/smms_defects.csv", "defects/tdms_defects.csv",
            "traffic/train_timetable.csv", "traffic/live_train_delays.csv", "traffic/goods_forecast.csv",
            "traffic/corridor_slot_availability.csv", "resources/machine_inventory.csv",
            "resources/crew_inventory.csv", "historical/historical_block_records.csv",
            "historical/mdps_training_labels.csv", "disruptions/disruption_events.csv",
            "calendars/seasonal_calendar.csv", "calendars/festival_traffic_calendar.csv"
        ]

        status = {}
        for rel_path in raw_files:
            f_path = settings.RAW_DATA_ROOT / rel_path
            repo = CSVRepository(f_path)
            status[rel_path] = repo.get_file_metadata()

        return {"datasets": status}
