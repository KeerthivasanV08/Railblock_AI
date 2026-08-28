"""
Maintenance Task Priority & MDPS Scoring Service for RailBlock AI.
"""

import pandas as pd
from app.config.settings import settings
from app.services.priority.mdps_engine import MDPSEngine
from app.repositories.csv_repository import CSVRepository
from app.repositories.task_repository import TaskRepository


class PriorityService:
    def __init__(self):
        self.engine = MDPSEngine()
        self.mapped_repo = CSVRepository(settings.PROCESSED_DATA_ROOT / "spatially_mapped_tasks.csv")
        self.scored_repo = CSVRepository(settings.PROCESSED_DATA_ROOT / "scored_tasks.csv")
        self.task_repo = TaskRepository()

    def run_priority_scoring(self) -> pd.DataFrame:
        tasks_df = self.mapped_repo.read_csv()
        scored_df = self.engine.score_dataframe(tasks_df)
        self.scored_repo.write_csv(scored_df)
        return scored_df

    def get_task_priority(self, task_id: str) -> dict:
        task = self.task_repo.get_task_by_id(task_id)
        if not task:
            return None
        res = self.engine.calculate_priority(task)
        res["task_id"] = task_id
        return res


MDPSService = PriorityService
