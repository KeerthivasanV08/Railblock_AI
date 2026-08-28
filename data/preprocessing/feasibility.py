"""
Constraint & Feasibility Engine for RailBlock AI (Vectorized).

Evaluates operational feasibility via tripartite matching (traffic availability + resource availability + spatial constraints).
Output: feasibility_checked_tasks.csv
"""

import logging
import numpy as np
import pandas as pd

from data.preprocessing.config import PROCESSED_DIR

logger = logging.getLogger(__name__)


def check_task_feasibility() -> pd.DataFrame:
    """
    Checks operational feasibility for each clustered maintenance task using vectorized operations.
    """
    clustered_path = PROCESSED_DIR / "clustered_tasks.csv"
    if not clustered_path.exists():
        from data.preprocessing.clustering import cluster_shadow_blocks
        clustered_df = cluster_shadow_blocks()
    else:
        clustered_df = pd.read_csv(clustered_path)

    resource_path = PROCESSED_DIR / "resource_availability.csv"
    if not resource_path.exists():
        from data.preprocessing.resource_enrichment import enrich_resource_availability
        res_df = enrich_resource_availability()
    else:
        res_df = pd.read_csv(resource_path)

    traffic_path = PROCESSED_DIR / "enriched_train_traffic.csv"
    if not traffic_path.exists():
        from data.preprocessing.traffic_enrichment import enrich_traffic_data
        traffic_df = enrich_traffic_data()
    else:
        traffic_df = pd.read_csv(traffic_path)

    # Join resource and traffic features efficiently via merge
    merged_df = clustered_df.merge(
        res_df[["task_id", "machine_available", "crew_available"]],
        on="task_id",
        how="left"
    ).merge(
        traffic_df[["section_id", "traffic_density"]],
        on="section_id",
        how="left"
    )

    mch_feasible = merged_df["machine_available"].fillna(False).values.astype(bool)
    crew_feasible = merged_df["crew_available"].fillna(False).values.astype(bool)
    traffic_feasible = (merged_df["traffic_density"].fillna(0.5).values < 0.85)
    time_feasible = (merged_df["estimated_duration_minutes"].fillna(120).values <= 240)
    spatially_feasible = ~merged_df["mapped_chainage_km"].isna().values

    overall = mch_feasible & crew_feasible & traffic_feasible & time_feasible & spatially_feasible

    # Rejection reasons array creation
    rejection_reasons = np.full(len(merged_df), "NONE", dtype=object)
    rejection_reasons[~overall & ~traffic_feasible] = "High Traffic Pressure / No Traffic Gap"
    rejection_reasons[~overall & traffic_feasible & ~mch_feasible] = "Machine Unavailable"
    rejection_reasons[~overall & traffic_feasible & mch_feasible & ~crew_feasible] = "Crew Unavailable"
    rejection_reasons[~overall & traffic_feasible & mch_feasible & crew_feasible & ~time_feasible] = "Insufficient Window Duration"
    rejection_reasons[~overall & traffic_feasible & mch_feasible & crew_feasible & time_feasible & ~spatially_feasible] = "Spatial Mapping Failure"

    feasibility_df = clustered_df.copy()
    feasibility_df["traffic_feasible"] = traffic_feasible
    feasibility_df["machine_feasible"] = mch_feasible
    feasibility_df["crew_feasible"] = crew_feasible
    feasibility_df["time_feasible"] = time_feasible
    feasibility_df["spatially_feasible"] = spatially_feasible
    feasibility_df["overall_feasible"] = overall
    feasibility_df["rejection_reason"] = rejection_reasons

    out_path = PROCESSED_DIR / "feasibility_checked_tasks.csv"
    feasibility_df.to_csv(out_path, index=False)
    logger.info(f"Generated {len(feasibility_df)} feasibility checked tasks at {out_path}")

    return feasibility_df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    check_task_feasibility()

