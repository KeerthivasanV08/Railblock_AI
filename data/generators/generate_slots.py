"""
Corridor Slot Availability Generator for RailBlock AI.

Generates data/raw/traffic/corridor_slot_availability.csv (>= 50,000 rows).
"""

import logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from data.generators.config import (
    RANDOM_SEED,
    TRAFFIC_DIR,
    NETWORK_DIR,
    MIN_SLOT_ROWS,
    START_DATE,
    SIMULATION_DAYS,
    SLOT_WINDOW_MINUTES,
)

logger = logging.getLogger(__name__)


def generate_slots(seed: int = RANDOM_SEED) -> pd.DataFrame:
    """
    Generates corridor slot availability records with traffic density and maintenance blocking status.
    """
    rng = np.random.default_rng(seed)
    TRAFFIC_DIR.mkdir(parents=True, exist_ok=True)

    sections_path = NETWORK_DIR / "block_sections.csv"
    if not sections_path.exists():
        raise FileNotFoundError(f"Missing required reference file: {sections_path}")
    sections_df = pd.read_csv(sections_path)
    section_ids = sections_df["section_id"].values

    sec_indices = rng.integers(0, len(section_ids), MIN_SLOT_ROWS)
    selected_sections = section_ids[sec_indices]

    day_offsets = rng.integers(0, SIMULATION_DAYS, MIN_SLOT_ROWS)
    durations = rng.choice(SLOT_WINDOW_MINUTES, size=MIN_SLOT_ROWS)

    window_starts = []
    window_ends = []
    densities = []
    is_blocked_list = []

    for i in range(MIN_SLOT_ROWS):
        d_offset = int(day_offsets[i])
        dur_min = int(durations[i])

        hour = int(rng.integers(0, 24))
        minute = int(rng.choice([0, 15, 30, 45]))
        
        w_start = datetime.combine(START_DATE + timedelta(days=d_offset), datetime.min.time()) + timedelta(hours=hour, minutes=minute)
        w_end = w_start + timedelta(minutes=dur_min)

        # Traffic density depends on peak hours (07-10, 17-21)
        h_start = w_start.hour
        if h_start in [7, 8, 9, 17, 18, 19, 20]:
            density = round(rng.uniform(0.70, 0.98), 2)
            # High traffic density -> mostly blocked (no maintenance slot available)
            is_blocked = bool(rng.random() < 0.85)
        elif h_start in [1, 2, 3, 4, 12, 13]:
            density = round(rng.uniform(0.10, 0.45), 2)
            # Low density -> open window for maintenance
            is_blocked = bool(rng.random() < 0.20)
        else:
            density = round(rng.uniform(0.40, 0.75), 2)
            is_blocked = bool(rng.random() < 0.50)

        window_starts.append(w_start.strftime("%Y-%m-%d %H:%M:%S"))
        window_ends.append(w_end.strftime("%Y-%m-%d %H:%M:%S"))
        densities.append(density)
        is_blocked_list.append(is_blocked)

    df = pd.DataFrame({
        "slot_id": [f"SLOT_{i+1:06d}" for i in range(MIN_SLOT_ROWS)],
        "section_id": selected_sections,
        "window_start": window_starts,
        "window_end": window_ends,
        "passenger_traffic_density": densities,
        "is_blocked": is_blocked_list
    })

    out_path = TRAFFIC_DIR / "corridor_slot_availability.csv"
    df.to_csv(out_path, index=False)
    logger.info(f"Generated {len(df)} corridor slot availability records at {out_path}")
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_slots()
