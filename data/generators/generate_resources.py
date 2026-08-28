"""
Resource Inventory Data Generator for RailBlock AI.

Generates:
1. data/raw/resources/machine_inventory.csv (~120 rows)
2. data/raw/resources/crew_inventory.csv (~200 rows)
"""

import logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from data.generators.config import (
    RANDOM_SEED,
    RESOURCES_DIR,
    NETWORK_DIR,
    NUM_MACHINES,
    NUM_CREWS,
    DEPARTMENTS,
)

logger = logging.getLogger(__name__)

MACHINE_TYPES = [
    "Tamping Machine",
    "Ballast Cleaning Machine",
    "Tower Wagon",
    "Rail Grinder"
]


def generate_resources(seed: int = RANDOM_SEED) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generates machine inventory and maintenance crew inventory records.
    """
    rng = np.random.default_rng(seed)
    RESOURCES_DIR.mkdir(parents=True, exist_ok=True)

    stations_path = NETWORK_DIR / "stations.csv"
    if not stations_path.exists():
        raise FileNotFoundError(f"Missing required reference file: {stations_path}")
    stations_df = pd.read_csv(stations_path)

    # Major depot stations
    depot_stations = stations_df.sample(min(10, len(stations_df)), random_state=seed)["station_name"].values

    # -------------------------------------------------------------------------
    # 1. MACHINE INVENTORY
    # -------------------------------------------------------------------------
    machines_list = []
    for i in range(NUM_MACHINES):
        m_type = rng.choice(MACHINE_TYPES, p=[0.40, 0.25, 0.25, 0.10])
        depot = rng.choice(depot_stations)
        
        # Current coords near station depot
        depot_row = stations_df[stations_df["station_name"] == depot].iloc[0]
        c_lat = round(depot_row["latitude"] + rng.normal(0, 0.005), 6)
        c_lon = round(depot_row["longitude"] + rng.normal(0, 0.005), 6)
        
        is_avail = bool(rng.random() < 0.82)
        last_updated = (datetime(2024, 1, 1) + timedelta(days=int(rng.integers(0, 365)), hours=int(rng.integers(0, 24)))).strftime("%Y-%m-%d %H:%M:%S")

        machines_list.append({
            "resource_id": f"MCH_{i+1:04d}",
            "resource_type": m_type,
            "home_depot": depot,
            "current_latitude": c_lat,
            "current_longitude": c_lon,
            "is_available": is_avail,
            "last_updated": last_updated
        })

    machines_df = pd.DataFrame(machines_list)
    machines_path = RESOURCES_DIR / "machine_inventory.csv"
    machines_df.to_csv(machines_path, index=False)
    logger.info(f"Generated {len(machines_df)} machine inventory records at {machines_path}")

    # -------------------------------------------------------------------------
    # 2. CREW INVENTORY
    # -------------------------------------------------------------------------
    crews_list = []
    for i in range(NUM_CREWS):
        dept = rng.choice(DEPARTMENTS, p=[0.45, 0.30, 0.25])
        depot = rng.choice(depot_stations)
        
        shift_h = rng.choice([6, 8, 14, 22])
        shift_start = f"{shift_h:02d}:00:00"
        shift_end = f"{(shift_h + 8) % 24:02d}:00:00"
        headcount = int(rng.integers(4, 12))
        is_avail = bool(rng.random() < 0.88)

        crews_list.append({
            "crew_id": f"CREW_{i+1:04d}",
            "department": dept,
            "home_depot": depot,
            "shift_start": shift_start,
            "shift_end": shift_end,
            "headcount": headcount,
            "is_available": is_avail
        })

    crews_df = pd.DataFrame(crews_list)
    crews_path = RESOURCES_DIR / "crew_inventory.csv"
    crews_df.to_csv(crews_path, index=False)
    logger.info(f"Generated {len(crews_df)} crew inventory records at {crews_path}")

    return machines_df, crews_df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_resources()
