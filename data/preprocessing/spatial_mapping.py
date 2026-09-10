"""
Spatial Translation & Linear Referencing Engine for RailBlock AI.

Translates:
- TMS Chainage (start_km / end_km)
- SMMS Signal IDs (signal_reference equivalent_km)
- TDMS OHE Mast numbers (ohe_mast_reference equivalent_km)

into unified GPS coordinates (latitude, longitude) and mapped chainage km.
Output: spatially_mapped_tasks.csv
"""

import logging
import numpy as np
import pandas as pd

from data.preprocessing.config import RAW_DIR, PROCESSED_DIR

logger = logging.getLogger(__name__)


def map_spatial_locations() -> pd.DataFrame:
    """
    Translates heterogeneous location references into common geospatial coordinates.
    """
    unified_path = PROCESSED_DIR / "unified_maintenance_tasks.csv"
    if not unified_path.exists():
        from data.preprocessing.unify_tasks import unify_maintenance_tasks
        tasks_df = unify_maintenance_tasks()
    else:
        tasks_df = pd.read_csv(unified_path)

    stations_df = pd.read_csv(RAW_DIR / "network/stations.csv")
    sections_df = pd.read_csv(RAW_DIR / "network/block_sections.csv")
    geometry_df = pd.read_csv(RAW_DIR / "network/track_geometry.csv")
    masts_df = pd.read_csv(RAW_DIR / "network/ohe_mast_reference.csv")
    signals_df = pd.read_csv(RAW_DIR / "network/signal_reference.csv")

    # Fast lookup dictionaries
    mast_map = masts_df.set_index("mast_number")["equivalent_km"].to_dict()
    signal_map = signals_df.set_index("signal_id")["equivalent_km"].to_dict()

    # Pre-build section start/end coords lookup from stations
    station_coord = stations_df.set_index("station_code")[["latitude", "longitude", "chainage_km"]].to_dict("index")
    sec_info = {}
    for idx, row in sections_df.iterrows():
        sec_id = row["section_id"]
        from_st = station_coord[row["from_station"]]
        to_st = station_coord[row["to_station"]]
        sec_info[sec_id] = {
            "start_km": row["start_km"],
            "end_km": row["end_km"],
            "lat1": from_st["latitude"],
            "lon1": from_st["longitude"],
            "lat2": to_st["latitude"],
            "lon2": to_st["longitude"],
        }

    mapped_lats = []
    mapped_lons = []
    mapped_kms = []
    methods = []
    confidences = []

    for idx, row in tasks_df.iterrows():
        ref_type = row["location_reference_type"]
        ref_id = row["location_reference_id"]
        sec_id = row["section_id"]

        info = sec_info.get(sec_id)
        if not info:
            mapped_lats.append(np.nan)
            mapped_lons.append(np.nan)
            mapped_kms.append(np.nan)
            methods.append("FAILED")
            confidences.append(0.0)
            continue

        s_km = info["start_km"]
        e_km = info["end_km"]
        length = e_km - s_km + 1e-9

        if ref_type == "CHAINAGE":
            st_k = row["start_km"]
            en_k = row["end_km"]
            m_km = (st_k + en_k) / 2.0 if not np.isnan(st_k) else s_km
            method = "LINEAR_SEGMENT_INTERPOLATION"
            conf = 0.98
        elif ref_type == "SIGNAL":
            m_km = signal_map.get(ref_id, (s_km + e_km) / 2.0)
            method = "SIGNAL_ASSET_REFERENCE"
            conf = 0.95
        elif ref_type == "MAST":
            m_km = mast_map.get(ref_id, (s_km + e_km) / 2.0)
            method = "OHE_MAST_REFERENCE"
            conf = 0.95
        else:
            m_km = (s_km + e_km) / 2.0
            method = "SECTION_MIDPOINT_FALLBACK"
            conf = 0.70

        # Calculate GPS coordinate along section vector
        frac = max(0.0, min(1.0, (m_km - s_km) / length))
        lat = round(info["lat1"] + frac * (info["lat2"] - info["lat1"]), 6)
        lon = round(info["lon1"] + frac * (info["lon2"] - info["lon1"]), 6)

        mapped_lats.append(lat)
        mapped_lons.append(lon)
        mapped_kms.append(round(m_km, 3))
        methods.append(method)
        confidences.append(conf)

    mapped_df = tasks_df.copy()
    mapped_df["gps_latitude"] = mapped_lats
    mapped_df["gps_longitude"] = mapped_lons
    mapped_df["mapped_chainage_km"] = mapped_kms
    mapped_df["spatial_mapping_method"] = methods
    mapped_df["spatial_mapping_confidence"] = confidences

    # Enrich with weather features so downstream MDPS scoring consumes live SRS
    try:
        from data.preprocessing.feature_engineering import enrich_tasks_with_weather
        mapped_df = enrich_tasks_with_weather(mapped_df)
    except Exception as exc:
        logger.warning(f"Could not enrich weather features in spatial_mapping: {exc}")

    out_path = PROCESSED_DIR / "spatially_mapped_tasks.csv"
    mapped_df.to_csv(out_path, index=False)
    logger.info(f"Generated {len(mapped_df)} spatially mapped tasks at {out_path}")

    return mapped_df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    map_spatial_locations()

