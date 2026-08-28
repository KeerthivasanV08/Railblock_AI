"""
Traffic Operations Data Repository.
"""

from backend.app.core.config import settings
from backend.app.repositories.csv_repository import CSVRepository


class TrafficRepository:
    def __init__(self):
        self.timetable_repo = CSVRepository(settings.RAW_DATA_ROOT / "traffic/train_timetable.csv")
        self.delays_repo = CSVRepository(settings.RAW_DATA_ROOT / "traffic/live_train_delays.csv")
        self.goods_repo = CSVRepository(settings.RAW_DATA_ROOT / "traffic/goods_forecast.csv")
        self.slots_repo = CSVRepository(settings.RAW_DATA_ROOT / "traffic/corridor_slot_availability.csv")
        self.enriched_traffic_repo = CSVRepository(settings.PROCESSED_DATA_ROOT / "enriched_train_traffic.csv")

    def get_timetable(self):
        return self.timetable_repo.read_csv()

    def get_live_delays(self):
        return self.delays_repo.read_csv()

    def get_goods_forecast(self):
        return self.goods_repo.read_csv()

    def get_slot_availability(self):
        return self.slots_repo.read_csv()
