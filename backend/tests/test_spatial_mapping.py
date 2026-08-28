"""
Tests for Spatial Mapping and Linear Referencing Engine.
"""

import pytest
import pandas as pd
from data.preprocessing.config import PROCESSED_DIR


def test_spatial_mapping_coordinates():
    mapped = pd.read_csv(PROCESSED_DIR / "spatially_mapped_tasks.csv")
    
    assert "gps_latitude" in mapped.columns
    assert "gps_longitude" in mapped.columns
    assert "mapped_chainage_km" in mapped.columns

    # Verify latitude/longitude bounds for New Delhi - Kanpur corridor (~26 to ~29 N lat, ~77 to ~81 E lon)
    valid_lats = mapped["gps_latitude"].between(26.0, 29.5)
    valid_lons = mapped["gps_longitude"].between(76.5, 81.0)
    assert valid_lats.all()
    assert valid_lons.all()


def test_location_reference_types():
    mapped = pd.read_csv(PROCESSED_DIR / "spatially_mapped_tasks.csv")
    types = set(mapped["location_reference_type"].unique())
    assert set(["CHAINAGE", "SIGNAL", "MAST"]).issubset(types)

