"""
Core Constants and Domain Enums for RailBlock AI.
"""

from enum import Enum


class Department(str, Enum):
    ENGINEERING = "Engineering"
    ST = "S&T"
    TRD = "TRD"


class SeverityClass(str, Enum):
    A = "A"
    B = "B"
    C = "C"


class TaskStatus(str, Enum):
    OPEN = "Open"
    DEFERRED = "Deferred"
    COMPLETED = "Completed"
    IN_PROGRESS = "In-Progress"


class PriorityBand(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class LocationReferenceType(str, Enum):
    CHAINAGE = "CHAINAGE"
    SIGNAL = "SIGNAL"
    MAST = "MAST"


class TrainType(str, Enum):
    PASSENGER = "Passenger"
    EXPRESS = "Express"
    FREIGHT = "Freight"


class PriorityClass(str, Enum):
    RAJDHANI = "Rajdhani"
    SUPERFAST = "Superfast"
    MAIL_PASSENGER = "Mail Passenger"
    GOODS = "Goods"


class DisruptionType(str, Enum):
    LATE_TRAIN = "Late Train"
    EMERGENCY_DEFECT = "Emergency Defect"
    MACHINE_BREAKDOWN = "Machine Breakdown"


class RejectionReason(str, Enum):
    NONE = "NONE"
    NO_TRAFFIC_GAP = "High Traffic Pressure / No Traffic Gap"
    MACHINE_UNAVAILABLE = "Machine Unavailable"
    CREW_UNAVAILABLE = "Crew Unavailable"
    INSUFFICIENT_WINDOW = "Insufficient Window Duration"
    SPATIAL_MAPPING_FAILURE = "Spatial Mapping Failure"
    WEATHER_HAZARD_EXCLUSION = "Severe Weather Hazard / SRS Threshold Exceeded"
    USER_REJECTED = "User Rejected"


class BlockPlanState(str, Enum):
    PROPOSED = "PROPOSED"
    UNDER_REVIEW = "UNDER_REVIEW"
    MODIFIED = "MODIFIED"
    APPROVED = "APPROVED"
    SCHEDULED = "SCHEDULED"
    IN_EXECUTION = "IN_EXECUTION"
    EXECUTED = "EXECUTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


BLOCK_STATE_TRANSITIONS = {
    BlockPlanState.PROPOSED.value: {
        BlockPlanState.UNDER_REVIEW.value,
        BlockPlanState.MODIFIED.value,
        BlockPlanState.APPROVED.value,
        BlockPlanState.REJECTED.value,
        BlockPlanState.CANCELLED.value,
    },
    BlockPlanState.UNDER_REVIEW.value: {
        BlockPlanState.MODIFIED.value,
        BlockPlanState.APPROVED.value,
        BlockPlanState.REJECTED.value,
        BlockPlanState.CANCELLED.value,
    },
    BlockPlanState.MODIFIED.value: {
        BlockPlanState.MODIFIED.value,
        BlockPlanState.APPROVED.value,
        BlockPlanState.REJECTED.value,
        BlockPlanState.CANCELLED.value,
    },
    BlockPlanState.APPROVED.value: {
        BlockPlanState.SCHEDULED.value,
        BlockPlanState.IN_EXECUTION.value,
        BlockPlanState.EXECUTED.value,
        BlockPlanState.REJECTED.value,
        BlockPlanState.CANCELLED.value,
    },
    BlockPlanState.SCHEDULED.value: {
        BlockPlanState.IN_EXECUTION.value,
        BlockPlanState.EXECUTED.value,
        BlockPlanState.CANCELLED.value,
    },
    BlockPlanState.IN_EXECUTION.value: {
        BlockPlanState.EXECUTED.value,
        BlockPlanState.CANCELLED.value,
    },
    BlockPlanState.REJECTED.value: {
        BlockPlanState.PROPOSED.value,
        BlockPlanState.UNDER_REVIEW.value,
        BlockPlanState.MODIFIED.value,
        BlockPlanState.APPROVED.value,
        BlockPlanState.CANCELLED.value,
    },
}


# Weight Configuration for MDPS Scoring Engine
MDPS_WEIGHTS = {
    "severity_weight": 0.35,
    "overdue_weight": 0.25,
    "traffic_weight": 0.15,
    "criticality_weight": 0.10,
    "deferral_weight": 0.10,
    "historical_weight": 0.05
}

# Defect Resource Compatibility Map
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
