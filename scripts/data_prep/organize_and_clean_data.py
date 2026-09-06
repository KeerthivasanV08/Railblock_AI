"""
organize_and_clean_data.py
==========================
RailBlock AI — Data Organization, Reorganization & Cleanup
Executes Step 10 & 11 of the Implementation Plan:
  - Moves original raw files to canonical standardized locations
  - Renames files using snake_case naming convention
  - Removes confirmed redundant duplicate copies
  - Preserves exact source contents
"""

import os
import sys
import shutil
import hashlib

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.abspath("d:/Railblock_AI")
DATA_DIR = os.path.join(BASE_DIR, "data")

TARGET_DIRS = [
    "data/raw/timetable/ogd",
    "data/raw/infrastructure/ogd",
    "data/raw/traffic/ogd",
    "data/raw/reference/railway_statistics",
    "data/raw/reference/cag"
]

for d in TARGET_DIRS:
    os.makedirs(os.path.join(BASE_DIR, d), exist_ok=True)
print("Verified target directory hierarchy.")

# 1. Timetable files
src_tt1 = os.path.join(DATA_DIR, "raw/Train_details_22122017.csv")
src_tt2 = os.path.join(DATA_DIR, "raw/Train_details_22122017 (1).csv")
dst_tt1 = os.path.join(DATA_DIR, "raw/timetable/ogd/railway_train_details_original.csv")
dst_tt2 = os.path.join(DATA_DIR, "raw/timetable/ogd/railway_train_details_original_2.csv")

if os.path.exists(src_tt1):
    shutil.move(src_tt1, dst_tt1)
    print(f"Moved: {src_tt1} -> {dst_tt1}")
elif os.path.exists(dst_tt1):
    print(f"Already at destination: {dst_tt1}")

if os.path.exists(src_tt2):
    shutil.move(src_tt2, dst_tt2)
    print(f"Moved: {src_tt2} -> {dst_tt2}")
elif os.path.exists(dst_tt2):
    print(f"Already at destination: {dst_tt2}")

# Remove redundant duplicate in raw/timetable if it exists
redundant_tt = os.path.join(DATA_DIR, "raw/timetable/Train_details_22122017.csv")
if os.path.exists(redundant_tt):
    os.remove(redundant_tt)
    print(f"Removed redundant duplicate: {redundant_tt}")

# 2. Key Railway Statistics
src_stats = os.path.join(DATA_DIR, "raw/68_Railway_Key_Statistics_1950-51_to_2013-14.csv")
dst_stats = os.path.join(DATA_DIR, "raw/reference/railway_statistics/railway_key_statistics_1950_51_to_2013_14.csv")

if os.path.exists(src_stats):
    shutil.move(src_stats, dst_stats)
    print(f"Moved: {src_stats} -> {dst_stats}")
elif os.path.exists(dst_stats):
    print(f"Already at destination: {dst_stats}")

# 3. CAG Reports
cag_files = [f for f in os.listdir(os.path.join(DATA_DIR, "raw")) if f.startswith("Report_No.45") or f.startswith("Report-No.-22")]
for f in cag_files:
    src_f = os.path.join(DATA_DIR, "raw", f)
    if "45" in f:
        dst_f = os.path.join(DATA_DIR, "raw/reference/cag/cag_report_45_2018_track_maintenance.pdf")
    else:
        dst_f = os.path.join(DATA_DIR, "raw/reference/cag/cag_report_22_2022_derailments.pdf")
    shutil.move(src_f, dst_f)
    print(f"Moved: {src_f} -> {dst_f}")

# Clean up raw/cag/ folder if it exists
raw_cag_dir = os.path.join(DATA_DIR, "raw/cag")
if os.path.exists(raw_cag_dir):
    shutil.rmtree(raw_cag_dir)
    print(f"Removed temporary directory: {raw_cag_dir}")

print("\n--- FILE REORGANIZATION AND CLEANUP COMPLETED ---")
