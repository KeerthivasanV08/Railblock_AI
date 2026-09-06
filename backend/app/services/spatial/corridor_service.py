from typing import List, Dict, Any
from pathlib import Path
import json
import pandas as pd
from app.repositories.network_repository import NetworkRepository
from app.config.settings import settings


class CorridorService:
    def __init__(self, network_repo: NetworkRepository = None):
        self.network_repo = network_repo or NetworkRepository()

    def get_corridor_stations(self) -> List[Dict[str, Any]]:
        df = self.network_repo.get_all_stations()
        return df.to_dict(orient="records")

    def get_corridor_sections(self) -> List[Dict[str, Any]]:
        df = self.network_repo.get_all_sections()
        return df.to_dict(orient="records")

    def get_corridor_geometry(self) -> List[Dict[str, Any]]:
        df = self.network_repo.get_all_geometry()
        return df.to_dict(orient="records")

    def get_corridor_info(self) -> Dict[str, Any]:
        stations_df = self.network_repo.get_all_stations()
        sections_df = self.network_repo.get_all_sections()

        min_lat = float(stations_df["latitude"].min()) if not stations_df.empty else 8.806
        max_lat = float(stations_df["latitude"].max()) if not stations_df.empty else 13.078
        min_lon = float(stations_df["longitude"].min()) if not stations_df.empty else 78.023
        max_lon = float(stations_df["longitude"].max()) if not stations_df.empty else 80.261
        total_len = float(sections_df["end_km"].max()) if not sections_df.empty else 648.23

        return {
            "corridor_name": "Chennai Egmore - Thoothukudi",
            "zone": "Southern Railway (SR)",
            "divisions": ["Chennai (MAS)", "Tiruchchirappalli (TPJ)", "Madurai (MDU)"],
            "start_station": stations_df.iloc[0]["station_code"] if not stations_df.empty else "MS",
            "end_station": stations_df.iloc[-1]["station_code"] if not stations_df.empty else "TN",
            "start_station_name": stations_df.iloc[0]["station_name"] if not stations_df.empty else "Chennai Egmore",
            "end_station_name": stations_df.iloc[-1]["station_name"] if not stations_df.empty else "Tuticorin",
            "total_length_km": round(total_len, 2),
            "num_stations": len(stations_df),
            "num_sections": len(sections_df),
            "bounds": {
                "min_lat": round(min_lat, 4),
                "max_lat": round(max_lat, 4),
                "min_lon": round(min_lon, 4),
                "max_lon": round(max_lon, 4),
            },
        }

    def get_tracks_geojson(self) -> Dict[str, Any]:
        geojson_path = settings.DATA_ROOT / "processed/network/tracks_normalized.geojson"
        if geojson_path.exists():
            with open(geojson_path, encoding="utf-8") as f:
                return json.load(f)

        # Fallback: construct from track_geometry.csv
        geom_df = self.network_repo.get_all_geometry()
        features = []
        for sec_id, group in geom_df.groupby("section_id"):
            coords = []
            for _, row in group.iterrows():
                if not coords:
                    coords.append([row["longitude_start"], row["latitude_start"]])
                coords.append([row["longitude_end"], row["latitude_end"]])
            features.append({
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coords},
                "properties": {"section_id": sec_id},
            })
        return {
            "type": "FeatureCollection",
            "features": features,
        }

