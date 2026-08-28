"""
Train Timetable Data Generator for RailBlock AI.

Generates data/raw/traffic/train_timetable.csv (>= 50,000 rows).
"""

import logging
from datetime import datetime, timedelta, time
import numpy as np
import pandas as pd

from data.generators.config import (
    RANDOM_SEED,
    TRAFFIC_DIR,
    NETWORK_DIR,
    MIN_TRAIN_ROWS,
    TRAIN_TYPES,
    PRIORITY_CLASSES,
)

logger = logging.getLogger(__name__)

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def generate_timetable(seed: int = RANDOM_SEED) -> pd.DataFrame:
    """
    Generates realistic timetable records across corridor sections with peak/off-peak distributions.
    """
    rng = np.random.default_rng(seed)
    TRAFFIC_DIR.mkdir(parents=True, exist_ok=True)

    sections_path = NETWORK_DIR / "block_sections.csv"
    if not sections_path.exists():
        raise FileNotFoundError(f"Missing required reference file: {sections_path}")
    sections_df = pd.read_csv(sections_path)
    section_ids = sections_df["section_id"].values

    # Base pool of ~500 train numbers operating across section runs
    train_numbers = [f"{12000 + i}" if i % 2 == 0 else f"{22000 + i}" for i in range(500)]

    records = []
    num_sections = len(section_ids)

    # Generate MIN_TRAIN_ROWS timetable slots
    sec_indices = rng.integers(0, num_sections, MIN_TRAIN_ROWS)
    days = rng.choice(DAYS_OF_WEEK, size=MIN_TRAIN_ROWS)
    selected_trains = rng.choice(train_numbers, size=MIN_TRAIN_ROWS)

    for i in range(MIN_TRAIN_ROWS):
        sec_id = section_ids[sec_indices[i]]
        t_num = selected_trains[i]
        day = days[i]

        # Train type & priority correlation
        r_type = rng.random()
        if r_type < 0.45:
            t_type = "Express"
            priority = rng.choice(["Rajdhani", "Superfast"], p=[0.3, 0.7])
        elif r_type < 0.75:
            t_type = "Passenger"
            priority = "Mail Passenger"
        else:
            t_type = "Freight"
            priority = "Goods"

        # Departure time: Peak hours higher for passenger, off-peak for freight
        if t_type == "Freight":
            # Prefer night/mid-day off-peak hours
            hour = int(rng.choice([0, 1, 2, 3, 4, 11, 12, 13, 14, 22, 23]))
        else:
            # Morning (7-10) and Evening (17-21) peaks
            if rng.random() < 0.55:
                hour = int(rng.choice([7, 8, 9, 10, 17, 18, 19, 20, 21]))
            else:
                hour = int(rng.integers(0, 24))

        minute = int(rng.integers(0, 60))
        sec_offset = int(rng.integers(0, 60))

        base_date = datetime(2024, 1, 1, hour, minute, sec_offset)
        
        # Section travel duration: 5 to 30 minutes depending on train type
        if priority in ["Rajdhani", "Superfast"]:
            duration_mins = rng.integers(5, 12)
        elif t_type == "Passenger":
            duration_mins = rng.integers(10, 20)
        else:  # Freight
            duration_mins = rng.integers(15, 30)

        dep_dt = base_date
        arr_dt = dep_dt + timedelta(minutes=int(duration_mins))

        records.append({
            "train_number": t_num,
            "train_type": t_type,
            "section_id": sec_id,
            "scheduled_departure": dep_dt.strftime("%H:%M:%S"),
            "scheduled_arrival": arr_dt.strftime("%H:%M:%S"),
            "priority_class": priority,
            "day_of_week": day
        })

    df = pd.DataFrame(records)
    out_path = TRAFFIC_DIR / "train_timetable.csv"
    df.to_csv(out_path, index=False)
    logger.info(f"Generated {len(df)} timetable entries at {out_path}")
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_timetable()
