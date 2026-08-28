"""
Block Optimization Service for RailBlock AI.
"""

import pandas as pd
from app.config.settings import settings
from app.services.optimization.milp_solver import OptimizationEngine
from app.repositories.csv_repository import CSVRepository


class OptimizationService:
    def __init__(self):
        self.engine = OptimizationEngine()
        self.feasibility_repo = CSVRepository(settings.PROCESSED_DATA_ROOT / "feasibility_checked_tasks.csv")

    def run_optimization(self, candidates_df: pd.DataFrame = None) -> tuple[pd.DataFrame, dict]:
        if candidates_df is None:
            candidates_df = self.feasibility_repo.read_csv()
            candidates_df = candidates_df[candidates_df["overall_feasible"]].copy()

        selected_df, metrics = self.engine.optimize_blocks(candidates_df)
        return selected_df, metrics


PlannerService = OptimizationService
