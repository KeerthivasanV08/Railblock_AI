"""
Live Train Delays Data Generator for RailBlock AI.

Generates data/raw/traffic/live_train_delays.csv (>= 50,000 rows).
"""

import logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from data.generators.config import (
    RANDOM_SEED,
    TRAFFIC_DIR,
    MIN_DELAY_ROWS,
    START_DATE,
    SIMULATION_DAYS,
    DELAY_REASONS,
)

logger = logging.getLogger(__name__)


def generate_live_delays(seed: int = RANDOM_SEED) -> pd.DataFrame:
    """
    Generates realistic live train delay records with right-skewed delay distribution
    and strict internal temporal consistency.
    """
    rng = np.random.default_rng(seed)
    TRAFFIC_DIR.mkdir(parents=True, exist_ok=True)

    # Load timetable trains if available, or generate train numbers
    timetable_path = TRAFFIC_DIR / "train_timetable.csv"
    if timetable_path.exists():
        tt_df = pd.read_csv(timetable_path)
        train_numbers = tt_df["train_number"].unique()
    else:
        train_numbers = [f"{12000 + i}" for i in range(500)]

    selected_trains = rng.choice(train_numbers, size=MIN_DELAY_ROWS)

    # Random dates across simulation window
    day_offsets = rng.integers(0, SIMULATION_DAYS, MIN_DELAY_ROWS)
    dates = [START_DATE + timedelta(days=int(d)) for d in day_offsets]

    # Right-skewed delay distribution (Gamma distribution)
    # Shape = 0.8, Scale = 15 -> mode ~0, mean ~12 mins, with long right tail
    raw_delays = rng.gamma(shape=0.8, scale=15.0, size=MIN_DELAY_ROWS)
    # 25% of trains run on-time (0 delay)
    ontime_mask = rng.random(MIN_DELAY_ROWS) < 0.25
    raw_delays[ontime_mask] = 0.0
    delay_minutes = np.round(raw_delays, 1)

    scheduled_times = []
    actual_times = []
    reasons = []

    for i in range(MIN_DELAY_ROWS):
        del_m = delay_minutes[i]
        
        hour = rng.integers(0, 24)
        minute = rng.integers(0, 60)
        sch_dt = datetime(2024, 1, 1, hour, minute)
        act_dt = sch_dt + timedelta(minutes=float(del_m))

        scheduled_times.append(sch_dt.strftime("%H:%M:%S"))
        actual_times.append(act_dt.strftime("%H:%M:%S"))

        if del_m == 0:
            reason = "Other"
        elif del_m > 60:
            reason = rng.choice(DELAY_REASONS, p=[0.4, 0.3, 0.2, 0.1])
        else:
            reason = rng.choice(DELAY_REASONS, p=[0.6, 0.15, 0.15, 0.1])

        reasons.append(reason)

    df = pd.DataFrame({
        "train_number": selected_trains,
        "date": [d.isoformat() for d in dates],
        "scheduled_time": scheduled_times,
        "actual_time": actual_times,
        "delay_minutes": delay_minutes,
        "delay_reason": reasons
    })

    out_path = TRAFFIC_DIR / "live_train_delays.csv"
    df.to_csv(out_path, index=False)
    logger.info(f"Generated {len(df)} live train delay records at {out_path}")
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_live_delays()
