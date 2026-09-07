"""
OSM Section Attribute and Planning Model Builder for RailBlock AI.

Derives RailBlock planning sections with operational attributes (line_type,
num_lines, max_speed_kmph) based on Southern Railway corridor characteristics.
"""

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def build_block_sections(
    section_geometries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Construct the final block sections table with railway operational parameters.
    """
    sections = []
    for sec in section_geometries:
        sec_id = sec["section_id"]
        from_st = sec["from_station"]
        to_st = sec["to_station"]
        start_km = sec["start_km"]
        end_km = sec["end_km"]

        # Southern Railway Mainline operational attributes:
        # MS to TPJ is double-line HDN with 130 km/h MPS.
        # TPJ to MDU is double-line with 110-130 km/h MPS.
        # South of MDU towards TN is 110 km/h MPS.
        if end_km <= 350.0:
            line_type = "HDN"
            num_lines = 2
            max_speed = 130
        elif end_km <= 520.0:
            line_type = "HDN"
            num_lines = 2
            max_speed = 120
        else:
            line_type = "HUN"
            num_lines = 2 if end_km < 600.0 else 1
            max_speed = 110

        sections.append({
            "section_id": sec_id,
            "from_station": from_st,
            "to_station": to_st,
            "start_km": start_km,
            "end_km": end_km,
            "line_type": line_type,
            "num_lines": num_lines,
            "max_speed_kmph": max_speed,
        })

    return sections
