"""
OSM Station Normalization and Extraction for RailBlock AI.

Extracts, filters, and normalizes real railway stations along the
Chennai Egmore (MS) -> Thoothukudi (TN) corridor from OSM raw data.

Input:
    data/raw/network/osm/chennai_thoothukudi/stations_raw.geojson

Output:
    data/processed/network/stations_normalized.geojson
"""

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
STATIONS_RAW_FILE = (
    REPO_ROOT
    / "data"
    / "raw"
    / "network"
    / "osm"
    / "chennai_thoothukudi"
    / "stations_raw.geojson"
)
OUTPUT_DIR = REPO_ROOT / "data" / "processed" / "network"
OUTPUT_GEOJSON = OUTPUT_DIR / "stations_normalized.geojson"

# Ordered master list of Indian Railways stations along the
# Chennai Egmore -> Villupuram -> Tiruchchirappalli -> Madurai -> Tuticorin corridor.
# Columns: (station_code, official_station_name, railway_division)
CORRIDOR_STATION_METADATA = [
    ("MS", "Chennai Egmore", "Chennai (MAS)"),
    ("MBM", "Mambalam", "Chennai (MAS)"),
    ("GDY", "Guindy", "Chennai (MAS)"),
    ("STM", "St. Thomas Mount", "Chennai (MAS)"),
    ("PZA", "Palavanthangal", "Chennai (MAS)"),
    ("MN", "Meenambakkam", "Chennai (MAS)"),
    ("TLM", "Tirusulam", "Chennai (MAS)"),
    ("PV", "Pallavaram", "Chennai (MAS)"),
    ("CMP", "Chromepet", "Chennai (MAS)"),
    ("TBMS", "Tambaram Sanatorium", "Chennai (MAS)"),
    ("TBM", "Tambaram", "Chennai (MAS)"),
    ("PRGL", "Perungalattur", "Chennai (MAS)"),
    ("VDR", "Vandalur", "Chennai (MAS)"),
    ("UPM", "Urappakkam", "Chennai (MAS)"),
    ("GI", "Guduvancheri", "Chennai (MAS)"),
    ("CTM", "Kattangulathur", "Chennai (MAS)"),
    ("SKL", "Singaperumal Koil", "Chennai (MAS)"),
    ("CGL", "Chengalpattu Junction", "Chennai (MAS)"),
    ("OV", "Ottivakkam", "Chennai (MAS)"),
    ("KGZ", "Karunguzhi", "Chennai (MAS)"),
    ("MMK", "Madurantakam", "Chennai (MAS)"),
    ("MLMR", "Melmaruvattur", "Chennai (MAS)"),
    ("TZD", "Tozhuppedu", "Chennai (MAS)"),
    ("KSGL", "Karasangal", "Chennai (MAS)"),
    ("OLA", "Olakur", "Chennai (MAS)"),
    ("TMV", "Tindivanam", "Chennai (MAS)"),
    ("MTL", "Mailam", "Tiruchchirappalli (TPJ)"),
    ("PEI", "Perani", "Tiruchchirappalli (TPJ)"),
    ("VVN", "Vikravandi", "Tiruchchirappalli (TPJ)"),
    ("MYP", "Mundiyampakkam", "Tiruchchirappalli (TPJ)"),
    ("VM", "Viluppuram Junction", "Tiruchchirappalli (TPJ)"),
    ("KDMD", "Kandambakkam", "Tiruchchirappalli (TPJ)"),
    ("TVNL", "Tiruvennainallur Road", "Tiruchchirappalli (TPJ)"),
    ("PVN", "Pavunur", "Tiruchchirappalli (TPJ)"),
    ("VRI", "Vriddhachalam Junction", "Tiruchchirappalli (TPJ)"),
    ("TLNR", "Talanallur", "Tiruchchirappalli (TPJ)"),
    ("PNDM", "Pennadam", "Tiruchchirappalli (TPJ)"),
    ("ICG", "Ichchangadu", "Tiruchchirappalli (TPJ)"),
    ("MTUR", "Mathur", "Tiruchchirappalli (TPJ)"),
    ("SNDI", "Sendurai", "Tiruchchirappalli (TPJ)"),
    ("OTK", "Ottakovil", "Tiruchchirappalli (TPJ)"),
    ("ALU", "Ariyalur", "Tiruchchirappalli (TPJ)"),
    ("SLTH", "Sillakkudi", "Tiruchchirappalli (TPJ)"),
    ("KLGM", "Kallagam", "Tiruchchirappalli (TPJ)"),
    ("KKPM", "Kallakkudi Palanganatham", "Tiruchchirappalli (TPJ)"),
    ("PMB", "Pullampadi", "Tiruchchirappalli (TPJ)"),
    ("KTTR", "Kattur", "Tiruchchirappalli (TPJ)"),
    ("LLI", "Lalgudi", "Tiruchchirappalli (TPJ)"),
    ("VLDE", "Valadi", "Tiruchchirappalli (TPJ)"),
    ("SRGM", "Srirangam", "Tiruchchirappalli (TPJ)"),
    ("TPTN", "Tiruchchirappalli Town", "Tiruchchirappalli (TPJ)"),
    ("TP", "Tiruchchirapalli Fort", "Tiruchchirappalli (TPJ)"),
    ("TPE", "Tiruchchirappalli Palakarai", "Tiruchchirappalli (TPJ)"),
    ("TPJ", "Tiruchchirappalli Junction", "Tiruchchirappalli (TPJ)"),
    ("PUG", "Punggudi", "Tiruchchirappalli (TPJ)"),
    ("KLS", "Kolatur", "Tiruchchirappalli (TPJ)"),
    ("MPA", "Manapparai", "Tiruchchirappalli (TPJ)"),
    ("CII", "Chettiyapatti", "Madurai (MDU)"),
    ("VPJ", "Vaiyampatti", "Madurai (MDU)"),
    ("KFC", "Kalpattichatram", "Madurai (MDU)"),
    ("AYR", "Ayyalur", "Madurai (MDU)"),
    ("VDM", "Vadamadurai", "Madurai (MDU)"),
    ("KON", "Kudalnagar", "Madurai (MDU)"),
    ("MDU", "Madurai Junction", "Madurai (MDU)"),
    ("TDN", "Tiruparankundram", "Madurai (MDU)"),
    ("APK", "Aruppukkottai", "Madurai (MDU)"),
    ("TIP", "Tattapparai", "Madurai (MDU)"),
    ("MVN", "Milavittan", "Madurai (MDU)"),
    ("TN", "Tuticorin", "Madurai (MDU)"),
]


