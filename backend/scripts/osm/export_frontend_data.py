"""
Export Real-World OSM Network Data to Frontend TypeScript Modules.

Generates:
- frontend/src/data/stations.ts
- frontend/src/data/sections.ts
"""

from pathlib import Path
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
STATIONS_CSV = REPO_ROOT / "data" / "raw" / "network" / "stations.csv"
SECTIONS_CSV = REPO_ROOT / "data" / "raw" / "network" / "block_sections.csv"
FRONTEND_DATA_DIR = REPO_ROOT / "frontend" / "src" / "data"

MAJOR_STATION_CODES = {
    "MS", "MBM", "GDY", "TBM", "CGL", "MMK", "MLMR", "TMV",
    "VM", "VRI", "ALU", "LLI", "SRGM", "TPJ", "MPA", "VDM",
    "MDU", "APK", "TIP", "MVN", "TN",
}


def export_stations_ts():
    df = pd.read_csv(STATIONS_CSV)
    rows = []
    for _, r in df.iterrows():
        c = r["station_code"]
        n = r["station_name"]
        k = round(float(r["chainage_km"]), 1)
        la = round(float(r["latitude"]), 4)
        lo = round(float(r["longitude"]), 4)
        m = "true" if c in MAJOR_STATION_CODES else "false"
        rows.append(f'  {{ station_code: "{c}", name: "{n}", km: {k}, lat: {la}, lng: {lo}, major: {m} }},')

    content = f"""import type {{ Station }} from "@/types";

/** Real-world Chennai Egmore – Thoothukudi corridor derived from OpenStreetMap ({len(df)} stations). */
export const STATIONS: Station[] = [
""" + "\n".join(rows) + f"""
];

export const stationByCode = (code: string) => STATIONS.find((s) => s.station_code === code);

export const CORRIDOR_START_KM = STATIONS[0].km;
export const CORRIDOR_END_KM = STATIONS[STATIONS.length - 1].km;

/** Interpolate a lat/lng along the corridor for an arbitrary chainage. */
export function kmToLatLng(km: number): {{ lat: number; lng: number }} {{
  const clamped = Math.min(Math.max(km, CORRIDOR_START_KM), CORRIDOR_END_KM);
  for (let i = 0; i < STATIONS.length - 1; i++) {{
    const a = STATIONS[i];
    const b = STATIONS[i + 1];
    if (clamped >= a.km && clamped <= b.km) {{
      const t = (clamped - a.km) / (b.km - a.km || 1);
      return {{ lat: a.lat + (b.lat - a.lat) * t, lng: a.lng + (b.lng - a.lng) * t }};
    }}
  }}
  const last = STATIONS[STATIONS.length - 1];
  return {{ lat: last.lat, lng: last.lng }};
}}

export function kmToStationLabel(km: number): string {{
  let nearest = STATIONS[0];
  for (const s of STATIONS) if (Math.abs(s.km - km) < Math.abs(nearest.km - km)) nearest = s;
  return nearest.station_code;
}}
"""
    out_path = FRONTEND_DATA_DIR / "stations.ts"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved {len(df)} stations to {out_path}")


def export_sections_ts():
    df = pd.read_csv(SECTIONS_CSV)
    rows = []
    for _, r in df.iterrows():
        sec_id = r["section_id"]
        from_st = r["from_station"]
        to_st = r["to_station"]
        from_km = round(float(r["start_km"]), 1)
        to_km = round(float(r["end_km"]), 1)
        double_line = "true" if int(r.get("num_lines", 2)) >= 2 else "false"
        # realistic traffic density between 65 and 95
        traffic_density = 90 if from_km < 350 else 75
        rows.append(
            f'  {{\n'
            f'    section_id: "{sec_id}",\n'
            f'    from_station: "{from_st}",\n'
            f'    to_station: "{to_st}",\n'
            f'    from_km: {from_km},\n'
            f'    to_km: {to_km},\n'
            f'    traffic_density: {traffic_density},\n'
            f'    double_line: {double_line},\n'
            f'  }},'
        )

    content = f"""import type {{ BlockSection }} from "@/types";

/** Real-world Chennai Egmore – Thoothukudi block sections ({len(df)} sections). */
export const SECTIONS: BlockSection[] = [
""" + "\n".join(rows) + f"""
];

export const sectionById = (id: string) => SECTIONS.find((s) => s.section_id === id);

export function sectionForKm(km: number): BlockSection {{
  return SECTIONS.find((s) => km >= s.from_km && km <= s.to_km) ?? SECTIONS[SECTIONS.length - 1];
}}
"""
    out_path = FRONTEND_DATA_DIR / "sections.ts"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved {len(df)} sections to {out_path}")


if __name__ == "__main__":
    export_stations_ts()
    export_sections_ts()
