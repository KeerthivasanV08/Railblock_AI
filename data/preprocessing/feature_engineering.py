"""
Feature Engineering Engine for RailBlock AI.

Combines maintenance, spatial, traffic, resource, seasonal, historical, MDPS,
cluster, and feasibility features into planning_features.csv to support AI optimization models.
"""

import logging
import pandas as pd

from data.preprocessing.config import RAW_DIR, PROCESSED_DIR

logger = logging.getLogger(__name__)


def enrich_tasks_with_weather(frame: pd.DataFrame) -> pd.DataFrame:
    """
    Enriches a task DataFrame with section SRS, live weather severity,
    and weather maintenance suitability.
    """
    df = frame.copy()
    try:
        from app.engines.seasonal_risk_engine import seasonal_risk_engine
        srs_list = []
        live_list = []
        suitability_list = []

        for _, row in df.iterrows():
            sec = str(row.get("section_id", ""))
            asset = str(row.get("department", row.get("asset_type", "TRACK")))
            risk_obj = seasonal_risk_engine.calculate_srs(sec, asset_type=asset)
            srs_val = risk_obj.srs
            live_val = risk_obj.live_weather_severity if risk_obj.live_weather_severity is not None else 20.0
            suitability = round(max(0.0, 1.0 - ((srs_val * 0.4 + live_val * 0.6) / 100.0)), 2)

            srs_list.append(srs_val)
            live_list.append(live_val)
            suitability_list.append(suitability)

        df["srs"] = srs_list
        df["seasonal_risk_score"] = srs_list
        df["live_weather_severity"] = live_list
        df["live_weather_risk_score"] = live_list
        df["weather_maintenance_suitability"] = suitability_list
        df["seasonal_risk_factor"] = [round(v / 100.0, 2) for v in srs_list]
    except Exception as e:
        logger.warning(f"Could not load SeasonalRiskEngine in enrich_tasks_with_weather: {e}")
        df["srs"] = 35.0
        df["seasonal_risk_score"] = 35.0
        df["live_weather_severity"] = 20.0
        df["live_weather_risk_score"] = 20.0
        df["weather_maintenance_suitability"] = 0.75
        df["seasonal_risk_factor"] = 0.35
    return df


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

    # Enrich with weather features
    planning_df = enrich_tasks_with_weather(planning_df)

    # Sort deterministically
    if "priority_rank" in planning_df.columns:
        planning_df = planning_df.sort_values("priority_rank").reset_index(drop=True)

    out_path = PROCESSED_DIR / "planning_features.csv"
    planning_df.to_csv(out_path, index=False)
    logger.info(f"Generated {len(planning_df)} master planning features at {out_path}")

    return planning_df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    build_planning_features()

