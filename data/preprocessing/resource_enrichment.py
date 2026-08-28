"""
Resource Enrichment Engine for RailBlock AI (Fully Vectorized Matrix Operations).

Matches maintenance tasks with heavy machinery and crew inventories based on geographic distance,
department, and availability status.
Output: resource_availability.csv
"""

import logging
import numpy as np
import pandas as pd

from data.preprocessing.config import RAW_DIR, PROCESSED_DIR, MAX_RESOURCE_DISTANCE_KM

logger = logging.getLogger(__name__)


def enrich_resource_availability() -> pd.DataFrame:
    """
    Computes time-dependent resource feasibility for tasks using fully vectorized matrix ops.
    """
    tasks_path = PROCESSED_DIR / "spatially_mapped_tasks.csv"
    if not tasks_path.exists():
        from data.preprocessing.spatial_mapping import map_spatial_locations
        tasks_df = map_spatial_locations()
    else:
        tasks_df = pd.read_csv(tasks_path)

    machines_df = pd.read_csv(RAW_DIR / "resources/machine_inventory.csv")
    crews_df = pd.read_csv(RAW_DIR / "resources/crew_inventory.csv")

    # Map department crew availability
    dept_crew_map = crews_df.groupby("department")["is_available"].any().to_dict()

    # Pre-filter available machines
    avail_mch = machines_df[machines_df["is_available"]].copy()

    task_lats = tasks_df["gps_latitude"].values
    task_lons = tasks_df["gps_longitude"].values
    req_resources = tasks_df["required_resource_type"].values
    departments = tasks_df["department"].values

    n_tasks = len(tasks_df)
    nearest_mch_arr = np.full(n_tasks, "NONE", dtype=object)
    min_dist_arr = np.full(n_tasks, 999.0, dtype=float)
    mch_avail_arr = np.zeros(n_tasks, dtype=bool)

    # Fast vectorization per resource type (only 4 unique machine types)
    for m_type in avail_mch["resource_type"].unique():
        task_mask = (req_resources == m_type)
        if not np.any(task_mask):
            continue

        m_sub = avail_mch[avail_mch["resource_type"] == m_type]
        m_lats = m_sub["current_latitude"].values
        m_lons = m_sub["current_longitude"].values
        m_ids = m_sub["resource_id"].values

        sub_lats = task_lats[task_mask][:, np.newaxis]  # Shape (N_sub, 1)
        sub_lons = task_lons[task_mask][:, np.newaxis]

        # Euclidean distance matrix (N_sub, M)
        d_lat = (sub_lats - m_lats[np.newaxis, :]) * 111.0
        d_lon = (sub_lons - m_lons[np.newaxis, :]) * 111.0 * np.cos(np.radians(sub_lats))
        dists = np.sqrt(d_lat ** 2 + d_lon ** 2)

        min_indices = np.argmin(dists, axis=1)
        min_distances = dists[np.arange(len(sub_lats)), min_indices]

        nearest_mch_arr[task_mask] = m_ids[min_indices]
        min_dist_arr[task_mask] = np.round(min_distances, 2)
        mch_avail_arr[task_mask] = True

    # Crew-only requirements do not need a machine inventory match. Their
    # feasibility is determined by the department crew availability below.
    crew_only_mask = np.isin(req_resources, ["Engineering crew", "TRD crew", "S&T crew"])
    mch_avail_arr[crew_only_mask] = True
    min_dist_arr[crew_only_mask] = 0.0

    crew_avail_arr = np.array([dept_crew_map.get(d, False) for d in departments])
    res_feasible_arr = mch_avail_arr & crew_avail_arr & (min_dist_arr <= MAX_RESOURCE_DISTANCE_KM)

    res_df = pd.DataFrame({
        "task_id": tasks_df["task_id"],
        "section_id": tasks_df["section_id"],
        "required_resource_type": req_resources,
        "nearest_machine": nearest_mch_arr,
        "machine_distance_km": min_dist_arr,
        "machine_available": mch_avail_arr,
        "crew_available": crew_avail_arr,
        "resource_feasible": res_feasible_arr,
        "utilization_rate": np.full(n_tasks, 0.75)
    })

    out_path = PROCESSED_DIR / "resource_availability.csv"
    res_df.to_csv(out_path, index=False)
    logger.info(f"Generated resource availability metrics ({len(res_df)} tasks) at {out_path}")

    return res_df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    enrich_resource_availability()

