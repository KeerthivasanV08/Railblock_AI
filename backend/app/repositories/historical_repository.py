"""
Historical Block Records & MDPS Labels Repository.
"""

from backend.app.core.config import settings
from backend.app.repositories.csv_repository import CSVRepository


class HistoricalRepository:
    def __init__(self):
        self.records_repo = CSVRepository(settings.RAW_DATA_ROOT / "historical/historical_block_records.csv")
        self.labels_repo = CSVRepository(settings.RAW_DATA_ROOT / "historical/mdps_training_labels.csv")

    def get_records(self):
        return self.records_repo.read_csv()

    def get_labels(self):
        return self.labels_repo.read_csv()
