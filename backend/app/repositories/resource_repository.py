"""
Resource Inventory Data Repository.
"""

from app.config.settings import settings
from app.repositories.csv_repository import CSVRepository


class ResourceRepository:
    def __init__(self):
        self.machines_repo = CSVRepository(settings.RAW_DATA_ROOT / "resources/machine_inventory.csv")
        self.crews_repo = CSVRepository(settings.RAW_DATA_ROOT / "resources/crew_inventory.csv")
        self.availability_repo = CSVRepository(settings.PROCESSED_DATA_ROOT / "resource_availability.csv")

    def get_machines(self):
        return self.machines_repo.read_csv()

    def get_crews(self):
        return self.crews_repo.read_csv()
