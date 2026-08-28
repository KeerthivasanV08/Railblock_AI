"""
Quality Report Generator for RailBlock AI.

Generates comprehensive data quality metrics across raw and processed datasets.
"""

import json
import logging
from pathlib import Path
import pandas as pd

from data.preprocessing.config import RAW_DIR, PROCESSED_DIR

logger = logging.getLogger(__name__)


def generate_quality_report() -> dict:
    """
    Computes quality report metrics across raw and processed datasets.
    """
    report = {}

    # Load datasets
    tms = pd.read_csv(RAW_DIR / "defects/tms_defects.csv")
    smms = pd.read_csv(RAW_DIR / "defects/smms_defects.csv")
    tdms = pd.read_csv(RAW_DIR / "defects/tdms_defects.csv")
    unified = pd.read_csv(PROCESSED_DIR / "unified_maintenance_tasks.csv")
    feasibility = pd.read_csv(PROCESSED_DIR / "feasibility_checked_tasks.csv")
    traffic = pd.read_csv(PROCESSED_DIR / "enriched_train_traffic.csv")
    res = pd.read_csv(PROCESSED_DIR / "resource_availability.csv")

    report["row_counts"] = {
        "tms_defects": len(tms),
        "smms_defects": len(smms),
        "tdms_defects": len(tdms),
        "total_tasks": len(unified),
        "feasibility_tasks": len(feasibility),
    }

    # Severity distribution
    sev_counts = unified["severity_class"].value_counts().to_dict()
    total_sev = len(unified)
    report["severity_distribution"] = {
        k: f"{v / total_sev:.2%}" for k, v in sev_counts.items()
    }

    # Department distribution
    dept_counts = unified["department"].value_counts().to_dict()
    report["department_distribution"] = dept_counts

    # Operational metrics
    report["operational_summary"] = {
        "average_overdue_days": round(float(unified["overdue_days"].mean()), 2),
        "average_deferral_count": round(float(unified["deferred_count"].mean()), 2),
        "average_traffic_density": round(float(traffic["traffic_density"].mean()), 3),
        "resource_availability_rate": f"{res['resource_feasible'].mean():.2%}",
        "block_feasibility_rate": f"{feasibility['overall_feasible'].mean():.2%}"
    }

    out_path = PROCESSED_DIR / "quality_report.json"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Data Quality Report saved to {out_path}")
    return report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    rep = generate_quality_report()
    print(json.dumps(rep, indent=2))

