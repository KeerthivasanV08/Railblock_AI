"""
Global Configuration for RailBlock AI Synthetic Data Generation.

Contains all constants, thresholds, file paths, parameters, distributions,
and random seed settings for deterministic and reproducible generation.
"""

from pathlib import Path
from datetime import datetime, date

# -----------------------------------------------------------------------------
# GLOBAL REPRODUCIBILITY & PATHS
# -----------------------------------------------------------------------------
RANDOM_SEED = 42

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = DATA_DIR / "outputs"
MODELS_DIR = DATA_DIR / "models"

# Raw Data Directory Sub-paths
NETWORK_DIR = RAW_DIR / "network"
DEFECTS_DIR = RAW_DIR / "defects"
TRAFFIC_DIR = RAW_DIR / "traffic"
RESOURCES_DIR = RAW_DIR / "resources"
HISTORICAL_DIR = RAW_DIR / "historical"
DISRUPTIONS_DIR = RAW_DIR / "disruptions"
CALENDARS_DIR = RAW_DIR / "calendars"

# -----------------------------------------------------------------------------
# CORRIDOR & GEOMETRY SETTINGS
# -----------------------------------------------------------------------------
CORRIDOR_NAME = "Chennai Egmore-Thoothukudi"
CORRIDOR_LENGTH_KM = 648.23

NUM_STATIONS = 69
NUM_BLOCK_SECTIONS = 68  # Connected linearly between consecutive stations

# Geography anchor points (Approximate coordinates)
START_STATION_NAME = "Chennai Egmore"
START_STATION_CODE = "MS"
START_LAT = 13.0777
START_LON = 80.2613

END_STATION_NAME = "Tuticorin"
END_STATION_CODE = "TN"
END_LAT = 8.8060
END_LON = 78.1553

DIVISION_NAME = "Southern Railway (SR)"

# Reference Asset Densities
MASTS_PER_KM = 20  # ~50 meters apart
SIGNALS_PER_SECTION_MIN = 2
SIGNALS_PER_SECTION_MAX = 5
SEGMENTS_PER_SECTION_MIN = 2
SEGMENTS_PER_SECTION_MAX = 5

# -----------------------------------------------------------------------------
# DATASET VOLUME TARGETS (MINIMUM REQUIRED ROWS)
# -----------------------------------------------------------------------------
MIN_TMS_ROWS = 30000
MIN_SMMS_ROWS = 25000
MIN_TDMS_ROWS = 25000

MIN_TRAIN_ROWS = 50000
MIN_DELAY_ROWS = 50000
MIN_GOODS_ROWS = 30000
MIN_SLOT_ROWS = 50000

MIN_HISTORICAL_ROWS = 50000
MIN_MDPS_LABEL_ROWS = 30000
MIN_DISRUPTION_ROWS = 25000

# Small Reference Counts
NUM_MACHINES = 120
NUM_CREWS = 200

# -----------------------------------------------------------------------------
# TEMPORAL SIMULATION WINDOW
# -----------------------------------------------------------------------------
START_DATE = date(2024, 1, 1)
END_DATE = date(2024, 12, 31)
SIMULATION_DAYS = (END_DATE - START_DATE).days + 1

# -----------------------------------------------------------------------------
# SEVERITY & DEFECT CONFIGURATIONS
# -----------------------------------------------------------------------------
SEVERITY_WEIGHTS = {
    "A": 0.20,  # High criticality
    "B": 0.50,  # Medium criticality
    "C": 0.30   # Lower criticality
}

TMS_DEFECT_TYPES = [
    "Rail Fracture Risk",
    "Weld Failure",
    "Track Parameter Deviation",
    "Deep Screening Overdue",
    "Ballast Issue"
]

SMMS_DEFECT_TYPES = [
    "Interlocking Fault",
    "Track Circuit Failure",
    "Axle Counter Error",
    "Cable Fault",
    "Point Machine Issue"
]

