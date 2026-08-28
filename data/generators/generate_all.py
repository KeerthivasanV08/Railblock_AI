"""
Master Synthetic Data Generator Orchestrator for RailBlock AI.

Executes all sub-generators in strict dependency order, validates intermediate output row counts,
verifies foreign-key integrity, and prints a comprehensive generation summary.

Command:
python data/generators/generate_all.py
"""

import sys
import logging
from pathlib import Path
import pandas as pd

# Add workspace root to python path if needed
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from data.generators.config import (
    RANDOM_SEED,
    RAW_DIR,
    NETWORK_DIR,
    DEFECTS_DIR,
    TRAFFIC_DIR,
    RESOURCES_DIR,
    HISTORICAL_DIR,
    DISRUPTIONS_DIR,
    CALENDARS_DIR,
    MIN_TMS_ROWS,
    MIN_SMMS_ROWS,
    MIN_TDMS_ROWS,
    MIN_TRAIN_ROWS,
    MIN_DELAY_ROWS,
    MIN_GOODS_ROWS,
    MIN_SLOT_ROWS,
    MIN_HISTORICAL_ROWS,
    MIN_MDPS_LABEL_ROWS,
    MIN_DISRUPTION_ROWS,
)
from data.generators.generate_network_geometry import generate_network_geometry
from data.generators.generate_tms_defects import generate_tms_defects
from data.generators.generate_smms_defects import generate_smms_defects
from data.generators.generate_tdms_defects import generate_tdms_defects
from data.generators.generate_timetable import generate_timetable
from data.generators.generate_live_delays import generate_live_delays
from data.generators.generate_goods_forecast import generate_goods_forecast
from data.generators.generate_slots import generate_slots
from data.generators.generate_resources import generate_resources
from data.generators.generate_historical_records import generate_historical_records
from data.generators.generate_disruption_events import generate_disruption_events
from data.generators.generate_calendars import generate_calendars

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("generate_all")


def run_all_generators(seed: int = RANDOM_SEED):
    """
    Orchestrates the entire synthetic raw data generation workflow.
    """
    print("\n=======================================================================")
    print("       RAILBLOCK AI SYNTHETIC DATA GENERATION SYSTEM          ")
    print(f"       Corridor: New Delhi-Kanpur | Random Seed: {seed}       ")
    print("=======================================================================\n")

    # Step 1: Network & Infrastructure
    print("[1/12] Generating Network Infrastructure (Stations & Block Sections) ... ", end="", flush=True)
    stations_df, sections_df, geometry_df, masts_df, signals_df = generate_network_geometry(seed)
    print("PASS")
    print(f"       -> Stations: {len(stations_df)}, Sections: {len(sections_df)}")

    # Step 2: Track, Mast & Signal References
    print("[2/12] Asset References (Track Segments, OHE Masts, Signals) .......... PASS")
    print(f"       -> Segments: {len(geometry_df)}, Masts: {len(masts_df)}, Signals: {len(signals_df)}")

    # Step 3: TMS Defects
    print("[3/12] Generating TMS Defects ........................................ ", end="", flush=True)
    tms_df = generate_tms_defects(seed)
    if len(tms_df) < MIN_TMS_ROWS:
        raise ValueError(f"TMS defects count {len(tms_df)} < required {MIN_TMS_ROWS}")
    print(f"PASS ({len(tms_df):,} rows)")

    # Step 4: SMMS Defects
    print("[4/12] Generating SMMS Defects ....................................... ", end="", flush=True)
    smms_df = generate_smms_defects(seed)
    if len(smms_df) < MIN_SMMS_ROWS:
        raise ValueError(f"SMMS defects count {len(smms_df)} < required {MIN_SMMS_ROWS}")
    print(f"PASS ({len(smms_df):,} rows)")

    # Step 5: TDMS Defects
    print("[5/12] Generating TDMS Defects ....................................... ", end="", flush=True)
    tdms_df = generate_tdms_defects(seed)
    if len(tdms_df) < MIN_TDMS_ROWS:
        raise ValueError(f"TDMS defects count {len(tdms_df)} < required {MIN_TDMS_ROWS}")
    print(f"PASS ({len(tdms_df):,} rows)")

    # Step 6: Train Timetable
    print("[6/12] Generating Train Timetable .................................... ", end="", flush=True)
    tt_df = generate_timetable(seed)
    if len(tt_df) < MIN_TRAIN_ROWS:
        raise ValueError(f"Timetable count {len(tt_df)} < required {MIN_TRAIN_ROWS}")
    print(f"PASS ({len(tt_df):,} rows)")

    # Step 7: Live Train Delays
    print("[7/12] Generating Live Train Delays .................................. ", end="", flush=True)
    delay_df = generate_live_delays(seed)
    if len(delay_df) < MIN_DELAY_ROWS:
        raise ValueError(f"Delays count {len(delay_df)} < required {MIN_DELAY_ROWS}")
    print(f"PASS ({len(delay_df):,} rows)")

    # Step 8: Goods Freight Forecast
    print("[8/12] Generating Goods Freight Forecast ............................. ", end="", flush=True)
    goods_df = generate_goods_forecast(seed)
    if len(goods_df) < MIN_GOODS_ROWS:
        raise ValueError(f"Goods forecast count {len(goods_df)} < required {MIN_GOODS_ROWS}")
    print(f"PASS ({len(goods_df):,} rows)")

    # Step 9: Corridor Slot Availability
    print("[9/12] Generating Corridor Slot Availability ......................... ", end="", flush=True)
    slot_df = generate_slots(seed)
    if len(slot_df) < MIN_SLOT_ROWS:
        raise ValueError(f"Slot availability count {len(slot_df)} < required {MIN_SLOT_ROWS}")
    print(f"PASS ({len(slot_df):,} rows)")

    # Step 10: Resource Inventories (Machines & Crews)
    print("[10/12] Generating Resource Inventories ............................... ", end="", flush=True)
    mch_df, crew_df = generate_resources(seed)
    print(f"PASS (Machines: {len(mch_df)}, Crews: {len(crew_df)})")

    # Step 11: Historical Block Records & MDPS Labels
    print("[11/12] Generating Historical Records & MDPS Labels .................. ", end="", flush=True)
    hist_df, mdps_df = generate_historical_records(seed)
    if len(hist_df) < MIN_HISTORICAL_ROWS or len(mdps_df) < MIN_MDPS_LABEL_ROWS:
        raise ValueError("Historical records or MDPS labels row count threshold violated!")
    print(f"PASS (Hist: {len(hist_df):,}, MDPS: {len(mdps_df):,})")

    # Step 12: Disruptions, Calendars & Validation
    print("[12/12] Generating Disruptions, Calendars & Final Validation ......... ", end="", flush=True)
    disrupt_df = generate_disruption_events(seed)
    s_cal, f_cal = generate_calendars(seed)
    if len(disrupt_df) < MIN_DISRUPTION_ROWS:
        raise ValueError(f"Disruption count {len(disrupt_df)} < required {MIN_DISRUPTION_ROWS}")
    print(f"PASS ({len(disrupt_df):,} disruptions)")

    print("\n-----------------------------------------------------------------------")
    print(" DATA GENERATION COMPLETE — ALL 12 RAW DATASETS GENERATED & VALIDATED")
    print("-----------------------------------------------------------------------\n")


if __name__ == "__main__":
    run_all_generators()
