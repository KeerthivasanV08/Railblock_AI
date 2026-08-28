"""
Input Data Validation Utilities for RailBlock AI.
"""

from typing import Any, List


def validate_required_fields(record: dict, required_fields: List[str]) -> List[str]:
    """Returns list of missing or null required fields in a dictionary record."""
    missing = []
    for field in required_fields:
        if field not in record or record[field] is None or record[field] == "":
            missing.append(field)
    return missing