def load_raw_stations(path: Path = STATIONS_RAW_FILE) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_corridor_stations(
    raw_data: dict[str, Any] = None,
) -> list[dict[str, Any]]:
    """
    Extract normalized station records matched against raw OSM station points.
    Returns list of dicts: {station_code, station_name, division, latitude, longitude}.
    """
    if raw_data is None:
        raw_data = load_raw_stations()

    # Index OSM stations by uppercase ref
    osm_by_ref: dict[str, tuple[float, float]] = {}
    for feat in raw_data.get("features", []):
        props = feat.get("properties") or {}
        ref = (props.get("ref") or "").strip().upper()
        if ref and ref not in osm_by_ref:
            coords = feat["geometry"]["coordinates"]
            osm_by_ref[ref] = (float(coords[1]), float(coords[0]))  # (lat, lon)

    stations = []
    for code, name, division in CORRIDOR_STATION_METADATA:
        if code in osm_by_ref:
            lat, lon = osm_by_ref[code]
        else:
            raise ValueError(f"Station {code} ({name}) not found in raw OSM stations data!")

        stations.append({
            "station_code": code,
            "station_name": name,
            "division": division,
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
        })

    return stations


def save_stations_geojson(
    stations: list[dict[str, Any]], output_path: Path = OUTPUT_GEOJSON
) -> Path:
    """Save normalized stations as a GeoJSON FeatureCollection."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [st["longitude"], st["latitude"]],
            },
            "properties": {
                "station_code": st["station_code"],
                "station_name": st["station_name"],
                "division": st["division"],
            },
        }
        for st in stations
    ]

    fc = {
        "type": "FeatureCollection",
        "name": "chennai_thoothukudi_stations",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": features,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(fc, f, indent=2)
    return output_path


def main():
    print("Extracting and normalizing corridor stations...")
    stations = get_corridor_stations()
    out_file = save_stations_geojson(stations)
    print(f"Successfully processed {len(stations)} stations along Chennai Egmore -> Tuticorin.")
    print(f"Saved to: {out_file}")


if __name__ == "__main__":
    main()