TDMS_DEFECT_TYPES = [
    "Catenary Wear",
    "Neutral Section Fault",
    "Substation Feed Issue",
    "Insulator Damage"
]

# Defect to Severity class probabilities
DEFECT_SEVERITY_PROBS = {
    # TMS
    "Rail Fracture Risk": {"A": 0.70, "B": 0.25, "C": 0.05},
    "Weld Failure": {"A": 0.50, "B": 0.40, "C": 0.10},
    "Track Parameter Deviation": {"A": 0.20, "B": 0.50, "C": 0.30},
    "Deep Screening Overdue": {"A": 0.10, "B": 0.60, "C": 0.30},
    "Ballast Issue": {"A": 0.05, "B": 0.45, "C": 0.50},
    # SMMS
    "Interlocking Fault": {"A": 0.65, "B": 0.30, "C": 0.05},
    "Track Circuit Failure": {"A": 0.40, "B": 0.50, "C": 0.10},
    "Axle Counter Error": {"A": 0.35, "B": 0.50, "C": 0.15},
    "Cable Fault": {"A": 0.30, "B": 0.50, "C": 0.20},
    "Point Machine Issue": {"A": 0.25, "B": 0.55, "C": 0.20},
    # TDMS
    "Catenary Wear": {"A": 0.40, "B": 0.50, "C": 0.10},
    "Neutral Section Fault": {"A": 0.60, "B": 0.30, "C": 0.10},
    "Substation Feed Issue": {"A": 0.70, "B": 0.25, "C": 0.05},
    "Insulator Damage": {"A": 0.20, "B": 0.50, "C": 0.30}
}

# Mapping defect types to required resource types
DEFECT_RESOURCE_MAPPING = {
    "Rail Fracture Risk": "Engineering crew",
    "Weld Failure": "Engineering crew",
    "Track Parameter Deviation": "Tamping Machine",
    "Deep Screening Overdue": "Ballast Cleaning Machine",
    "Ballast Issue": "Ballast Cleaning Machine",
    "Interlocking Fault": "S&T crew",
    "Track Circuit Failure": "S&T crew",
    "Axle Counter Error": "S&T crew",
    "Cable Fault": "S&T crew",
    "Point Machine Issue": "S&T crew",
    "Catenary Wear": "Tower Wagon",
    "Neutral Section Fault": "Tower Wagon",
    "Substation Feed Issue": "TRD crew",
    "Insulator Damage": "Tower Wagon"
}

# -----------------------------------------------------------------------------
# TRAFFIC & OPERATIONAL CONFIGURATIONS
# -----------------------------------------------------------------------------
TRAIN_TYPES = ["Passenger", "Express", "Freight"]
PRIORITY_CLASSES = ["Rajdhani", "Superfast", "Mail Passenger", "Goods"]

SIGNAL_TYPES = ["Home", "Distant", "Starter", "Point Machine", "Axle Counter"]
LINE_TYPES = ["HDN", "HUN", "Branch"]
NUM_LINES_OPTIONS = [1, 2, 3, 4]
NUM_LINES_PROBS = [0.05, 0.70, 0.15, 0.10]  # Double line dominant corridor

COMMODITY_TYPES = ["Coal", "Steel", "Foodgrain", "Cement", "Other"]
DELAY_REASONS = ["Congestion", "Technical", "Weather", "Other"]
DISRUPTION_TYPES = ["Late Train", "Emergency Defect", "Machine Breakdown"]
DEPARTMENTS = ["Engineering", "S&T", "TRD"]

SLOT_WINDOW_MINUTES = [15, 30, 60, 90, 120, 180]

# -----------------------------------------------------------------------------
# SPATIAL & CLUSTERING TOLERANCES
# -----------------------------------------------------------------------------
SPATIAL_CLUSTER_TOLERANCE_KM = 2.0  # Proximity for shadow-block candidate clustering
RESOURCE_MAX_FEASIBLE_DISTANCE_KM = 50.0
