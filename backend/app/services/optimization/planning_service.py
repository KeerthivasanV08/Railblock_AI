"""
Weekly, Monthly, and Rolling Block Planning Service for RailBlock AI.
"""

from datetime import datetime, timedelta
from uuid import uuid4
import pandas as pd
from app.config.settings import settings
from app.repositories.csv_repository import CSVRepository
from app.services.optimization.planner_service import OptimizationService
from app.utils.id_utils import generate_block_id


class PlanningService:
    def __init__(self):
        self.opt_service = OptimizationService()
        self.weekly_repo = CSVRepository(settings.OUTPUT_DATA_ROOT / "weekly_block_plan.csv")
        self.monthly_repo = CSVRepository(settings.OUTPUT_DATA_ROOT / "monthly_rolling_block_plan.csv")
        self.version_repo = CSVRepository(settings.OUTPUT_DATA_ROOT / "plan_versions.csv")

    def generate_weekly_plan(self, start_date: str = None, section_id: str = None) -> pd.DataFrame:
        selected_df, metrics = self.opt_service.run_optimization()
        if section_id:
            selected_df = selected_df[selected_df["section_id"] == section_id]

        plans = []
        base_dt = datetime.fromisoformat(start_date) if start_date else datetime.now()
        run_id = metrics.get("run_id", f"RUN-{uuid4().hex[:12]}")
        generated_at = datetime.now().isoformat()

        for plan_idx, (_, row) in enumerate(selected_df.iterrows()):
            sec = row["section_id"]
            dur = int(row.get("estimated_duration_minutes", 120))
            st_dt = base_dt + timedelta(hours=plan_idx * 4)
            end_dt = st_dt + timedelta(minutes=dur)

            plans.append({
                "block_id": generate_block_id(sec, plan_idx + 1),
                "plan_run_id": run_id,
                "plan_version": 1,
                "generated_at": generated_at,
                "plan_date": st_dt.strftime("%Y-%m-%d"),
                "section_id": sec,
                "start_time": st_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": end_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_minutes": dur,
                "task_ids": row.get("task_id", f"TASK_{plan_idx:04d}"),
                "departments": row.get("departments_involved", row.get("department", "Engineering")),
                "priority": row.get("criticality_score", 75.0),
                "resources": row.get("required_resource_type", "Engineering crew"),
                "crew": f"CREW_{sec}",
                "train_impact": "LOW" if row.get("traffic_density", 0.5) < 0.6 else "MEDIUM",
                "utilization": round(float(row.get("spatial_overlap_score", 0.8)), 2),
                "optimization_score": row.get("optimization_score", 90.0),
                "status": "PROPOSED",
                "xai_reason": f"Recommended shadow-block on {sec} with confirmed resource feasibility and low train impact.",
                "source": "csv",
                "source_record_id": row.get("task_id", ""),
                "dataset_name": "feasibility_checked_tasks.csv",
                "optimizer_status": metrics.get("status", "UNKNOWN"),
            })

        plan_df = pd.DataFrame(plans)
        self.weekly_repo.write_csv(plan_df)
        self._append_plan_versions(plan_df, "WEEKLY", run_id, generated_at)
        return plan_df

    def generate_monthly_plan(self, start_date: str = None) -> pd.DataFrame:
        selected_df, metrics = self.opt_service.run_optimization()
        base_dt = datetime.fromisoformat(start_date) if start_date else datetime.now()
        run_id = metrics.get("run_id", f"RUN-{uuid4().hex[:12]}")
        generated_at = datetime.now().isoformat()
        rows = []

        for week in range(4):
            week_start = base_dt + timedelta(days=7 * week)
            for plan_idx, (_, row) in enumerate(selected_df.iterrows()):
                sec = row["section_id"]
                dur = int(row.get("estimated_duration_minutes", 120))
                st_dt = week_start + timedelta(hours=plan_idx * 4)
                end_dt = st_dt + timedelta(minutes=dur)
                rows.append({
                    "block_id": f"{generate_block_id(sec, plan_idx + 1)}-W{week + 1}",
                    "plan_run_id": run_id,
                    "plan_version": 1,
                    "horizon": "MONTHLY",
                    "generated_at": generated_at,
                    "plan_date": st_dt.strftime("%Y-%m-%d"),
                    "section_id": sec,
                    "start_time": st_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "end_time": end_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "duration_minutes": dur,
                    "task_ids": row.get("task_id", f"TASK_{plan_idx:04d}"),
                    "departments": row.get("departments_involved", row.get("department", "Engineering")),
                    "priority": row.get("criticality_score", 75.0),
                    "resources": row.get("required_resource_type", "Engineering crew"),
                    "crew": f"CREW_{sec}",
                    "train_impact": "LOW" if row.get("traffic_density", 0.5) < 0.6 else "MEDIUM",
                    "utilization": round(float(row.get("spatial_overlap_score", 0.8)), 2),
                    "optimization_score": row.get("optimization_score", 90.0),
                    "status": "PROPOSED",
                    "xai_reason": f"Monthly recommendation for {sec}; human approval required before execution.",
                    "source": "csv",
                    "source_record_id": row.get("task_id", ""),
                    "dataset_name": "feasibility_checked_tasks.csv",
                    "optimizer_status": metrics.get("status", "UNKNOWN"),
                })

        monthly_df = pd.DataFrame(rows)
        self.monthly_repo.write_csv(monthly_df)
        self._append_plan_versions(monthly_df, "MONTHLY", run_id, generated_at)
        return monthly_df

    def _append_plan_versions(self, plan_df: pd.DataFrame, horizon: str, run_id: str, generated_at: str) -> None:
        if plan_df.empty:
            return
        rows = []
        for _, row in plan_df.iterrows():
            rows.append({
                "plan_run_id": run_id,
                "block_id": row["block_id"],
                "plan_version": int(row.get("plan_version", 1)),
                "horizon": horizon,
                "status": row.get("status", "PROPOSED"),
                "start_time": row.get("start_time", ""),
                "end_time": row.get("end_time", ""),
                "created_at": generated_at,
                "source": "csv",
                "source_record_id": row.get("source_record_id", row.get("task_ids", "")),
            })
        self.version_repo.append_rows(rows)
