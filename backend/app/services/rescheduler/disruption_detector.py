"""
Disruption Detection Service for RailBlock AI.
"""

from app.config.settings import settings
from app.services.rescheduler.impact_analyzer import DisruptionEngine
from app.repositories.disruption_repository import DisruptionRepository
from app.repositories.traffic_repository import TrafficRepository


class DisruptionService:
    def __init__(self):
        self.engine = DisruptionEngine()
        self.disruption_repo = DisruptionRepository()
        self.traffic_repo = TrafficRepository()

    def detect_disruptions(self) -> list:
        disruptions_df = self.disruption_repo.get_disruptions()
        delays_df = self.traffic_repo.get_live_delays()
        return self.engine.detect_disruptions(disruptions_df, delays_df)


DisruptionDetectorService = DisruptionService
