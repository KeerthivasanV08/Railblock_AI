"""
build_unified_feature_tables.py
===============================
Phase 6 of RailBlock AI Data Setup & Preprocessing.
Builds unified maintenance tasks and feature-ready preprocessing tables:
  - data/processed/unified/unified_maintenance_tasks.csv (80,000 rows)
  - data/processed/unified_maintenance_tasks.csv (backward compatibility)
  - data/processed/features/planning_features.csv (80,000 rows)
  - data/processed/features/priority_score_inputs.csv (80,000 rows)
  - data/processed/planning_features.csv (backward compatibility)

STRICT CONSTRAINT: NO MODEL TRAINING PERFORMED.
Feature inputs are purely domain-derived and normalized.
"""

import os
import sys
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.abspath("d:/Railblock_AI")
DATA_DIR = os.path.join(BASE_DIR, "data")

PROC_UNIFIED_DIR = os.path.join(DATA_DIR, "processed/unified")
PROC_FEAT_DIR    = os.path.join(DATA_DIR, "processed/features")
os.makedirs(PROC_UNIFIED_DIR, exist_ok=True)
os.makedirs(PROC_FEAT_DIR, exist_ok=True)

# 1. Load calibrated TMS, SMMS, TDMS
df_tms = pd.read_csv(os.path.join(DATA_DIR, "calibrated/maintenance/tms_defects.csv"))
df_smms = pd.read_csv(os.path.join(DATA_DIR, "calibrated/maintenance/smms_defects.csv"))
df_tdms = pd.read_csv(os.path.join(DATA_DIR, "calibrated/maintenance/tdms_defects.csv"))

# Map required resources by department & defect type
def get_resource_req(dept, task_type):
    if dept == "ENGINEERING":
        if "Tamping" in task_type or "Parameter" in task_type:
            return "Track Tamping Machine (CSM/Duomatic) + Track Maintenance Gang (SSE/P-Way)"
        elif "Ballast" in task_type or "Screening" in task_type:
            return "Ballast Cleaning Machine (BCM) + Deep Screening & Ballasting Crew"
        elif "Weld" in task_type or "Fracture" in task_type:
            return "Mobile Flash Butt Welding Plant + Certified Weld Fitter Team"
        else:
            return "Utility Track Vehicle (UTV) + Track Maintenance Gang"
    elif dept == "SIGNAL":
        if "Point" in task_type or "Interlocking" in task_type:
            return "Signal & Interlocking Maintenance Gang + Point Machine Testing Rig"
        else:
            return "Axle Counter & Point Machine Team + Cable Testing Kit"
    else: # TRACTION
        if "Catenary" in task_type or "Mast" in task_type:
            return "OHE Tower Wagon (8-Wheeler) + OHE Overhead Crew (SSE/TRD)"
        else:
            return "Substation & Switching Post Maintenance Team + Insulation Testing Van"

# Align column names for unification
tms_u = df_tms.copy()
tms_u["date"] = tms_u["logged_date"]
tms_u["task_type"] = tms_u["defect_type"]
tms_u["required_resources"] = [get_resource_req("ENGINEERING", t) for t in tms_u["task_type"]]

smms_u = df_smms.copy()
smms_u["date"] = smms_u["logged_date"]
smms_u["task_type"] = smms_u["defect_type"]
smms_u["required_resources"] = [get_resource_req("SIGNAL", t) for t in smms_u["task_type"]]

tdms_u = df_tdms.copy()
tdms_u["date"] = tdms_u["logged_date"]
tdms_u["task_type"] = tdms_u["defect_type"]
tdms_u["required_resources"] = [get_resource_req("TRACTION", t) for t in tdms_u["task_type"]]

unified_cols = [
    "task_id", "date", "target_completion_date", "department", "task_type",
    "location", "latitude", "longitude", "station_code", "section_id",
    "severity", "priority", "estimated_duration_hours", "deferred_count",
    "required_resources", "status", "corridor_id", "source_type", "source"
]

df_unified = pd.concat([tms_u[unified_cols], smms_u[unified_cols], tdms_u[unified_cols]], ignore_index=True)
out_unified = os.path.join(PROC_UNIFIED_DIR, "unified_maintenance_tasks.csv")
df_unified.to_csv(out_unified, index=False)
print(f"Saved {len(df_unified)} rows to {out_unified}")

