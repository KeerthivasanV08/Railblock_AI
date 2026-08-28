"""
Machine allocation and compatibility matching service.
"""

from typing import Dict, Any, List
from app.core.constants import DEFECT_RESOURCE_MAPPING


class MachineMatchingService:
    def match_machine(self, defect_type: str, max_distance_km: float = 50.0) -> Dict[str, Any]:
        required_type = DEFECT_RESOURCE_MAPPING.get(defect_type, "Engineering crew")
        return {
            "defect_type": defect_type,
            "required_resource": required_type,
            "is_machine": "Machine" in required_type or "Wagon" in required_type,
        }
