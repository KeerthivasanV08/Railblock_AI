"""
Corridor query and topology management service.
"""

from typing import List, Dict, Any
from app.repositories.network_repository import NetworkRepository


class CorridorService:
    def __init__(self, network_repo: NetworkRepository = None):
        self.network_repo = network_repo or NetworkRepository()

    def get_corridor_sections(self) -> List[Dict[str, Any]]:
        df = self.network_repo.get_all_sections()
        return df.to_dict(orient="records")
