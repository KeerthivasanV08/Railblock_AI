"""
Notification service package stub for RailBlock AI.

STATUS: NOT CONNECTED / FUTURE INTEGRATION
"""

from typing import Dict, Any


class NotificationService:
    """Stub notification service for alerts and dispatch messages."""
    def send_alert(self, title: str, message: str, recipient: str = None) -> Dict[str, Any]:
        return {"status": "QUEUED_OR_NOT_CONNECTED", "title": title}
