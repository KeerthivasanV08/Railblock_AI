"""
Universal Geo-Spatial Linear Referencing Coordinate Mapper for RailBlock AI.

Translates departmental location references (TMS Chainage, SMMS Signal IDs, TDMS OHE Masts)
into unified WGS84 GPS latitude/longitude coordinates and mapped chainage km.
"""

import numpy as np
import pandas as pd
from app.repositories.network_repository import NetworkRepository


class LinearReferenceEngine:
    def __init__(self, network_repo: NetworkRepository = None):
        self.network_repo = network_repo or NetworkRepository()

    def translate_task_locations(self, tasks_df: pd.DataFrame) -> pd.DataFrame:
        """
        Translates task location reference types (CHAINAGE, SIGNAL, MAST) into WGS84 GPS coordinates.
        """
        stations_df = self.network_repo.get_all_stations()
        sections_df = self.network_repo.get_all_sections()
        geometry_df = self.network_repo.get_all_geometry()
        masts_df = self.network_repo.masts_repo.read_csv()
        signals_df = self.network_repo.signals_repo.read_csv()

        mast_map = masts_df.set_index("mast_number")["equivalent_km"].to_dict()
        signal_map = signals_df.set_index("signal_id")["equivalent_km"].to_dict()

        station_coords = stations_df.set_index("station_code")[["latitude", "longitude", "chainage_km"]].to_dict("index")
        sec_info = {}
        for idx, row in sections_df.iterrows():
            from_st = station_coords.get(row["from_station"], {})
            to_st = station_coords.get(row["to_station"], {})
            sec_info[row["section_id"]] = {
                "start_km": row["start_km"],
                "end_km": row["end_km"],
                "lat1": from_st.get("latitude", 13.077749),
                "lon1": from_st.get("longitude", 80.261257),
                "lat2": to_st.get("latitude", 8.805996),
                "lon2": to_st.get("longitude", 78.155349),
            }

        # Index track geometry segments by section_id
        sec_segments = {}
        if not geometry_df.empty:
            for sec_id, group in geometry_df.groupby("section_id"):
                sec_segments[sec_id] = group.sort_values("start_km").to_dict(orient="records")

        lats, lons, kms, methods, confidences, statuses, errors = [], [], [], [], [], [], []

        for idx, row in tasks_df.iterrows():
            ref_type = row.get("location_reference_type", "CHAINAGE")
            ref_id = row.get("location_reference_id", "")
            sec_id = row.get("section_id", "")

            info = sec_info.get(sec_id, {"start_km": 0.0, "end_km": 10.0, "lat1": 13.077749, "lon1": 80.261257, "lat2": 8.805996, "lon2": 78.155349})
            s_km, e_km = info["start_km"], info["end_km"]
            length = max(0.001, e_km - s_km)

            status = "HIGH_CONFIDENCE"
            error_estimate = 0.0

            if sec_id not in sec_info:
                status = "LOW_CONFIDENCE"
                error_estimate = length / 2.0

            if ref_type == "CHAINAGE":
                st_k = row.get("start_km")
                en_k = row.get("end_km")
                if pd.isna(st_k) or pd.isna(en_k):
                    m_km = (s_km + e_km) / 2.0
                    status = "LOW_CONFIDENCE"
                    error_estimate = length / 2.0
                else:
                    m_km = (float(st_k) + float(en_k)) / 2.0
                    if m_km < s_km or m_km > e_km:
                        status = "LOW_CONFIDENCE"
                        error_estimate = min(abs(m_km - s_km), abs(m_km - e_km))
                method = "LINEAR_SEGMENT_INTERPOLATION"
                conf = 0.98
            elif ref_type == "SIGNAL":
                if ref_id in signal_map:
                    m_km = signal_map[ref_id]
                else:
                    m_km = (s_km + e_km) / 2.0
                    status = "LOW_CONFIDENCE"
                    error_estimate = length / 2.0
                method = "SIGNAL_ASSET_REFERENCE"
                conf = 0.95 if status == "HIGH_CONFIDENCE" else 0.55
            elif ref_type == "MAST":
                if ref_id in mast_map:
                    m_km = mast_map[ref_id]
                else:
                    m_km = (s_km + e_km) / 2.0
                    status = "LOW_CONFIDENCE"
                    error_estimate = length / 2.0
                method = "OHE_MAST_REFERENCE"
                conf = 0.95 if status == "HIGH_CONFIDENCE" else 0.55
            else:
                m_km = (s_km + e_km) / 2.0
                method = "SECTION_MIDPOINT_FALLBACK"
                conf = 0.50
                status = "UNMAPPED"
                error_estimate = length / 2.0

            # Interpolate along curved geometry segments if available
            segments = sec_segments.get(sec_id, [])
            matched_seg = None
            for seg in segments:
                if seg["start_km"] <= m_km <= seg["end_km"]:
                    matched_seg = seg
                    break

            if matched_seg is not None:
                seg_len = max(0.0001, matched_seg["end_km"] - matched_seg["start_km"])
                seg_frac = max(0.0, min(1.0, (m_km - matched_seg["start_km"]) / seg_len))
                lat = round(matched_seg["latitude_start"] + seg_frac * (matched_seg["latitude_end"] - matched_seg["latitude_start"]), 6)
                lon = round(matched_seg["longitude_start"] + seg_frac * (matched_seg["longitude_end"] - matched_seg["longitude_start"]), 6)
            else:
                frac = max(0.0, min(1.0, (m_km - s_km) / length))
                lat = round(info["lat1"] + frac * (info["lat2"] - info["lat1"]), 6)
                lon = round(info["lon1"] + frac * (info["lon2"] - info["lon1"]), 6)

            lats.append(lat)
            lons.append(lon)
            kms.append(round(m_km, 3))
            methods.append(method)
            confidences.append(conf)
            statuses.append(status)
            errors.append(round(float(error_estimate), 3))

        mapped_df = tasks_df.copy()
        mapped_df["gps_latitude"] = lats
        mapped_df["gps_longitude"] = lons
        mapped_df["mapped_chainage_km"] = kms
        mapped_df["spatial_mapping_method"] = methods
        mapped_df["spatial_mapping_confidence"] = confidences
        mapped_df["spatial_mapping_status"] = statuses
        mapped_df["spatial_error_estimate_km"] = errors

        return mapped_df
