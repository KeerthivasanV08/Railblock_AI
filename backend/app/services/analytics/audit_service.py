"""
Audit Logging Service for RailBlock AI.

Stores all system events, plan modifications, approvals, rejections, data validation,
and model training actions directly into data/outputs/audit_log.csv.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd

from app.config.settings import settings
from app.repositories.csv_repository import CSVRepository
from app.utils.id_utils import generate_audit_id


class AuditService:
    def __init__(self):
        self.audit_repo = CSVRepository(settings.OUTPUT_DATA_ROOT / "audit_log.csv")

    def log_event(
        self,
        entity: str,
        entity_id: str,
        action: str,
        actor: str = "System",
        old_value: str = "",
        new_value: str = "",
        reason: str = "",
        model_version: str = "1.0.0"
    ) -> dict:
        """Logs an audit record to data/outputs/audit_log.csv."""
        record = {
            "log_id": generate_audit_id(),
            "entity": entity,
            "entity_id": entity_id,
            "action": action,
            "actor": actor,
            "old_value": str(old_value),
            "new_value": str(new_value),
            "reason": str(reason),
            "timestamp": datetime.now().isoformat(),
            "model_version": model_version
        }
        self.audit_repo.append_rows([record])
        return record

    def get_audit_logs(self, page: int = 1, page_size: int = 50) -> dict:
        if not self.audit_repo.file_exists():
            return {"items": [], "page": page, "page_size": page_size, "total": 0, "pages": 0}
        return self.audit_repo.filter_rows({}, page=page, page_size=page_size)
