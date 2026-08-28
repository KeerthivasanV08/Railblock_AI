"""
Shadow-Block & Integrated Maintenance Clustering Engine for RailBlock AI (Linear O(N) Sliding Window).

Identifies spatial proximity overlaps across departments (Engineering, S&T, TRD)
on common block sections to form integrated multi-department mega blocks.
Output: clustered_tasks.csv
"""

import logging
import numpy as np
import pandas as pd

from data.preprocessing.config import PROCESSED_DIR, SPATIAL_PROXIMITY_KM

logger = logging.getLogger(__name__)


def cluster_shadow_blocks() -> pd.DataFrame:
    """
    Groups maintenance tasks into shadow-block clusters using an efficient O(N) sliding window.
    """
    tasks_path = PROCESSED_DIR / "scored_tasks.csv"
    if not tasks_path.exists():
        from data.preprocessing.mdps_dataset import train_mdps_model_and_score_tasks
        tasks_df, _ = train_mdps_model_and_score_tasks()
    else:
        tasks_df = pd.read_csv(tasks_path)

    tasks_df = tasks_df.sort_values(["section_id", "mapped_chainage_km"]).reset_index(drop=True)

    cluster_ids = []
    cluster_sizes = []
    departments_involved = []
    integrated_candidates = []
    spatial_overlap_scores = []

    # Process per section using linear sliding window
    for sec_id, group in tasks_df.groupby("section_id", sort=False):
        kms = group["mapped_chainage_km"].values
        depts = group["department"].values
        n = len(group)

        c_idx = 1
        i = 0
        while i < n:
            start_km = kms[i]
            # Find contiguous block within SPATIAL_PROXIMITY_KM
            j = i + 1
            while j < n and (kms[j] - start_km) <= SPATIAL_PROXIMITY_KM:
                j += 1

            c_size = j - i
            c_depts = set(depts[i:j])
            dept_str = ";".join(sorted(c_depts))
            is_integrated = (len(c_depts) >= 2) or (c_size >= 3)
            overlap_score = round(min(1.0, 0.5 + 0.25 * (len(c_depts) - 1) + 0.1 * (c_size - 1)), 2)

            cid = f"CLUST_{sec_id}_{c_idx:04d}"
            c_idx += 1

            for _ in range(c_size):
                cluster_ids.append(cid)
                cluster_sizes.append(c_size)
                departments_involved.append(dept_str)
                integrated_candidates.append(is_integrated)
                spatial_overlap_scores.append(overlap_score)

            i = j

    tasks_df["cluster_id"] = cluster_ids
    tasks_df["cluster_size"] = cluster_sizes
    tasks_df["departments_involved"] = departments_involved
    tasks_df["integrated_block_candidate"] = integrated_candidates
    tasks_df["spatial_overlap_score"] = spatial_overlap_scores

    out_path = PROCESSED_DIR / "clustered_tasks.csv"
    tasks_df.to_csv(out_path, index=False)
    logger.info(f"Generated {len(tasks_df)} clustered task records at {out_path}")

    return tasks_df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cluster_shadow_blocks()

