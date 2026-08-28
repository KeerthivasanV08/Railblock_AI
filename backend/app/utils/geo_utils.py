"""
Geospatial Calculation Helper Utilities for RailBlock AI.
"""

import numpy as np


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates approximate geographic distance in km using spherical approximation."""
    if np.isnan(lat1) or np.isnan(lon1) or np.isnan(lat2) or np.isnan(lon2):
        return 999.0

    d_lat = (lat2 - lat1) * 111.0
    d_lon = (lon2 - lon1) * 111.0 * np.cos(np.radians((lat1 + lat2) / 2.0))
    return round(float(np.sqrt(d_lat ** 2 + d_lon ** 2)), 2)
