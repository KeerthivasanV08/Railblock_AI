"""
Disruption Events Data Generator for RailBlock AI.

Generates data/raw/disruptions/disruption_events.csv (>= 25,000 rows).
"""

import logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from data.generators.config import (
    RANDOM_SEED,
    DISRUPTIONS_DIR,
    NETWORK_DIR,
    MIN_DISRUPTION_ROWS,
    START_DATE,
    SIMULATION_DAYS,
    DISRUPTION_TYPES,
)

logger = logging.getLogger(__name__)


def generate_disruption_events(seed: int = RANDOM_SEED) -> pd.DataFrame:
    """
    Generates operational disruption events (Late Train, Emergency Defect, Machine Breakdown).
    """
    rng = np.random.default_rng(seed)
    DISRUPTIONS_DIR.mkdir(parents=True, exist_ok=True)

    sections_path = NETWORK_DIR / "block_sections.csv"
    if not sections_path.exists():
        raise FileNotFoundError(f"Missing required reference file: {sections_path}")
    sections_df = pd.read_csv(sections_path)
    section_ids = sections_df["section_id"].values

    sec_indices = rng.integers(0, len(section_ids), MIN_DISRUPTION_ROWS)
    selected_sections = section_ids[sec_indices]

    event_types = rng.choice(DISRUPTION_TYPES, size=MIN_DISRUPTION_ROWS, p=[0.50, 0.30, 0.20])
    severities = rng.choice(["Low", "Medium", "High"], size=MIN_DISRUPTION_ROWS, p=[0.50, 0.35, 0.15])

    day_offsets = rng.integers(0, SIMULATION_DAYS, MIN_DISRUPTION_ROWS)
    
    detected_at_list = []
    affected_blocks = []
    descriptions = []

    for i in range(MIN_DISRUPTION_ROWS):
        d_offset = int(day_offsets[i])
        h = int(rng.integers(0, 24))
        m = int(rng.integers(0, 60))
        
        det_dt = datetime.combine(START_DATE + timedelta(days=d_offset), datetime.min.time()) + timedelta(hours=h, minutes=m)
        detected_at_list.append(det_dt.strftime("%Y-%m-%d %H:%M:%S"))

        e_type = event_types[i]
        sev = severities[i]

        # 60% of disruptions directly affect an active/scheduled block
        if rng.random() < 0.60:
            aff_id = f"SLOT_{rng.integers(1, 50000):06d}"
        else:
            aff_id = ""

        affected_blocks.append(aff_id)

        if e_type == "Late Train":
            desc = f"Late express train delay cascading in section {selected_sections[i]} (Severity {sev})"
        elif e_type == "Emergency Defect":
            desc = f"Emergency rail/OHE defect detected requiring urgent track access in {selected_sections[i]}"
        else:
            desc = f"Tamping/BCM machine breakdown during block operation in {selected_sections[i]}"

        descriptions.append(desc)

    df = pd.DataFrame({
        "event_id": [f"DIS_{i+1:06d}" for i in range(MIN_DISRUPTION_ROWS)],
        "event_type": event_types,
        "section_id": selected_sections,
        "detected_at": detected_at_list,
        "affected_block_id": affected_blocks,
        "impact_description": descriptions,
        "severity": severities
    })

    out_path = DISRUPTIONS_DIR / "disruption_events.csv"
    df.to_csv(out_path, index=False)
    logger.info(f"Generated {len(df)} disruption events at {out_path}")
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_disruption_events()
