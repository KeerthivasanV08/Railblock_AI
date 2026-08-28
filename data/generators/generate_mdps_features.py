"""
Generate MDPS feature split files: train.csv, validation.csv, test.csv.

Uses the SAME preprocessing and random split used during model training
to ensure reproducibility. Output goes to data/features/mdps_features/.
"""
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split


LABEL_FILE = PROJECT_ROOT / "data" / "raw" / "historical" / "mdps_training_labels.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "features" / "mdps_features"
METADATA_FILE = PROJECT_ROOT / "backend" / "app" / "ml" / "models" / "mdps_feature_metadata.json"

SEV_MAP = {"A": 3, "B": 2, "C": 1}
TRAFFIC_MAP = {"High": 3, "Medium": 2, "Low": 1}
FEATURE_COLS = ["sev_num", "overdue_days", "traffic_num", "deferred_count"]
TARGET_COL = "actual_priority_rank"
RANDOM_SEED = 42


def generate_feature_splits():
    print(f"Loading labels from: {LABEL_FILE}")
    if not LABEL_FILE.exists():
        print(f"ERROR: Label file not found at {LABEL_FILE}")
        return False

    df = pd.read_csv(LABEL_FILE)
    print(f"Loaded {len(df)} rows, columns: {df.columns.tolist()}")

    # Apply same feature engineering as training
    if "severity_class" in df.columns:
        df["sev_num"] = df["severity_class"].map(SEV_MAP).fillna(1).astype(int)
    elif "sev_num" not in df.columns:
        print("ERROR: Neither 'severity_class' nor 'sev_num' found")
        return False

    if "traffic_density_class" in df.columns:
        df["traffic_num"] = df["traffic_density_class"].map(TRAFFIC_MAP).fillna(1).astype(int)
    elif "traffic_density" in df.columns:
        df["traffic_num"] = df["traffic_density"].apply(
            lambda x: 3 if x > 0.7 else (2 if x > 0.4 else 1)
        ).astype(int)
    elif "traffic_num" not in df.columns:
        print("ERROR: No traffic column found")
        return False

    if "deferred_count" not in df.columns:
        df["deferred_count"] = 0

    if TARGET_COL not in df.columns:
        print(f"ERROR: Target column '{TARGET_COL}' not found")
        return False

    feature_df = df[FEATURE_COLS + [TARGET_COL]].dropna()
    print(f"Feature matrix: {len(feature_df)} rows after dropna")

    # Deterministic split (same as training)
    train_df, temp_df = train_test_split(feature_df, test_size=0.3, random_state=RANDOM_SEED)
    val_df, test_df = train_test_split(temp_df, test_size=0.5, random_state=RANDOM_SEED)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    train_df.to_csv(OUTPUT_DIR / "train.csv", index=False)
    val_df.to_csv(OUTPUT_DIR / "validation.csv", index=False)
    test_df.to_csv(OUTPUT_DIR / "test.csv", index=False)

    print(f"Written splits:")
    print(f"  train.csv:      {len(train_df):,} rows")
    print(f"  validation.csv: {len(val_df):,} rows")
    print(f"  test.csv:       {len(test_df):,} rows")

    # Write split metadata
    meta = {
        "source_file": str(LABEL_FILE.name),
        "feature_columns": FEATURE_COLS,
        "target_column": TARGET_COL,
        "random_seed": RANDOM_SEED,
        "total_rows": len(feature_df),
        "train_rows": len(train_df),
        "validation_rows": len(val_df),
        "test_rows": len(test_df),
        "sev_map": SEV_MAP,
        "traffic_map": TRAFFIC_MAP,
    }
    with open(OUTPUT_DIR / "split_metadata.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(f"  split_metadata.json written")
    return True


if __name__ == "__main__":
    ok = generate_feature_splits()
    sys.exit(0 if ok else 1)
