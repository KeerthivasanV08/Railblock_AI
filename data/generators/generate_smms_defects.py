"""
SMMS (Signal and Interlocking Management System) Defect Generator for RailBlock AI.

Generates data/raw/defects/smms_defects.csv (>= 25,000 rows).
"""

import logging
from datetime import timedelta
import numpy as np
import pandas as pd

from data.generators.config import (
    RANDOM_SEED,
    DEFECTS_DIR,
    NETWORK_DIR,
    MIN_SMMS_ROWS,
    START_DATE,
    SIMULATION_DAYS,
    SMMS_DEFECT_TYPES,
    DEFECT_SEVERITY_PROBS,
)

logger = logging.getLogger(__name__)


def generate_smms_defects(seed: int = RANDOM_SEED) -> pd.DataFrame:
    """
    Generates SMMS signal defect records referencing valid signal_id and section_id.
    """
    rng = np.random.default_rng(seed)
    DEFECTS_DIR.mkdir(parents=True, exist_ok=True)

    signals_path = NETWORK_DIR / "signal_reference.csv"
    if not signals_path.exists():
        raise FileNotFoundError(f"Missing required reference file: {signals_path}")
    signals_df = pd.read_csv(signals_path)

    # Randomly select signal records for MIN_SMMS_ROWS defects
    sig_indices = rng.integers(0, len(signals_df), MIN_SMMS_ROWS)
    selected_signals = signals_df.iloc[sig_indices].reset_index(drop=True)

    defect_types = rng.choice(SMMS_DEFECT_TYPES, size=MIN_SMMS_ROWS)

    severity_classes = []
    for d_type in defect_types:
        probs = DEFECT_SEVERITY_PROBS[d_type]
        sev = rng.choice(["A", "B", "C"], p=[probs["A"], probs["B"], probs["C"]])
        severity_classes.append(sev)
    severity_classes = np.array(severity_classes)

    day_offsets = rng.integers(0, SIMULATION_DAYS, MIN_SMMS_ROWS)
    logged_dates = [START_DATE + timedelta(days=int(d)) for d in day_offsets]

    target_completion_dates = []
    deferred_counts = []
    statuses = []

    status_options = ["Open", "Deferred", "Completed", "In-Progress"]

    for i in range(MIN_SMMS_ROWS):
        sev = severity_classes[i]
        log_d = logged_dates[i]

        if sev == "A":
            target_days = rng.integers(1, 6)
            defer_prob = 0.12
        elif sev == "B":
            target_days = rng.integers(5, 16)
            defer_prob = 0.30
        else:
            target_days = rng.integers(10, 31)
            defer_prob = 0.45

        target_d = log_d + timedelta(days=int(target_days))
        target_completion_dates.append(target_d)

        if rng.random() < defer_prob:
            d_count = rng.integers(1, 5)
            status = rng.choice(["Deferred", "Open", "In-Progress"], p=[0.6, 0.2, 0.2])
        else:
            d_count = 0
            status = rng.choice(status_options, p=[0.35, 0.10, 0.35, 0.20])

        deferred_counts.append(d_count)
        statuses.append(status)

    df = pd.DataFrame({
        "task_id": [f"SMMS_TASK_{i+1:06d}" for i in range(MIN_SMMS_ROWS)],
        "section_id": selected_signals["section_id"],
        "signal_id": selected_signals["signal_id"],
        "defect_type": defect_types,
        "severity_class": severity_classes,
        "logged_date": [d.isoformat() for d in logged_dates],
        "target_completion_date": [d.isoformat() for d in target_completion_dates],
        "deferred_count": deferred_counts,
        "status": statuses
    })

    out_path = DEFECTS_DIR / "smms_defects.csv"
    df.to_csv(out_path, index=False)
    logger.info(f"Generated {len(df)} SMMS defects at {out_path}")
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_smms_defects()
