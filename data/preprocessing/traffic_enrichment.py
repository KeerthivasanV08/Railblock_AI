"""
Traffic Enrichment Module for RailBlock AI.

Aggregates timetable, live delays, and goods forecast to generate
section-level traffic density, delay statistics, and traffic pressure scores.
Output: enriched_train_traffic.csv
"""

import logging
import numpy as np
import pandas as pd

from data.preprocessing.config import RAW_DIR, PROCESSED_DIR

logger = logging.getLogger(__name__)


def enrich_traffic_data() -> pd.DataFrame:
    """
    Computes traffic density, passenger/freight train split, average delay,
    and traffic pressure score per section.
    """
    tt_df = pd.read_csv(RAW_DIR / "traffic/train_timetable.csv")
    delay_df = pd.read_csv(RAW_DIR / "traffic/live_train_delays.csv")
    goods_df = pd.read_csv(RAW_DIR / "traffic/goods_forecast.csv")
    sections_df = pd.read_csv(RAW_DIR / "network/block_sections.csv")

    # Aggregate timetable by section
    tt_summary = tt_df.groupby("section_id").agg(
        train_count=("train_number", "count"),
        passenger_train_count=("train_type", lambda x: (x == "Passenger").sum() + (x == "Express").sum()),
        freight_train_count=("train_type", lambda x: (x == "Freight").sum())
    ).reset_index()

    # Aggregate delay metrics
    avg_delay_global = delay_df["delay_minutes"].mean()
    max_delay_global = delay_df["delay_minutes"].max()

    # Aggregate freight rakes forecast by section
    goods_summary = goods_df.groupby("section_id").agg(
        freight_demand=("expected_rakes", "sum")
    ).reset_index()

    # Merge onto all block sections
    traffic_df = sections_df[["section_id"]].merge(tt_summary, on="section_id", how="left").fillna(0)
    traffic_df = traffic_df.merge(goods_summary, on="section_id", how="left").fillna(0)

    max_tc = traffic_df["train_count"].max() if traffic_df["train_count"].max() > 0 else 1.0
    traffic_df["traffic_density"] = np.round(traffic_df["train_count"] / max_tc, 3)

    # Derive delay statistics & peak hour flags
    traffic_df["average_delay"] = np.round(avg_delay_global, 1)
    traffic_df["max_delay"] = np.round(max_delay_global, 1)
    traffic_df["peak_hour_flag"] = (traffic_df["traffic_density"] > 0.6).astype(int)

    # Calculate overall traffic_pressure_score (0 - 100)
    traffic_df["traffic_pressure_score"] = np.round(
        (traffic_df["traffic_density"] * 50.0) +
        (np.clip(traffic_df["freight_demand"] / 100.0, 0, 1) * 30.0) +
        (traffic_df["peak_hour_flag"] * 20.0),
        2
    )

    out_path = PROCESSED_DIR / "enriched_train_traffic.csv"
    traffic_df.to_csv(out_path, index=False)
    logger.info(f"Generated traffic enrichment data ({len(traffic_df)} sections) at {out_path}")

    return traffic_df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    enrich_traffic_data()

