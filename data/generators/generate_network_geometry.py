"""
Network Geometry Data Generator for RailBlock AI.

Generates:
1. stations.csv (~50 stations)
2. block_sections.csv (~49 block sections)
3. track_geometry.csv (~500-2000 segments)
4. ohe_mast_reference.csv (~4,000 OHE masts)
5. signal_reference.csv (~1,000+ signals)

All geographic and linear referencing coordinates are internally consistent.
"""

import logging
from pathlib import Path
import numpy as np
import pandas as pd

from data.generators.config import (
    RANDOM_SEED,
    NETWORK_DIR,
    NUM_STATIONS,
    CORRIDOR_LENGTH_KM,
    START_LAT,
    START_LON,
    END_LAT,
    END_LON,
    START_STATION_CODE,
    START_STATION_NAME,
    END_STATION_CODE,
    END_STATION_NAME,
    DIVISION_NAME,
    MASTS_PER_KM,
    SIGNALS_PER_SECTION_MIN,
    SIGNALS_PER_SECTION_MAX,
    SEGMENTS_PER_SECTION_MIN,
    SEGMENTS_PER_SECTION_MAX,
    SIGNAL_TYPES,
    LINE_TYPES,
    NUM_LINES_OPTIONS,
    NUM_LINES_PROBS,
)

logger = logging.getLogger(__name__)