# Backward compatibility copy
legacy_unified = os.path.join(DATA_DIR, "processed/unified_maintenance_tasks.csv")
df_unified.to_csv(legacy_unified, index=False)
print(f"Updated legacy processed copy at: {legacy_unified}")

# 2. Build Feature-Ready Inputs (WITHOUT model training)
print("Building Feature-Ready Datasets (Section 32 compliance: No model training)...")

# Load supporting context for feature fusion
df_enr = pd.read_csv(os.path.join(DATA_DIR, "derived/traffic/enriched_traffic.csv"))
traffic_sec_map = df_enr.set_index("section_id").to_dict(orient="index")

df_fest = pd.read_csv(os.path.join(DATA_DIR, "real/reference/festival_calendar.csv"))
fest_date_map = df_fest.set_index("date")["estimated_traffic_multiplier"].to_dict()

# Numerical encoding for features
sev_num = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
prio_rank = {"P1_EMERGENCY": 4, "P2_URGENT": 3, "P3_NORMAL": 2, "P4_ROUTINE": 1}

feat_rows = []
for _, r in df_unified.iterrows():
    sec_id = r["section_id"]
    t_info = traffic_sec_map.get(sec_id, {
        "passenger_trains_daily": 36, "freight_rakes_daily": 12,
        "total_trains_daily": 48, "capacity_utilization_percent": 80.0
    })
    
    d_str = r["date"]
    fest_mult = fest_date_map.get(d_str, 1.0)
    fest_flag = 1 if fest_mult > 1.0 else 0
    
    # Target urgency
    try:
        d1 = datetime.strptime(r["date"], "%Y-%m-%d")
        d2 = datetime.strptime(r["target_completion_date"], "%Y-%m-%d")
        days_to_target = max(1, (d2 - d1).days)
    except Exception:
        days_to_target = 7
        
    feat_rows.append({
        "task_id": r["task_id"],
        "date": r["date"],
        "department": r["department"],
        "section_id": sec_id,
        "severity_level": r["severity"],
        "severity_num": sev_num.get(r["severity"], 2),
        "priority_code": r["priority"],
        "priority_rank": prio_rank.get(r["priority"], 2),
        "estimated_duration_hours": r["estimated_duration_hours"],
        "deferred_count": r["deferred_count"],
        "days_until_target": days_to_target,
        "passenger_trains_daily": t_info.get("passenger_trains_daily", 36),
        "freight_rakes_daily": t_info.get("freight_rakes_daily", 12),
        "total_trains_daily": t_info.get("total_trains_daily", 48),
        "capacity_utilization_percent": t_info.get("capacity_utilization_percent", 80.0),
        "festival_flag": fest_flag,
        "festival_traffic_multiplier": fest_mult,
        "latitude": r["latitude"],
        "longitude": r["longitude"],
        "status": r["status"],
        "source_type": r["source_type"]
    })

df_feat = pd.DataFrame(feat_rows)

out_plan_feat = os.path.join(PROC_FEAT_DIR, "planning_features.csv")
df_feat.to_csv(out_plan_feat, index=False)
print(f"Saved {len(df_feat)} rows to {out_plan_feat}")

legacy_plan_feat = os.path.join(DATA_DIR, "processed/planning_features.csv")
df_feat.to_csv(legacy_plan_feat, index=False)
print(f"Updated legacy planning features copy at: {legacy_plan_feat}")

# Priority score inputs (raw feature matrix for future MDPS ranking engine without computing learned score)
priority_cols = [
    "task_id", "department", "section_id", "severity_num", "priority_rank",
    "estimated_duration_hours", "deferred_count", "days_until_target",
    "total_trains_daily", "capacity_utilization_percent", "festival_traffic_multiplier"
]
df_prio_inputs = df_feat[priority_cols].copy()
out_prio_inputs = os.path.join(PROC_FEAT_DIR, "priority_score_inputs.csv")
df_prio_inputs.to_csv(out_prio_inputs, index=False)
print(f"Saved {len(df_prio_inputs)} rows to {out_prio_inputs}")
print("\nSection 32 Compliance Verified: NO LEARNED PREDICTIONS OR MODELS TRAINED.")
