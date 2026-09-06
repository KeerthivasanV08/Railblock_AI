"""
Network Model Builder for RailBlock AI.

Combines normalized OSM stations and processed track geometry into production
datasets for RailBlock AI:
- stations.csv
- block_sections.csv
- track_geometry.csv
- ohe_mast_reference.csv
- signal_reference.csv

Writes output to:
- data/processed/network/ (canonical processed OSM network)
- data/raw/network/ (production location read by backend repositories)
"""

import json
import sys
from pathlib import Path
from typing import Any
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.osm.process_stations import get_corridor_stations
from scripts.osm.process_tracks import build_section_geometries, CORRIDOR_TRACKS_FILE
from scripts.osm.build_sections import build_block_sections

PROCESSED_NETWORK_DIR = REPO_ROOT / "data" / "processed" / "network"
RAW_NETWORK_DIR = REPO_ROOT / "data" / "raw" / "network"
BACKUP_DIR = RAW_NETWORK_DIR / "synthetic_backup"


def build_network_tables(verbose: bool = True) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Build all network tables from processed OSM data.
    """
    if verbose:
        print("1. Loading corridor stations and tracks...")
    stations = get_corridor_stations()
    with open(CORRIDOR_TRACKS_FILE, encoding="utf-8") as f:
        corridor_tracks = json.load(f)

    if verbose:
        print("2. Building section track geometries...")
    section_geoms = build_section_geometries(stations, corridor_tracks)

    # 3. Build Stations Table with accurate chainage_km
    if verbose:
        print("3. Generating stations.csv...")
    station_rows = []
    # Station 0 (Chennai Egmore) starts at 0.0 km
    station_rows.append({
        "station_code": stations[0]["station_code"],
        "station_name": stations[0]["station_name"],
        "chainage_km": 0.0,
        "division": stations[0]["division"],
        "latitude": stations[0]["latitude"],
        "longitude": stations[0]["longitude"],
    })

    # Subsequent stations get chainage from section end_km
    for i, sec in enumerate(section_geoms):
        st = stations[i + 1]
        station_rows.append({
            "station_code": st["station_code"],
            "station_name": st["station_name"],
            "chainage_km": sec["end_km"],
            "division": st["division"],
            "latitude": st["latitude"],
            "longitude": st["longitude"],
        })

    stations_df = pd.DataFrame(station_rows)

    # 4. Build Block Sections Table
    if verbose:
        print("4. Generating block_sections.csv...")
    section_rows = build_block_sections(section_geoms)
    sections_df = pd.DataFrame(section_rows)

    # 5. Build Track Geometry Table
    if verbose:
        print("5. Generating track_geometry.csv...")
    geom_rows = []
    seg_counter = 1

    for sec in section_geoms:
        sec_id = sec["section_id"]
        pts = sec["points"]
        s_km = sec["start_km"]
        e_km = sec["end_km"]
        total_len = max(0.001, e_km - s_km)

        # Distribute chainage across sub-segments
        lens = sec.get("seg_lengths", [])
        sum_lens = sum(lens) if lens else total_len

        curr_km = s_km
        for j in range(len(pts) - 1):
            p_start = pts[j]
            p_end = pts[j + 1]
            frac_len = (lens[j] / sum_lens) * total_len if lens else total_len / (len(pts) - 1)
            next_km = round(min(e_km, curr_km + frac_len), 3)

            geom_rows.append({
                "segment_id": f"SEG_{seg_counter:05d}",
                "section_id": sec_id,
                "start_km": round(curr_km, 3),
                "end_km": next_km,
                "latitude_start": round(p_start[0], 6),
                "longitude_start": round(p_start[1], 6),
                "latitude_end": round(p_end[0], 6),
                "longitude_end": round(p_end[1], 6),
            })
            seg_counter += 1
            curr_km = next_km

    geometry_df = pd.DataFrame(geom_rows)

    # 6. Build / Scale Asset References (OHE Masts & Signals)
    # Maintain existing IDs so defect foreign key integrity in TDMS/SMMS remains unbroken,
    # while placing them at physically valid equivalent_km within the real sections.
    if verbose:
        print("6. Updating asset references (masts and signals)...")
    old_masts_path = (
        BACKUP_DIR / "ohe_mast_reference.csv"
        if (BACKUP_DIR / "ohe_mast_reference.csv").exists()
        else RAW_NETWORK_DIR / "ohe_mast_reference.csv"
    )
    old_signals_path = (
        BACKUP_DIR / "signal_reference.csv"
        if (BACKUP_DIR / "signal_reference.csv").exists()
        else RAW_NETWORK_DIR / "signal_reference.csv"
    )

    old_masts = pd.read_csv(old_masts_path)
    old_signals = pd.read_csv(old_signals_path)

    # Build section bounds lookup for new sections
    sec_bounds = {row["section_id"]: (row["start_km"], row["end_km"]) for _, row in sections_df.iterrows()}

    # Scale existing mast locations to new section boundaries
    new_masts = old_masts.copy()
    masts_scaled_km = []
    # Find original synthetic section bounds from old masts
    old_sec_ranges = old_masts.groupby("section_id")["equivalent_km"].agg(["min", "max"]).to_dict("index")

    for _, row in new_masts.iterrows():
        sid = row["section_id"]
        eq_km = row["equivalent_km"]
        if sid in sec_bounds and sid in old_sec_ranges:
            old_min = old_sec_ranges[sid]["min"]
            old_max = old_sec_ranges[sid]["max"]
            new_start, new_end = sec_bounds[sid]
            old_span = max(0.001, old_max - old_min)
            frac = max(0.0, min(1.0, (eq_km - old_min) / old_span))
            new_km = round(new_start + frac * (new_end - new_start), 3)
            masts_scaled_km.append(new_km)
        else:
            masts_scaled_km.append(eq_km)
    new_masts["equivalent_km"] = masts_scaled_km

    # Add masts for newly added sections SEC_050 to SEC_068 (~20 masts per km)
    extra_masts = []
    for sid in [f"SEC_{k:03d}" for k in range(50, len(sections_df) + 1)]:
        if sid in sec_bounds:
            s_km, e_km = sec_bounds[sid]
            mast_count = max(5, int((e_km - s_km) * 20))
            for m_i in range(1, mast_count + 1):
                m_km = round(s_km + (m_i / (mast_count + 1)) * (e_km - s_km), 3)
                extra_masts.append({
                    "mast_number": f"OHE_{sid}_{m_i:04d}",
                    "section_id": sid,
                    "equivalent_km": m_km,
                })
    if extra_masts:
        new_masts = pd.concat([new_masts, pd.DataFrame(extra_masts)], ignore_index=True)

    # Scale existing signals to new section boundaries
    new_signals = old_signals.copy()
    sig_scaled_km = []
    old_sig_ranges = old_signals.groupby("section_id")["equivalent_km"].agg(["min", "max"]).to_dict("index")

    for _, row in new_signals.iterrows():
        sid = row["section_id"]
        eq_km = row["equivalent_km"]
        if sid in sec_bounds and sid in old_sig_ranges:
            old_min = old_sig_ranges[sid]["min"]
            old_max = old_sig_ranges[sid]["max"]
            new_start, new_end = sec_bounds[sid]
            old_span = max(0.001, old_max - old_min)
            frac = max(0.0, min(1.0, (eq_km - old_min) / old_span))
            new_km = round(new_start + frac * (new_end - new_start), 3)
            sig_scaled_km.append(new_km)
        else:
            sig_scaled_km.append(eq_km)
    new_signals["equivalent_km"] = sig_scaled_km

    # Add signals for new sections SEC_050 to SEC_068 (Starter, Distant, Home, Point Machine)
    extra_signals = []
    sig_id_counter = len(old_signals) + 1
    for sid in [f"SEC_{k:03d}" for k in range(50, len(sections_df) + 1)]:
        if sid in sec_bounds:
            s_km, e_km = sec_bounds[sid]
            sig_types = ["Starter", "Distant", "Point Machine", "Home"]
            for s_idx, stype in enumerate(sig_types):
                eq_k = round(s_km + ((s_idx + 1) / 5.0) * (e_km - s_km), 3)
                extra_signals.append({
                    "signal_id": f"SIG_{sid}_{sig_id_counter:04d}",
                    "signal_type": stype,
                    "section_id": sid,
                    "equivalent_km": eq_k,
                })
                sig_id_counter += 1
    if extra_signals:
        new_signals = pd.concat([new_signals, pd.DataFrame(extra_signals)], ignore_index=True)

    return stations_df, sections_df, geometry_df, new_masts, new_signals


def save_network_tables(
    stations_df: pd.DataFrame,
    sections_df: pd.DataFrame,
    geometry_df: pd.DataFrame,
    masts_df: pd.DataFrame,
    signals_df: pd.DataFrame,
    output_dir: Path,
):
    output_dir.mkdir(parents=True, exist_ok=True)
    stations_df.to_csv(output_dir / "stations.csv", index=False)
    sections_df.to_csv(output_dir / "block_sections.csv", index=False)
    geometry_df.to_csv(output_dir / "track_geometry.csv", index=False)
    masts_df.to_csv(output_dir / "ohe_mast_reference.csv", index=False)
    signals_df.to_csv(output_dir / "signal_reference.csv", index=False)


def main():
    print("Building RailBlock AI real-world OSM network tables...")
    stations_df, sections_df, geometry_df, masts_df, signals_df = build_network_tables(verbose=True)

    # Save to data/processed/network/
    save_network_tables(stations_df, sections_df, geometry_df, masts_df, signals_df, PROCESSED_NETWORK_DIR)
    print(f"Saved processed tables to {PROCESSED_NETWORK_DIR}")

    # Save to data/raw/network/ (production location)
    save_network_tables(stations_df, sections_df, geometry_df, masts_df, signals_df, RAW_NETWORK_DIR)
    print(f"Updated production tables in {RAW_NETWORK_DIR}")

    print("\nSummary of Generated Network:")
    print(f"  Stations:       {len(stations_df)} (from {stations_df.iloc[0]['station_code']} to {stations_df.iloc[-1]['station_code']})")
    print(f"  Block Sections: {len(sections_df)} (total length: {sections_df.iloc[-1]['end_km']:.2f} km)")
    print(f"  Track Segments: {len(geometry_df)}")
    print(f"  OHE Masts:      {len(masts_df)}")
    print(f"  Signals:        {len(signals_df)}")


if __name__ == "__main__":
    main()
