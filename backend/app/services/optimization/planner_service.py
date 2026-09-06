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

        # Augment with seasonal intelligence if missing
        if "seasonal_risk_score" not in candidates_df.columns and "section_id" in candidates_df.columns:
            sensitivity_path = settings.DERIVED_DATA_ROOT / "weather" / "section_weather_sensitivity.csv"
            if sensitivity_path.exists():
                try:
                    sens_df = pd.read_csv(sensitivity_path, usecols=["section_id", "overall_section_vulnerability"])
                    sens_map = dict(zip(sens_df["section_id"], sens_df["overall_section_vulnerability"]))
                    candidates_df["seasonal_risk_score"] = candidates_df["section_id"].map(sens_map).fillna(20.0)
                except Exception:
                    candidates_df["seasonal_risk_score"] = 20.0

        selected_df, metrics = self.engine.optimize_blocks(candidates_df)
        return selected_df, metrics


PlannerService = OptimizationService
