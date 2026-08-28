"""
Disruption Events Data Repository.
"""

from backend.app.core.config import settings
from backend.app.repositories.csv_repository import CSVRepository


class DisruptionRepository:
    def __init__(self):
        self.disruptions_repo = CSVRepository(settings.RAW_DATA_ROOT / "disruptions/disruption_events.csv")
        self.reschedule_log_repo = CSVRepository(settings.OUTPUT_DATA_ROOT / "disruption_reschedule_log.csv")

    def get_disruptions(self):
        return self.disruptions_repo.read_csv()

    def get_reschedule_log(self):
        return self.reschedule_log_repo.read_csv() if self.reschedule_log_repo.file_exists() else None
