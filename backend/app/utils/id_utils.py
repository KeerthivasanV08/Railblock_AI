"""
Identifier Generation Utilities for RailBlock AI.
"""

import uuid


def generate_block_id(section_id: str, index: int) -> str:
    """Generates standardized block recommendation ID."""
    return f"RB-{section_id}-{index:04d}"


def generate_audit_id() -> str:
    """Generates unique audit log record ID."""
    return f"AUDIT_{uuid.uuid4().hex[:10].upper()}"


def generate_reschedule_id() -> str:
    """Generates unique reschedule record ID."""
    return f"RESCHED_{uuid.uuid4().hex[:8].upper()}"
