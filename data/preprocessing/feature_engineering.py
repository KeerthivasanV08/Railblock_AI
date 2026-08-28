"""
Feature Engineering Engine for RailBlock AI.

Combines maintenance, spatial, traffic, resource, seasonal, historical, MDPS,
cluster, and feasibility features into planning_features.csv to support AI optimization models.
"""

import logging
import pandas as pd

from data.preprocessing.config import RAW_DIR, PROCESSED_DIR

logger = logging.getLogger(__name__)


def build_planning_features() -> pd.DataFrame:
    """
    Constructs the master planning features dataset for downstream planning models.
    """
    feasibility_path = PROCESSED_DIR / "feasibility_checked_tasks.csv"
    if not feasibility_path.exists():
        from data.preprocessing.feasibility import check_task_feasibility
        tasks_df = check_task_feasibility()
    else:
        tasks_df = pd.read_csv(feasibility_path)

    traffic_df = pd.read_csv(PROCESSED_DIR / "enriched_train_traffic.csv")
    res_df = pd.read_csv(PROCESSED_DIR / "resource_availability.csv")
    s_cal = pd.read_csv(RAW_DIR / "calendars/seasonal_calendar.csv")

    # Merge traffic features
    planning_df = tasks_df.merge(
        traffic_df[["section_id", "train_count", "traffic_density", "average_delay", "traffic_pressure_score"]],
        on="section_id",
        how="left"
    )

    # Merge resource features
    planning_df = planning_df.merge(
        res_df[["task_id", "nearest_machine", "machine_distance_km", "resource_feasible"]],
        on="task_id",
        how="left"
    )

    # Add seasonal risk factor (mean season risk)
    avg_season_risk = s_cal["risk_factor"].mean()
    planning_df["seasonal_risk_factor"] = round(avg_season_risk, 2)

    # Sort deterministically
    planning_df = planning_df.sort_values("priority_rank").reset_index(drop=True)

    out_path = PROCESSED_DIR / "planning_features.csv"
    planning_df.to_csv(out_path, index=False)
    logger.info(f"Generated {len(planning_df)} master planning features at {out_path}")

    return planning_df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    build_planning_features()

