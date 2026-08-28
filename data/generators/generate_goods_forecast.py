"""
Goods Traffic Forecast Generator for RailBlock AI.

Generates data/raw/traffic/goods_forecast.csv (>= 30,000 rows).
"""

import logging
from datetime import timedelta
import numpy as np
import pandas as pd

from data.generators.config import (
    RANDOM_SEED,
    TRAFFIC_DIR,
    NETWORK_DIR,
    MIN_GOODS_ROWS,
    START_DATE,
    SIMULATION_DAYS,
    COMMODITY_TYPES,
)

logger = logging.getLogger(__name__)


def generate_goods_forecast(seed: int = RANDOM_SEED) -> pd.DataFrame:
    """
    Generates section-level commodity freight forecast records incorporating seasonal variation.
    """
    rng = np.random.default_rng(seed)
    TRAFFIC_DIR.mkdir(parents=True, exist_ok=True)

    sections_path = NETWORK_DIR / "block_sections.csv"
    if not sections_path.exists():
        raise FileNotFoundError(f"Missing required reference file: {sections_path}")
    sections_df = pd.read_csv(sections_path)
    section_ids = sections_df["section_id"].values

    sec_indices = rng.integers(0, len(section_ids), MIN_GOODS_ROWS)
    selected_sections = section_ids[sec_indices]

    day_offsets = rng.integers(0, SIMULATION_DAYS, MIN_GOODS_ROWS)
    forecast_dates = [START_DATE + timedelta(days=int(d)) for d in day_offsets]

    commodities = rng.choice(COMMODITY_TYPES, size=MIN_GOODS_ROWS)

    # Calculate seasonal factor based on month (e.g. monsoon low, winter peak, harvest season foodgrains)
    seasonal_factors = []
    expected_rakes_list = []

    for i in range(MIN_GOODS_ROWS):
        f_date = forecast_dates[i]
        comm = commodities[i]
        month = f_date.month

        # Seasonal multiplier
        if month in [6, 7, 8]:  # Monsoon
            sf = round(rng.uniform(0.70, 0.90), 2)
        elif month in [10, 11]:  # Festival / Post-monsoon peak
            sf = round(rng.uniform(1.15, 1.40), 2)
        elif month in [3, 4] and comm == "Foodgrain":  # Rabi harvest
            sf = round(rng.uniform(1.30, 1.50), 2)
        elif month in [12, 1, 2]:  # Winter industrial surge
            sf = round(rng.uniform(1.05, 1.25), 2)
        else:
            sf = round(rng.uniform(0.95, 1.10), 2)

        base_rakes = rng.integers(2, 15)
        expected_rakes = max(1, int(round(base_rakes * sf)))

        seasonal_factors.append(sf)
        expected_rakes_list.append(expected_rakes)

    df = pd.DataFrame({
        "section_id": selected_sections,
        "forecast_date": [d.isoformat() for d in forecast_dates],
        "expected_rakes": expected_rakes_list,
        "commodity_type": commodities,
        "seasonal_factor": seasonal_factors
    })

    out_path = TRAFFIC_DIR / "goods_forecast.csv"
    df.to_csv(out_path, index=False)
    logger.info(f"Generated {len(df)} goods forecast records at {out_path}")
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_goods_forecast()
