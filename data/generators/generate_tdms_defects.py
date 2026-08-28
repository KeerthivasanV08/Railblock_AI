"""
TDMS (Traction Distribution Management System) Defect Generator for RailBlock AI.

Generates data/raw/defects/tdms_defects.csv (>= 25,000 rows).
"""

import logging
from datetime import timedelta
import numpy as np
import pandas as pd

from data.generators.config import (
    RANDOM_SEED,
    DEFECTS_DIR,
    NETWORK_DIR,
    MIN_TDMS_ROWS,
    START_DATE,
    SIMULATION_DAYS,
    TDMS_DEFECT_TYPES,
    DEFECT_SEVERITY_PROBS,
)

logger = logging.getLogger(__name__)


def generate_tdms_defects(seed: int = RANDOM_SEED) -> pd.DataFrame:
    """
    Generates TDMS OHE defect records referencing valid mast_number and section_id.
    """
    rng = np.random.default_rng(seed)
    DEFECTS_DIR.mkdir(parents=True, exist_ok=True)

    masts_path = NETWORK_DIR / "ohe_mast_reference.csv"
    if not masts_path.exists():
        raise FileNotFoundError(f"Missing required reference file: {masts_path}")
    masts_df = pd.read_csv(masts_path)

    # Randomly select OHE mast records for MIN_TDMS_ROWS defects
    mast_indices = rng.integers(0, len(masts_df), MIN_TDMS_ROWS)
    selected_masts = masts_df.iloc[mast_indices].reset_index(drop=True)

    defect_types = rng.choice(TDMS_DEFECT_TYPES, size=MIN_TDMS_ROWS)

    severity_classes = []
    for d_type in defect_types:
        probs = DEFECT_SEVERITY_PROBS[d_type]
        sev = rng.choice(["A", "B", "C"], p=[probs["A"], probs["B"], probs["C"]])
        severity_classes.append(sev)
    severity_classes = np.array(severity_classes)

    day_offsets = rng.integers(0, SIMULATION_DAYS, MIN_TDMS_ROWS)
    logged_dates = [START_DATE + timedelta(days=int(d)) for d in day_offsets]

    target_completion_dates = []
    deferred_counts = []
    statuses = []

    status_options = ["Open", "Deferred", "Completed", "In-Progress"]

    for i in range(MIN_TDMS_ROWS):
        sev = severity_classes[i]
        log_d = logged_dates[i]

        if sev == "A":
            target_days = rng.integers(1, 7)
            defer_prob = 0.10
        elif sev == "B":
            target_days = rng.integers(6, 18)
            defer_prob = 0.28
        else:
            target_days = rng.integers(12, 35)
            defer_prob = 0.40

        target_d = log_d + timedelta(days=int(target_days))
        target_completion_dates.append(target_d)

        if rng.random() < defer_prob:
            d_count = rng.integers(1, 5)
            status = rng.choice(["Deferred", "Open", "In-Progress"], p=[0.6, 0.2, 0.2])
        else:
            d_count = 0
            status = rng.choice(status_options, p=[0.30, 0.10, 0.40, 0.20])

        deferred_counts.append(d_count)
        statuses.append(status)

    df = pd.DataFrame({
        "task_id": [f"TDMS_TASK_{i+1:06d}" for i in range(MIN_TDMS_ROWS)],
        "section_id": selected_masts["section_id"],
        "mast_number": selected_masts["mast_number"],
        "defect_type": defect_types,
        "severity_class": severity_classes,
        "logged_date": [d.isoformat() for d in logged_dates],
        "target_completion_date": [d.isoformat() for d in target_completion_dates],
        "deferred_count": deferred_counts,
        "status": statuses
    })

    out_path = DEFECTS_DIR / "tdms_defects.csv"
    df.to_csv(out_path, index=False)
    logger.info(f"Generated {len(df)} TDMS defects at {out_path}")
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_tdms_defects()
