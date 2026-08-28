"""
Preprocessing Configuration for RailBlock AI.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = DATA_DIR / "outputs"
MODELS_DIR = DATA_DIR / "models"

# Spatial and temporal matching thresholds
SPATIAL_PROXIMITY_KM = 2.0  # Max distance for shadow-block candidate clustering
MAX_RESOURCE_DISTANCE_KM = 50.0  # Max distance for machine/crew positioning

# Duration estimation by defect type (in minutes)
DEFECT_DURATION_MAP = {
    "Rail Fracture Risk": 180,
    "Weld Failure": 120,
    "Track Parameter Deviation": 90,
    "Deep Screening Overdue": 240,
    "Ballast Issue": 120,
    "Interlocking Fault": 150,
    "Track Circuit Failure": 60,
    "Axle Counter Error": 45,
    "Cable Fault": 120,
    "Point Machine Issue": 90,
    "Catenary Wear": 120,
    "Neutral Section Fault": 150,
    "Substation Feed Issue": 180,
    "Insulator Damage": 60
}

