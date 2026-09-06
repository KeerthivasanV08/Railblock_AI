"""
Deterministic Railway Disruption Simulator for RailBlock AI.

Simulates 7 realistic railway operational disruption scenarios across the
Chennai Egmore -> Thoothukudi corridor:
1. PASSENGER_TRAIN_DELAY: Scheduled express/passenger train delayed, conflicting with planned possession.
2. FREIGHT_TRAIN_DELAY: Low-priority freight rake delayed or stalled.
3. EMERGENCY_DEFECT: Critical rail defect (fracture / weld failure) requiring immediate unplanned possession.
4. MACHINE_BREAKDOWN: Track machine (BCM / Tamping) mechanical/hydraulic failure during or prior to block.
5. CREW_UNAVAILABILITY: Specialized gang overrun or missing certifications.
6. WEATHER_HAZARD: Severe localized storm / flood alert exceeding safe operating limits.
7. COMPOUND_DISRUPTION: Multiple simultaneous disruptions (e.g. train delay + emergency defect).
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
import numpy as np
import pandas as pd


class DisruptionScenarioType(str, Enum):
    PASSENGER_TRAIN_DELAY = "PASSENGER_TRAIN_DELAY"
    FREIGHT_TRAIN_DELAY = "FREIGHT_TRAIN_DELAY"
    EMERGENCY_DEFECT = "EMERGENCY_DEFECT"
    MACHINE_BREAKDOWN = "MACHINE_BREAKDOWN"
    CREW_UNAVAILABILITY = "CREW_UNAVAILABILITY"
    WEATHER_HAZARD = "WEATHER_HAZARD"
    COMPOUND_DISRUPTION = "COMPOUND_DISRUPTION"


class DisruptionSimulator:
    """
    Generates reproducible disruption scenarios and applies them to a baseline schedule.
    """

    def __init__(self, random_seed: int = 42):
        self.rng = np.random.RandomState(random_seed)

    def generate_scenario(
        self,
        scenario_type: DisruptionScenarioType,
        section_id: str = "SEC_001",
        base_block_id: Optional[str] = None,
        base_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Creates a deterministic disruption scenario payload.
        """
        if base_time is None:
            base_time = datetime.now(timezone.utc)

        block_id = base_block_id or f"RB-BLK-{self.rng.randint(100, 999)}"
        event_id = f"DISR-{scenario_type.value[:4]}-{uuid.uuid4().hex[:6].upper()}"

        scenario = {
            "event_id": event_id,
            "scenario_type": scenario_type.value,
            "section_id": section_id,
            "affected_block_id": block_id,
            "timestamp": base_time.isoformat(),
            "status": "ACTIVE",
            "metadata": {},
        }

        if scenario_type == DisruptionScenarioType.PASSENGER_TRAIN_DELAY:
            train_no = str(self.rng.choice([12635, 12636, 12637, 16127, 16128]))
            delay_min = int(self.rng.randint(25, 65))
            scenario["metadata"] = {
                "train_number": train_no,
                "train_name": "Vaigai / Pandian / Guruvayur Express",
                "train_category": "Passenger Express",
                "delay_minutes": delay_min,
                "conflict_type": "TIMETABLE_COLLISION",
                "description": f"Train {train_no} delayed by {delay_min} min encroaches into scheduled maintenance possession.",
            }

        elif scenario_type == DisruptionScenarioType.FREIGHT_TRAIN_DELAY:
            rake_id = f"FRT-BOXN-{self.rng.randint(100, 999)}"
            delay_min = int(self.rng.randint(40, 90))
            scenario["metadata"] = {
                "train_number": rake_id,
                "train_name": "BOXN Coal/Fertilizer Rake",
                "train_category": "Freight",
                "delay_minutes": delay_min,
                "conflict_type": "BLOCK_OCCUPATION_OVERRUN",
                "description": f"Freight {rake_id} stalled or delayed by {delay_min} min occupying the block approach.",
            }

        elif scenario_type == DisruptionScenarioType.EMERGENCY_DEFECT:
            scenario["metadata"] = {
                "defect_id": f"EMG-DEF-{self.rng.randint(1000, 9999)}",
                "defect_type": "Rail Fracture (I-Rail Transverse Fissure)",
                "department": "Engineering",
                "severity": "Class A Emergency",
                "urgency_multiplier": 2.5,
                "required_window_min": 90,
                "description": "Urgent rail fracture detected via USFD. Immediate emergency block possession required.",
            }

        elif scenario_type == DisruptionScenarioType.MACHINE_BREAKDOWN:
            machine_id = f"MCH-CSU-{self.rng.randint(10, 99)}"
            scenario["metadata"] = {
                "machine_id": machine_id,
                "machine_type": "Continuous Action Tamper (09-3X)",
                "failure_mode": "Hydraulic tamping unit pump breakdown",
                "estimated_repair_hours": 6.0,
                "description": f"Track machine {machine_id} unavailable due to hydraulic pump failure.",
            }

        elif scenario_type == DisruptionScenarioType.CREW_UNAVAILABILITY:
            gang_id = f"GANG-TRD-{self.rng.randint(1, 9)}"
            scenario["metadata"] = {
                "crew_id": gang_id,
                "department": "TRD",
                "crew_status": "REST_PERIOD_MANDATORY",
                "hours_until_available": 8.0,
                "description": f"Specialized OHE tower wagon crew {gang_id} reached 12-hour continuous duty limit.",
            }

        elif scenario_type == DisruptionScenarioType.WEATHER_HAZARD:
            wind_kmh = float(self.rng.randint(70, 95))
            rain_mm = float(self.rng.randint(45, 80))
            scenario["metadata"] = {
                "weather_event": "IMD Cyclonic Wind & Torrential Rain Warning",
                "wind_speed_kmh": wind_kmh,
                "rainfall_mm": rain_mm,
                "simulated_srs": 82.5,
                "description": f"Severe cyclonic weather (wind {wind_kmh} km/h, rain {rain_mm} mm) exceeding safety gate.",
            }

        elif scenario_type == DisruptionScenarioType.COMPOUND_DISRUPTION:
            scenario["metadata"] = {
                "primary_event": "Express Train Delay (45 min)",
                "secondary_event": "Emergency Weld Defect at Km 142.6",
                "affected_sections": [section_id, f"SEC_{int(section_id.split('_')[-1]) + 1:03d}" if section_id.startswith("SEC_") and int(section_id.split('_')[-1]) < 68 else "SEC_002"],
                "description": "Compound event: Major passenger delay coincides with emergent rail defect.",
            }

        return scenario

    def get_all_benchmark_scenarios(self, base_block_id: str = "RB-BLK-101") -> List[Dict[str, Any]]:
        """Returns a deterministic suite of all 7 disruption scenarios for benchmark evaluations."""
        scenarios = []
        for st in DisruptionScenarioType:
            sc = self.generate_scenario(st, section_id="SEC_001", base_block_id=base_block_id)
            scenarios.append(sc)
        return scenarios


disruption_simulator = DisruptionSimulator()
