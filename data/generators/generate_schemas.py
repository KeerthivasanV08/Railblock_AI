"""Data source scanner for schema generation."""
import os
import json
import pandas as pd
from pathlib import Path

DATA_ROOT = Path("data")
SCHEMA_DIR = DATA_ROOT / "schemas"
SCHEMA_DIR.mkdir(exist_ok=True)

def schema_from_df(df: pd.DataFrame, title: str, source_file: str) -> dict:
    props = {}
    for col in df.columns:
        dtype = str(df[col].dtype)
        if "int" in dtype:
            props[col] = {"type": "integer"}
        elif "float" in dtype:
            props[col] = {"type": "number"}
        elif "bool" in dtype:
            props[col] = {"type": "boolean"}
        else:
            props[col] = {"type": "string"}
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": title,
        "description": f"Schema derived from {source_file}",
        "type": "object",
        "properties": props,
        "required": list(df.columns[:4].tolist()),
    }

def find_csv(root: str, pattern: str) -> Path | None:
    for fpath in Path(root).rglob("*.csv"):
        if pattern.lower() in fpath.name.lower():
            return fpath
    return None

def write_schema(schema: dict, name: str):
    out_path = SCHEMA_DIR / name
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    print(f"  Written: {out_path}")

# Enumerate source CSVs
print("=== Raw data CSV scan ===")
for root, dirs, files in os.walk("data/raw"):
    for f in files:
        if f.endswith(".csv"):
            print(f"  {os.path.join(root, f)}")

print()
print("=== Resource CSV scan ===")
for root, dirs, files in os.walk("data/raw/resources"):
    for f in files:
        print(f"  {os.path.join(root, f)}")

# Generate schemas from actual data
schemas_to_gen = {
    "maintenance_schema.json": ("data/processed/unified_maintenance_tasks.csv", "MaintenanceTask"),
    "block_schema.json": ("data/outputs/weekly_block_plan.csv", "BlockPlan"),
    "resource_schema.json": (None, "ResourceRecord"),  # will search
}

for schema_name, (csv_path, title) in schemas_to_gen.items():
    if csv_path and Path(csv_path).exists():
        try:
            df = pd.read_csv(csv_path, nrows=5)
            s = schema_from_df(df, title, csv_path)
            write_schema(s, schema_name)
        except Exception as e:
            print(f"  SKIP {schema_name}: {e}")
    else:
        print(f"  No source for {schema_name}, will search...")
        # Search in resources
        found = find_csv("data/raw/resources", "")
        if found:
            df = pd.read_csv(found, nrows=5)
            s = schema_from_df(df, title, str(found))
            write_schema(s, schema_name)

# Source system schemas — check what exists in raw/
for system, schema_name, title in [
    ("tms", "tms_schema.json", "TMSDefect"),
    ("smms", "smms_schema.json", "SMMSDefect"),
    ("tdms", "tdms_schema.json", "TDMSDefect"),
    ("coa", "coa_schema.json", "COARecord"),
    ("bdms", "bdms_schema.json", "BDMSRecord"),
]:
    # Search across all raw for matching files
    found = find_csv("data/raw", system)
    if found:
        try:
            df = pd.read_csv(found, nrows=5)
            s = schema_from_df(df, title, str(found))
            write_schema(s, schema_name)
        except Exception as e:
            print(f"  SKIP {schema_name}: {e}")
    else:
        # Create minimal documented schema
        s = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": title,
            "description": f"{system.upper()} source system schema. Data not yet connected — see data/README.md.",
            "type": "object",
            "properties": {
                "record_id": {"type": "string", "description": "Unique record identifier"},
                "section_id": {"type": "string", "description": "Railway section identifier"},
                "logged_date": {"type": "string", "format": "date"},
                "status": {"type": "string"},
            },
            "x-data-status": "NOT_YET_CONNECTED",
            "x-source-system": system.upper(),
        }
        write_schema(s, schema_name)

print("\nDone.")
