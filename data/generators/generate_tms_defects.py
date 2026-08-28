"""
TMS (Track Management System) Defect Generator for RailBlock AI.

Generates data/raw/defects/tms_defects.csv (>= 30,000 rows).
"""

import logging
from datetime import timedelta
import numpy as np
import pandas as pd

from data.generators.config import (
    RANDOM_SEED,
    DEFECTS_DIR,
    NETWORK_DIR,
    MIN_TMS_ROWS,
    START_DATE,
    END_DATE,
    SIMULATION_DAYS,
    TMS_DEFECT_TYPES,
    DEFECT_SEVERITY_PROBS,
)

logger = logging.getLogger(__name__)


def generate_tms_defects(seed: int = RANDOM_SEED) -> pd.DataFrame:
    """
    Generates TMS track defect records with realistic severity correlations,
    target completion dates, deferral counts, and status logic.
    """
    rng = np.random.default_rng(seed)
    DEFECTS_DIR.mkdir(parents=True, exist_ok=True)

    # Load block sections for valid section_id and chainage bounds
    sections_path = NETWORK_DIR / "block_sections.csv"
    if not sections_path.exists():
        raise FileNotFoundError(f"Missing required reference file: {sections_path}")
    sections_df = pd.read_csv(sections_path)

    # Randomly select section indices for MIN_TMS_ROWS defects
    sec_indices = rng.integers(0, len(sections_df), MIN_TMS_ROWS)
    selected_sections = sections_df.iloc[sec_indices].reset_index(drop=True)

    # Generate defect types
    defect_types = rng.choice(TMS_DEFECT_TYPES, size=MIN_TMS_ROWS)

    # Generate severity classes based on defect_type specific probability distributions
    severity_classes = []
    for d_type in defect_types:
        probs = DEFECT_SEVERITY_PROBS[d_type]
        sev = rng.choice(["A", "B", "C"], p=[probs["A"], probs["B"], probs["C"]])
        severity_classes.append(sev)
    severity_classes = np.array(severity_classes)

    # Generate start_km and end_km within section bounds
    start_kms = []
    end_kms = []
    for i, row in selected_sections.iterrows():
        s_min = row["start_km"]
        s_max = row["end_km"]
        length = s_max - s_min
        
        # Defect span typically 0.05 to 1.5 km
        defect_length = min(length * 0.5, rng.uniform(0.05, 1.5))
        d_start = rng.uniform(s_min, max(s_min, s_max - defect_length))
        d_end = min(s_max, d_start + defect_length)
        start_kms.append(round(d_start, 3))
        end_kms.append(round(d_end, 3))

    # Generate logged_dates uniformly over simulation period
    day_offsets = rng.integers(0, SIMULATION_DAYS, MIN_TMS_ROWS)
    logged_dates = [START_DATE + timedelta(days=int(d)) for d in day_offsets]

    # Calculate target_completion_days based on severity
    # Severity A: 1-7 days, Severity B: 7-21 days, Severity C: 14-45 days
    target_completion_dates = []
    deferred_counts = []
    statuses = []

    status_options = ["Open", "Deferred", "Completed", "In-Progress"]

    for i in range(MIN_TMS_ROWS):
        sev = severity_classes[i]
        log_d = logged_dates[i]

        if sev == "A":
            target_days = rng.integers(1, 8)
            defer_prob = 0.15
        elif sev == "B":
            target_days = rng.integers(7, 22)
            defer_prob = 0.35
        else:
            target_days = rng.integers(14, 46)
            defer_prob = 0.50

        target_d = log_d + timedelta(days=int(target_days))
        target_completion_dates.append(target_d)

        # Deferral logic
        if rng.random() < defer_prob:
            d_count = rng.integers(1, 5)
            status = rng.choice(["Deferred", "Open", "In-Progress"], p=[0.6, 0.2, 0.2])
        else:
            d_count = 0
            status = rng.choice(status_options, p=[0.3, 0.1, 0.4, 0.2])

        deferred_counts.append(d_count)
        statuses.append(status)

    df = pd.DataFrame({
        "task_id": [f"TMS_TASK_{i+1:06d}" for i in range(MIN_TMS_ROWS)],
        "section_id": selected_sections["section_id"],
        "start_km": start_kms,
        "end_km": end_kms,
        "defect_type": defect_types,
        "severity_class": severity_classes,
        "logged_date": [d.isoformat() for d in logged_dates],
        "target_completion_date": [d.isoformat() for d in target_completion_dates],
        "deferred_count": deferred_counts,
        "status": statuses
    })

    out_path = DEFECTS_DIR / "tms_defects.csv"
    df.to_csv(out_path, index=False)
    logger.info(f"Generated {len(df)} TMS defects at {out_path}")
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_tms_defects()
