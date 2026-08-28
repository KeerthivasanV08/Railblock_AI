"""
Shadow Block Discovery & Clustering Service for RailBlock AI.
"""

import pandas as pd
from app.config.settings import settings
from app.services.clustering.spatial_clustering import ShadowBlockEngine
from app.repositories.csv_repository import CSVRepository


class ClusteringService:
    def __init__(self):
        self.engine = ShadowBlockEngine()
        self.scored_repo = CSVRepository(settings.PROCESSED_DATA_ROOT / "scored_tasks.csv")
        self.clustered_repo = CSVRepository(settings.PROCESSED_DATA_ROOT / "clustered_tasks.csv")

    def run_clustering(self) -> pd.DataFrame:
        tasks_df = self.scored_repo.read_csv()
        clustered_df = self.engine.discover_shadow_blocks(tasks_df)
        self.clustered_repo.write_csv(clustered_df)
        return clustered_df


ShadowBlockService = ClusteringService
