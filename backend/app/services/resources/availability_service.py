"""
Resource availability aggregation service.
"""

from typing import Dict, Any
import pandas as pd
from app.repositories.resource_repository import ResourceRepository


class AvailabilityService:
    def __init__(self, repo: ResourceRepository = None):
        self.repo = repo or ResourceRepository()

    def get_summary(self) -> Dict[str, Any]:
        machines = self.repo.get_machines()
        crews = self.repo.get_crews()
        return {
            "total_machines": len(machines),
            "available_machines": int(machines["is_available"].sum()) if "is_available" in machines.columns else 0,
            "total_crews": len(crews),
            "available_crews": int(crews["is_available"].sum()) if "is_available" in crews.columns else 0,
        }
