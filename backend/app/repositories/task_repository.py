"""
Maintenance Tasks Data Repository.
"""

from app.config.settings import settings
from app.repositories.csv_repository import CSVRepository


class TaskRepository:
    def __init__(self):
        self.tms_repo = CSVRepository(settings.RAW_DATA_ROOT / "defects/tms_defects.csv")
        self.smms_repo = CSVRepository(settings.RAW_DATA_ROOT / "defects/smms_defects.csv")
        self.tdms_repo = CSVRepository(settings.RAW_DATA_ROOT / "defects/tdms_defects.csv")
        self.unified_repo = CSVRepository(settings.PROCESSED_DATA_ROOT / "unified_maintenance_tasks.csv")
        self.scored_repo = CSVRepository(settings.PROCESSED_DATA_ROOT / "scored_tasks.csv")

    def get_unified_tasks(self):
        return self.unified_repo.read_csv()

    def get_scored_tasks(self):
        return self.scored_repo.read_csv()

    def get_task_by_id(self, task_id: str):
        if self.scored_repo.file_exists():
            item = self.scored_repo.get_by_id("task_id", task_id)
            if item:
                return item
        if self.unified_repo.file_exists():
            return self.unified_repo.get_by_id("task_id", task_id)

        # Fallback raw defect lookup
        for repo in (self.tms_repo, self.smms_repo, self.tdms_repo):
            item = repo.get_by_id("task_id", task_id)
            if item:
                return item
        return None
