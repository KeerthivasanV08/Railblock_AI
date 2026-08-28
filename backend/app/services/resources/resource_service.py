"""
Live Resource Inventory & Monitoring Service for RailBlock AI.
"""

from typing import Dict, Any
from app.repositories.resource_repository import ResourceRepository


class ResourceService:
    def __init__(self):
        self.repo = ResourceRepository()

    def get_live_resources(self) -> Dict[str, Any]:
        mch_df = self.repo.get_machines()
        crew_df = self.repo.get_crews()

        avail_mch = int(mch_df["is_available"].sum()) if "is_available" in mch_df.columns else 0
        avail_crew = int(crew_df["is_available"].sum()) if "is_available" in crew_df.columns else 0

        return {
            "machines": mch_df.to_dict("records"),
            "crews": crew_df.to_dict("records"),
            "available_machine_count": avail_mch,
            "available_crew_count": avail_crew,
            "total_machines": len(mch_df),
            "total_crews": len(crew_df)
        }
