"""
Date and Time Helper Utilities for RailBlock AI.
"""

from datetime import datetime, date


def parse_datetime(dt_str: str) -> datetime:
    """Parses ISO or standard datetime strings."""
    if not dt_str or not isinstance(dt_str, str):
        return datetime.now()
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%H:%M:%S"):
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                pass
        return datetime.now()


def calculate_overdue_days(target_completion_date_str: str, planning_date: date = None) -> int:
    """Calculates non-negative overdue days relative to target completion date."""
    if planning_date is None:
        planning_date = date.today()
    target_dt = parse_datetime(target_completion_date_str).date()
    diff = (planning_date - target_dt).days
    return max(0, diff)
