"""
Historical Block Records & MDPS Labels Generator for RailBlock AI.

Generates:
1. data/raw/historical/historical_block_records.csv (>= 50,000 rows)
2. data/raw/historical/mdps_training_labels.csv (>= 30,000 rows)
"""

import logging
import numpy as np
import pandas as pd

from data.generators.config import (
    RANDOM_SEED,
    HISTORICAL_DIR,
    DEFECTS_DIR,
    NETWORK_DIR,
    MIN_HISTORICAL_ROWS,
    MIN_MDPS_LABEL_ROWS,
    DEPARTMENTS,
)

logger = logging.getLogger(__name__)


def generate_historical_records(seed: int = RANDOM_SEED) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generates historical maintenance block request logs and MDPS ground truth priority labels.
    """
    rng = np.random.default_rng(seed)
    HISTORICAL_DIR.mkdir(parents=True, exist_ok=True)

    # Load block sections for section IDs
    sections_path = NETWORK_DIR / "block_sections.csv"
    if not sections_path.exists():
        raise FileNotFoundError(f"Missing required reference file: {sections_path}")
    sections_df = pd.read_csv(sections_path)
    section_ids = sections_df["section_id"].values

    # Load available task IDs from defects if present
    task_ids = []
    for defect_file in ["tms_defects.csv", "smms_defects.csv", "tdms_defects.csv"]:
        f_path = DEFECTS_DIR / defect_file
        if f_path.exists():
            d_df = pd.read_csv(f_path)
            task_ids.extend(d_df["task_id"].tolist())

    if not task_ids:
        task_ids = [f"HIST_TASK_{i+1:06d}" for i in range(10000)]

    # -------------------------------------------------------------------------
    # 1. HISTORICAL BLOCK RECORDS GENERATION
    # -------------------------------------------------------------------------
    selected_tasks = rng.choice(task_ids, size=MIN_HISTORICAL_ROWS)
    selected_sections = rng.choice(section_ids, size=MIN_HISTORICAL_ROWS)
    depts = rng.choice(DEPARTMENTS, size=MIN_HISTORICAL_ROWS)

    requested_windows = rng.choice([60, 90, 120, 180, 240, 300], size=MIN_HISTORICAL_ROWS)
    granted_windows = []
    outcomes = []
    was_deferred_list = []

    for i in range(MIN_HISTORICAL_ROWS):
        req_w = int(requested_windows[i])
        
        # Demanded vs Granted discrepancy model
        # 30% chance full grant, 50% chance partial grant, 20% chance severe reduction/rejection
        r_val = rng.random()
        if r_val < 0.30:
            grant_w = req_w
            outcome = "Fully Completed"
            was_def = False
        elif r_val < 0.80:
            # Partial grant: 30% to 80% of requested time
            grant_frac = rng.uniform(0.3, 0.8)
            grant_w = int(round((req_w * grant_frac) / 15) * 15)
            grant_w = max(15, min(req_w, grant_w))
            outcome = "Partially Completed"
            was_def = bool(rng.random() < 0.40)
        else:
            # Severe reduction or zero grant
            grant_w = int(rng.choice([0, 15, 30]))
            outcome = "Not Completed"
            was_def = True

        granted_windows.append(grant_w)
        outcomes.append(outcome)
        was_deferred_list.append(was_def)

    hist_df = pd.DataFrame({
        "record_id": [f"HIST_{i+1:06d}" for i in range(MIN_HISTORICAL_ROWS)],
        "task_id": selected_tasks,
        "department": depts,
        "section_id": selected_sections,
        "requested_window_minutes": requested_windows,
        "granted_window_minutes": granted_windows,
        "outcome": outcomes,
        "was_deferred": was_deferred_list
    })

    hist_path = HISTORICAL_DIR / "historical_block_records.csv"
    hist_df.to_csv(hist_path, index=False)
    logger.info(f"Generated {len(hist_df)} historical block records at {hist_path}")

    # -------------------------------------------------------------------------
    # 2. MDPS TRAINING LABELS GENERATION
    # -------------------------------------------------------------------------
    selected_mdps_tasks = rng.choice(task_ids, size=MIN_MDPS_LABEL_ROWS)
    severities = rng.choice(["A", "B", "C"], size=MIN_MDPS_LABEL_ROWS, p=[0.25, 0.50, 0.25])
    overdue_days = rng.integers(0, 45, MIN_MDPS_LABEL_ROWS)
    traffic_classes = rng.choice(["Low", "Medium", "High", "Critical Peak"], size=MIN_MDPS_LABEL_ROWS)
    deferred_counts = rng.integers(0, 6, MIN_MDPS_LABEL_ROWS)

    actual_priority_ranks = []

    for i in range(MIN_MDPS_LABEL_ROWS):
        sev = severities[i]
        o_days = int(overdue_days[i])
        t_class = traffic_classes[i]
        def_c = int(deferred_counts[i])

        # Underlying scoring formula with controlled noise
        sev_score = 45.0 if sev == "A" else (25.0 if sev == "B" else 10.0)
        overdue_score = min(o_days, 30) * 1.1
        defer_score = def_c * 4.5

        t_score = 15.0 if t_class == "Critical Peak" else (10.0 if t_class == "High" else 5.0)

        # Stochastic noise
        noise = rng.normal(0, 3.0)
        
        raw_rank = sev_score + overdue_score + defer_score + t_score + noise
        priority_rank = round(max(0.0, min(100.0, raw_rank)), 2)
        actual_priority_ranks.append(priority_rank)

    mdps_df = pd.DataFrame({
        "task_id": selected_mdps_tasks,
        "severity_class": severities,
        "overdue_days": overdue_days,
        "traffic_density_class": traffic_classes,
        "deferred_count": deferred_counts,
        "actual_priority_rank": actual_priority_ranks
    })

    mdps_path = HISTORICAL_DIR / "mdps_training_labels.csv"
    mdps_df.to_csv(mdps_path, index=False)
    logger.info(f"Generated {len(mdps_df)} MDPS training labels at {mdps_path}")

    return hist_df, mdps_df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_historical_records()
