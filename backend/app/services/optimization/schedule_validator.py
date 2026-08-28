"""
Tripartite Feasibility & Schedule Validation Service for RailBlock AI.
"""

import pandas as pd
from app.config.settings import settings
from app.services.optimization.constraints import ConstraintEngine
from app.repositories.csv_repository import CSVRepository


class FeasibilityService:
    def __init__(self):
        self.engine = ConstraintEngine()
        self.clustered_repo = CSVRepository(settings.PROCESSED_DATA_ROOT / "clustered_tasks.csv")
        self.feasibility_repo = CSVRepository(settings.PROCESSED_DATA_ROOT / "feasibility_checked_tasks.csv")
        self.resource_repo = CSVRepository(settings.PROCESSED_DATA_ROOT / "resource_availability.csv")
        self.traffic_repo = CSVRepository(settings.PROCESSED_DATA_ROOT / "enriched_train_traffic.csv")

    def run_feasibility_check(self) -> pd.DataFrame:
        tasks_df = self.clustered_repo.read_csv()
        resource_df = self.resource_repo.read_csv() if self.resource_repo.file_exists() else None
        traffic_df = self.traffic_repo.read_csv() if self.traffic_repo.file_exists() else None
        feas_df = self.engine.check_feasibility(tasks_df, traffic_df=traffic_df, resource_df=resource_df)
        self.feasibility_repo.write_csv(feas_df)
        return feas_df


ScheduleValidatorService = FeasibilityService
