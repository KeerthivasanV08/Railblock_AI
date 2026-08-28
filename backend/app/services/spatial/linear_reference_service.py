"""
Spatial & Linear Referencing Service for RailBlock AI.
"""

import pandas as pd
from app.config.settings import settings
from app.services.spatial.coordinate_mapper import LinearReferenceEngine
from app.repositories.csv_repository import CSVRepository


class SpatialService:
    def __init__(self):
        self.engine = LinearReferenceEngine()
        self.unified_repo = CSVRepository(settings.PROCESSED_DATA_ROOT / "unified_maintenance_tasks.csv")
        self.mapped_repo = CSVRepository(settings.PROCESSED_DATA_ROOT / "spatially_mapped_tasks.csv")

    def run_spatial_mapping(self) -> pd.DataFrame:
        tasks_df = self.unified_repo.read_csv()
        mapped_df = self.engine.translate_task_locations(tasks_df)
        self.mapped_repo.write_csv(mapped_df)
        return mapped_df


# Alias for canonical target nomenclature
LinearReferenceService = SpatialService
