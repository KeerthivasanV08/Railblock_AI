"""
run_all_prep.py
===============
RailBlock AI — Master Data Setup & Preprocessing Runner
Executes all data engineering and preprocessing pipelines in sequence.
"""

import os
import sys
import subprocess

sys.stdout.reconfigure(encoding="utf-8")

PIPELINE_STEPS = [
    ("Phase 1: Existing-Data & Defect Audit",       "scripts/data_prep/audit_existing_defects.py"),
    ("Phase 2: CAG Railway Audit Data Extraction", "scripts/data_prep/extract_cag_evidence.py"),
    ("Phase 3: Weather & Festival Data Processing", "scripts/data_prep/process_environmental_and_festivals.py"),
    ("Phase 4: Freight & Traffic Statistics",       "scripts/data_prep/process_freight_and_traffic.py"),
    ("Phase 5: Calibrated Operational Datasets",    "scripts/data_prep/generate_calibrated_operational_data.py"),
    ("Phase 6: Unified Tables & Feature Prep",      "scripts/data_prep/build_unified_feature_tables.py"),
    ("Phase 7: Metadata & Validation Suite",        "scripts/data_prep/build_metadata_and_validation.py")
]

def run_step(name, script_path):
    print(f"\n==================================================")
    print(f"RUNNING: {name}")
    print(f"SCRIPT:  {script_path}")
    print(f"==================================================")
    res = subprocess.run([sys.executable, script_path], capture_output=True, text=True, encoding="utf-8")
    print(res.stdout)
    if res.stderr:
        print("STDERR / WARNINGS:\n", res.stderr)
    if res.returncode != 0:
        print(f"FAILED: {name} with exit code {res.returncode}")
        sys.exit(res.returncode)
    print(f"PASSED: {name}")

def main():
    print("STARTING RAILBLOCK AI MASTER DATA PREPROCESSING PIPELINE...")
    for name, path in PIPELINE_STEPS:
        run_step(name, path)
    print("\n==================================================")
    print("ALL PREPROCESSING PIPELINES EXECUTED SUCCESSFULLY.")
    print("==================================================")

if __name__ == "__main__":
    main()
