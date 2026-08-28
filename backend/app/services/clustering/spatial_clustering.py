"""
Shadow-Block Discovery & Integrated Multi-Department Clustering Engine for RailBlock AI.

Identifies spatial overlap and department compatibility to group tasks into shadow blocks.
"""

import numpy as np
import pandas as pd


class ShadowBlockEngine:
    def __init__(self, proximity_threshold_km: float = 2.0):
        self.proximity_threshold_km = proximity_threshold_km

    def discover_shadow_blocks(self, tasks_df: pd.DataFrame) -> pd.DataFrame:
        """
        Clusters spatially mapped tasks into shadow-block candidates across departments.
        """
        if "mapped_chainage_km" not in tasks_df.columns:
            from app.services.spatial.coordinate_mapper import LinearReferenceEngine
            tasks_df = LinearReferenceEngine().translate_task_locations(tasks_df)

        tasks_df = tasks_df.sort_values(["section_id", "mapped_chainage_km"]).reset_index(drop=True)

        cluster_ids = []
        cluster_sizes = []
        depts_involved = []
        integrated_candidates = []
        overlap_scores = []
        is_primary_flags = []

        for sec_id, group in tasks_df.groupby("section_id", sort=False):
            kms = group["mapped_chainage_km"].values
            depts = group["department"].values
            n = len(group)

            c_idx = 1
            i = 0
            while i < n:
                start_km = kms[i]
                j = i + 1
                while j < n and (kms[j] - start_km) <= self.proximity_threshold_km:
                    j += 1

                c_size = j - i
                c_depts = set(depts[i:j])
                dept_str = ";".join(sorted(c_depts))
                is_integrated = (len(c_depts) >= 2) or (c_size >= 3)
                overlap_score = round(min(1.0, 0.5 + 0.25 * (len(c_depts) - 1) + 0.1 * (c_size - 1)), 2)

                cid = f"CLUST_{sec_id}_{c_idx:04d}"
                c_idx += 1

                for k in range(c_size):
                    cluster_ids.append(cid)
                    cluster_sizes.append(c_size)
                    depts_involved.append(dept_str)
                    integrated_candidates.append(is_integrated)
                    overlap_scores.append(overlap_score)
                    is_primary_flags.append(k == 0)

                i = j

        clustered_df = tasks_df.copy()
        clustered_df["cluster_id"] = cluster_ids
        clustered_df["cluster_size"] = cluster_sizes
        clustered_df["departments_involved"] = depts_involved
        clustered_df["integrated_block_candidate"] = integrated_candidates
        clustered_df["spatial_overlap_score"] = overlap_scores
        clustered_df["is_primary_task"] = is_primary_flags

        return clustered_df
