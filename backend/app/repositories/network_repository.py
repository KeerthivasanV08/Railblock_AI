"""
Network Infrastructure Data Repository.
"""

from backend.app.core.config import settings
from backend.app.repositories.csv_repository import CSVRepository


class NetworkRepository:
    def __init__(self):
        self.stations_repo = CSVRepository(settings.RAW_DATA_ROOT / "network/stations.csv")
        self.sections_repo = CSVRepository(settings.RAW_DATA_ROOT / "network/block_sections.csv")
        self.geometry_repo = CSVRepository(settings.RAW_DATA_ROOT / "network/track_geometry.csv")
        self.masts_repo = CSVRepository(settings.RAW_DATA_ROOT / "network/ohe_mast_reference.csv")
        self.signals_repo = CSVRepository(settings.RAW_DATA_ROOT / "network/signal_reference.csv")

    def get_all_stations(self):
        return self.stations_repo.read_csv()

    def get_all_sections(self):
        return self.sections_repo.read_csv()

    def get_section_by_id(self, section_id: str):
        return self.sections_repo.get_by_id("section_id", section_id)