def generate_network_geometry(seed: int = RANDOM_SEED) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Generates network infrastructure files with strict spatial and referential integrity.
    """
    rng = np.random.default_rng(seed)
    NETWORK_DIR.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # 1. STATIONS GENERATION
    # -------------------------------------------------------------------------
    # Key real stations along NDLS - CNB route + realistic synthetic intermediate names
    major_stations = [
        ("NDLS", "New Delhi", 0.0),
        ("ANVT", "Anand Vihar Terminal", 12.5),
        ("GZB", "Ghaziabad Junction", 25.0),
        ("DER", "Dadri", 37.0),
        ("KRJ", "Khurja Junction", 83.0),
        ("ALJN", "Aligarh Junction", 126.0),
        ("HRS", "Hathras Junction", 156.0),
        ("TDL", "Tundla Junction", 205.0),
        ("SKB", "Shikohabad Junction", 222.0),
        ("ETW", "Etawah Junction", 277.0),
        ("PHD", "Phaphund", 333.0),
        ("CNB", "Kanpur Central", 440.0),
    ]

    # For the 200 km demo abstraction, scale chainages linearly into 0.0 to CORRIDOR_LENGTH_KM (200.0)
    # Generate NUM_STATIONS monotonically increasing chainage values
    raw_chainages = np.sort(rng.uniform(1.0, CORRIDOR_LENGTH_KM - 1.0, NUM_STATIONS - 2))
    chainages = np.concatenate([[0.0], raw_chainages, [CORRIDOR_LENGTH_KM]])
    chainages = np.round(chainages, 3)

    # Generate Station Names & Codes
    prefixes = ["Naya", "Purani", "North", "South", "Central", "Junction", "Road", "Khas", "Mandi", "Ganj"]
    base_names = [
        "Ghaziabad", "Dadri", "Dankaur", "Khurja", "Somna", "Aligarh", "Hathras", "Tundla", 
        "Firozabad", "Shikohabad", "Etawah", "Bharthana", "Phaphund", "Jhinjhak", "Rura", 
        "Panki", "Govindpuri", "Sikandrabad", "Koil", "Sasni", "Hirangau", "Kaurara",
        "Kanchausi", "Ambiapur", "Maitha", "Bhaupur", "Khurhand", "Shujatpur", "Manauri"
    ]

    station_names = []
    station_codes = []
    
    # Station 0 & Last Station fixed
    station_names.append(START_STATION_NAME)
    station_codes.append(START_STATION_CODE)

    used_codes = {START_STATION_CODE, END_STATION_CODE}
    used_names = {START_STATION_NAME, END_STATION_NAME}

    for i in range(1, NUM_STATIONS - 1):
        base = rng.choice(base_names)
        suffix = rng.choice(prefixes) if rng.random() > 0.4 else ""
        name = f"{base} {suffix}".strip() if suffix else f"{base} Stn-{i}"
        
        # Ensure unique name
        idx_suffix = 1
        while name in used_names:
            name = f"{base} {suffix} {idx_suffix}".strip()
            idx_suffix += 1
        used_names.add(name)
        station_names.append(name)

        # Generate 3-4 letter code
        clean_name = name.replace(" ", "").upper()
        code = clean_name[:3] if len(clean_name) >= 3 else clean_name.ljust(3, 'X')
        c_idx = 1
        while code in used_codes:
            code = f"{clean_name[:2]}{c_idx}"
            c_idx += 1
        used_codes.add(code)
        station_codes.append(code)

    station_names.append(END_STATION_NAME)
    station_codes.append(END_STATION_CODE)

    # Interpolate Latitude & Longitude with slight realistic jitter
    frac = chainages / CORRIDOR_LENGTH_KM
    lats = START_LAT + frac * (END_LAT - START_LAT) + rng.normal(0, 0.001, NUM_STATIONS)
    lons = START_LON + frac * (END_LON - START_LON) + rng.normal(0, 0.001, NUM_STATIONS)

    stations_df = pd.DataFrame({
        "station_code": station_codes,
        "station_name": station_names,
        "chainage_km": chainages,
        "division": DIVISION_NAME,
        "latitude": np.round(lats, 6),
        "longitude": np.round(lons, 6)
    })

    # Save stations.csv
    stations_path = NETWORK_DIR / "stations.csv"
    stations_df.to_csv(stations_path, index=False)
    logger.info(f"Generated {len(stations_df)} stations at {stations_path}")

    # -------------------------------------------------------------------------
    # 2. BLOCK SECTIONS GENERATION
    # -------------------------------------------------------------------------
    sections_list = []
    for i in range(len(stations_df) - 1):
        st_from = stations_df.iloc[i]
        st_to = stations_df.iloc[i + 1]
        
        sec_id = f"SEC_{i+1:03d}"
        line_type = rng.choice(LINE_TYPES, p=[0.75, 0.20, 0.05])
        num_lines = int(rng.choice(NUM_LINES_OPTIONS, p=NUM_LINES_PROBS))
        max_speed = int(rng.choice([110, 130, 160]))

        sections_list.append({
            "section_id": sec_id,
            "from_station": st_from["station_code"],
            "to_station": st_to["station_code"],
            "start_km": st_from["chainage_km"],
            "end_km": st_to["chainage_km"],
            "line_type": line_type,
            "num_lines": num_lines,
            "max_speed_kmph": max_speed
        })

    sections_df = pd.DataFrame(sections_list)
    sections_path = NETWORK_DIR / "block_sections.csv"
    sections_df.to_csv(sections_path, index=False)
    logger.info(f"Generated {len(sections_df)} block sections at {sections_path}")

    # -------------------------------------------------------------------------
    # 3. TRACK GEOMETRY SEGMENTS GENERATION
    # -------------------------------------------------------------------------
    segments_list = []
    seg_idx = 1

    for idx, sec in sections_df.iterrows():
        sec_id = sec["section_id"]
        s_km = sec["start_km"]
        e_km = sec["end_km"]
        st_from_lat = stations_df.loc[stations_df["station_code"] == sec["from_station"], "latitude"].values[0]
        st_from_lon = stations_df.loc[stations_df["station_code"] == sec["from_station"], "longitude"].values[0]
        st_to_lat = stations_df.loc[stations_df["station_code"] == sec["to_station"], "latitude"].values[0]
        st_to_lon = stations_df.loc[stations_df["station_code"] == sec["to_station"], "longitude"].values[0]

        num_segs = rng.integers(SEGMENTS_PER_SECTION_MIN, SEGMENTS_PER_SECTION_MAX + 1)
        seg_km_points = np.sort(rng.uniform(s_km, e_km, num_segs - 1))
        seg_km_points = np.concatenate([[s_km], seg_km_points, [e_km]])

        for k in range(len(seg_km_points) - 1):
            seg_start = round(seg_km_points[k], 3)
            seg_end = round(seg_km_points[k + 1], 3)
            
            # Linear interpolation for coords
            frac_start = (seg_start - s_km) / (e_km - s_km + 1e-9)
            frac_end = (seg_end - s_km) / (e_km - s_km + 1e-9)

            lat_start = round(st_from_lat + frac_start * (st_to_lat - st_from_lat), 6)
            lon_start = round(st_from_lon + frac_start * (st_to_lon - st_from_lon), 6)
            lat_end = round(st_from_lat + frac_end * (st_to_lat - st_from_lat), 6)
            lon_end = round(st_from_lon + frac_end * (st_to_lon - st_from_lon), 6)

            segments_list.append({
                "segment_id": f"SEG_{seg_idx:05d}",
                "section_id": sec_id,
                "start_km": seg_start,
                "end_km": seg_end,
                "latitude_start": lat_start,
                "longitude_start": lon_start,
                "latitude_end": lat_end,
                "longitude_end": lon_end
            })
            seg_idx += 1

    geometry_df = pd.DataFrame(segments_list)
    geometry_path = NETWORK_DIR / "track_geometry.csv"
    geometry_df.to_csv(geometry_path, index=False)
    logger.info(f"Generated {len(geometry_df)} track geometry segments at {geometry_path}")

    # -------------------------------------------------------------------------
    # 4. OHE MAST REFERENCE GENERATION
    # -------------------------------------------------------------------------
    masts_list = []
    mast_global_count = 1

    for idx, sec in sections_df.iterrows():
        sec_id = sec["section_id"]
        s_km = sec["start_km"]
        e_km = sec["end_km"]
        length_km = e_km - s_km
        num_masts = max(2, int(length_km * MASTS_PER_KM))

        mast_kms = np.linspace(s_km + 0.02, e_km - 0.02, num_masts)
        for m_km in mast_kms:
            masts_list.append({
                "mast_number": f"OHE_{sec_id}_{mast_global_count:04d}",
                "section_id": sec_id,
                "equivalent_km": round(m_km, 3)
            })
            mast_global_count += 1

    masts_df = pd.DataFrame(masts_list)
    masts_path = NETWORK_DIR / "ohe_mast_reference.csv"
    masts_df.to_csv(masts_path, index=False)
    logger.info(f"Generated {len(masts_df)} OHE masts at {masts_path}")

    # -------------------------------------------------------------------------
    # 5. SIGNAL REFERENCE GENERATION
    # -------------------------------------------------------------------------
    signals_list = []
    sig_global_count = 1

    for idx, sec in sections_df.iterrows():
        sec_id = sec["section_id"]
        s_km = sec["start_km"]
        e_km = sec["end_km"]
        num_sigs = rng.integers(SIGNALS_PER_SECTION_MIN, SIGNALS_PER_SECTION_MAX + 1)

        length_km = e_km - s_km
        pad = min(0.05, length_km * 0.05)
        sig_kms = np.sort(rng.uniform(s_km + pad, e_km - pad, num_sigs))
        for sig_km in sig_kms:
            sig_type = rng.choice(SIGNAL_TYPES)
            signals_list.append({
                "signal_id": f"SIG_{sec_id}_{sig_global_count:04d}",
                "signal_type": sig_type,
                "section_id": sec_id,
                "equivalent_km": round(sig_km, 3)
            })
            sig_global_count += 1

    signals_df = pd.DataFrame(signals_list)
    signals_path = NETWORK_DIR / "signal_reference.csv"
    signals_df.to_csv(signals_path, index=False)
    logger.info(f"Generated {len(signals_df)} signal references at {signals_path}")

    return stations_df, sections_df, geometry_df, masts_df, signals_df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_network_geometry()
