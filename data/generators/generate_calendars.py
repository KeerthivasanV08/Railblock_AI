"""
Operational Calendar Data Generator for RailBlock AI.

Generates:
1. data/raw/calendars/seasonal_calendar.csv
2. data/raw/calendars/festival_traffic_calendar.csv
"""

import logging
from datetime import timedelta
import numpy as np
import pandas as pd

from data.generators.config import (
    RANDOM_SEED,
    CALENDARS_DIR,
    START_DATE,
    END_DATE,
    SIMULATION_DAYS,
)

logger = logging.getLogger(__name__)


def generate_calendars(seed: int = RANDOM_SEED) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generates seasonal operational calendars and festival traffic surge calendars.
    """
    CALENDARS_DIR.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # 1. SEASONAL CALENDAR
    # -------------------------------------------------------------------------
    dates = [START_DATE + timedelta(days=i) for i in range(SIMULATION_DAYS)]
    seasons = []
    risk_factors = []
    penalties = []

    for d in dates:
        m = d.month
        if m in [7, 8, 9]:
            season = "Monsoon"
            risk = 1.45
            penalty = 0.15  # 15% speed restriction / delay penalty
        elif m in [12, 1]:
            season = "Winter-Fog"
            risk = 1.35
            penalty = 0.25  # Heavy fog speed restriction
        elif m in [10, 11]:
            season = "Festival-Peak"
            risk = 1.25
            penalty = 0.10
        elif m in [5, 6]:
            season = "Summer"
            risk = 1.10
            penalty = 0.05
        else:
            season = "Pre-Monsoon"
            risk = 1.00
            penalty = 0.00

        seasons.append(season)
        risk_factors.append(risk)
        penalties.append(penalty)

    seasonal_df = pd.DataFrame({
        "date": [d.isoformat() for d in dates],
        "season": seasons,
        "risk_factor": risk_factors,
        "operational_speed_penalty": penalties
    })

    s_path = CALENDARS_DIR / "seasonal_calendar.csv"
    seasonal_df.to_csv(s_path, index=False)
    logger.info(f"Generated seasonal calendar ({len(seasonal_df)} days) at {s_path}")

    # -------------------------------------------------------------------------
    # 2. FESTIVAL TRAFFIC CALENDAR
    # -------------------------------------------------------------------------
    festivals = [
        {"festival_name": "Holi Peak", "start_date": "2024-03-20", "end_date": "2024-03-28", "traffic_surge_factor": 1.45},
        {"festival_name": "Summer Rush", "start_date": "2024-05-15", "end_date": "2024-06-15", "traffic_surge_factor": 1.25},
        {"festival_name": "Durga Puja / Dussehra", "start_date": "2024-10-05", "end_date": "2024-10-15", "traffic_surge_factor": 1.50},
        {"festival_name": "Diwali & Chhath Puja", "start_date": "2024-10-28", "end_date": "2024-11-10", "traffic_surge_factor": 1.65},
        {"festival_name": "Winter Holidays", "start_date": "2024-12-22", "end_date": "2024-12-31", "traffic_surge_factor": 1.35},
    ]

    festival_df = pd.DataFrame(festivals)
    f_path = CALENDARS_DIR / "festival_traffic_calendar.csv"
    festival_df.to_csv(f_path, index=False)
    logger.info(f"Generated festival traffic calendar at {f_path}")

    return seasonal_df, festival_df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_calendars()
