"""
Execution Service for managing field execution records, calculating KPIs,
and computing analytics for RailBlock AI closed-loop feedback system.
"""

from datetime import datetime
import logging
from typing import List, Dict, Any, Optional, cast
import pandas as pd
import numpy as np

from app.config.settings import settings
from app.repositories.csv_repository import CSVRepository
from app.utils.csv_utils import sanitize_for_json

logger = logging.getLogger(__name__)


class ExecutionService:
    def __init__(self):
        # Locate execution_records.csv across raw/execution or fallback output locations
        self.raw_records_path = settings.RAW_DATA_ROOT / "execution" / "execution_records.csv"
        self.outcomes_path = settings.OUTPUT_DATA_ROOT / "execution_outcomes.csv"
        
        # Ensure raw repository file path
        if not self.raw_records_path.exists():
            backend_raw = settings.DATA_ROOT / "raw" / "execution" / "execution_records.csv"
            if backend_raw.exists():
                self.raw_records_path = backend_raw
            else:
                self.raw_records_path.parent.mkdir(parents=True, exist_ok=True)
                
        self.repo = CSVRepository(self.raw_records_path)

    def _ensure_df(self) -> pd.DataFrame:
        if self.repo.file_exists():
            df = self.repo.read_csv()
            if isinstance(df, pd.DataFrame) and not df.empty:
                return df
        
        # Fallback to outcomes_path if present
        if self.outcomes_path.exists():
            fallback_repo = CSVRepository(self.outcomes_path)
            df = fallback_repo.read_csv()
            if isinstance(df, pd.DataFrame):
                return df
            
        return pd.DataFrame()

    def get_all_records(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        df = self._ensure_df()
        if df.empty:
            return []
        
        if status:
            df = df[df["status"].astype(str).str.upper() == status.upper()]
            
        # Replace NaNs with suitable JSON/python defaults
        df = df.fillna("")
        records_raw = df.to_dict(orient="records") if isinstance(df, pd.DataFrame) else []
        records: List[Dict[str, Any]] = [dict(r) for r in cast(List[Dict[Any, Any]], records_raw)]
        
        for r in records:
            self._format_record_types(r)
        return cast(List[Dict[str, Any]], sanitize_for_json(records))

    def get_record_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        df = self._ensure_df()
        if df.empty:
            return None
            
        # Match execution_id or block_id
        match = df[(df["execution_id"].astype(str) == record_id) | (df["block_id"].astype(str) == record_id)]
        if match.empty:
            return None
            
        rec: Dict[str, Any] = dict(match.iloc[0].to_dict())
        self._format_record_types(rec)
        return cast(Dict[str, Any], sanitize_for_json(rec))

    def get_active_executions(self) -> List[Dict[str, Any]]:
        df = self._ensure_df()
        if df.empty:
            return []
            
        active_df = df[df["status"].astype(str).str.upper() == "ACTIVE"]
        records_raw = active_df.to_dict(orient="records") if isinstance(active_df, pd.DataFrame) else []
        records: List[Dict[str, Any]] = [dict(r) for r in cast(List[Dict[Any, Any]], records_raw)]
        
        for r in records:
            self._format_record_types(r)
        return cast(List[Dict[str, Any]], sanitize_for_json(records))

    def create_or_update_record(self, data: Dict[str, Any]) -> Dict[str, Any]:
        df = self._ensure_df()
        now_iso = datetime.now().isoformat()
        
        block_id = str(data.get("block_id", "RB-UNKNOWN"))
        execution_id = data.get("execution_id") or f"EXE_{block_id.replace('RB-', '').replace('RB_', '')}"
        
        planned_start = str(data.get("planned_start") or now_iso)
        planned_end = str(data.get("planned_end") or now_iso)
        actual_start = str(data.get("actual_start") or data.get("actual_start_time") or "")
        actual_end = str(data.get("actual_end") or data.get("actual_end_time") or "")
        
        planned_dur = int(float(data.get("planned_duration") or data.get("planned_duration_minutes") or 120))
        
        # Calculate actual duration & variance if start and end are set
        actual_dur = data.get("actual_duration") or data.get("actual_duration_minutes")
        if actual_dur is not None and str(actual_dur) != "":
            actual_dur = int(float(actual_dur))
        elif actual_start and actual_end:
            try:
                st = datetime.fromisoformat(actual_start.replace("Z", "+00:00"))
                et = datetime.fromisoformat(actual_end.replace("Z", "+00:00"))
                actual_dur = int((et - st).total_seconds() // 60)
            except Exception:
                actual_dur = planned_dur
                
        var_min = None
        if actual_dur is not None:
            var_min = int(actual_dur - planned_dur)
            
        comp_tasks = int(float(data.get("completed_tasks", 0) or 0))
        tot_tasks = int(float(data.get("total_tasks", 1) or 1))
        comp_pct = data.get("completion_percentage") or data.get("work_done_pct")
        if comp_pct is None:
            comp_pct = round((comp_tasks / max(1, tot_tasks)) * 100.0, 1)
        else:
            comp_pct = float(comp_pct)
            
        status = str(data.get("status") or data.get("completion_status") or "COMPLETED").upper()
        dev_reason = str(data.get("deviation_reason") or data.get("reason") or "")
        
        record: Dict[str, Any] = {
            "execution_id": execution_id,
            "block_id": block_id,
            "section_id": str(data.get("section_id", "SEC_001")),
            "department": str(data.get("department", "Engineering")),
            "planned_start": planned_start,
            "planned_end": planned_end,
            "actual_start": actual_start,
            "actual_end": actual_end,
            "planned_duration": planned_dur,
            "actual_duration": actual_dur if actual_dur is not None else "",
            "variance_minutes": var_min if var_min is not None else "",
            "completed_tasks": comp_tasks,
            "total_tasks": tot_tasks,
            "completion_percentage": comp_pct,
            "machine_id": str(data.get("machine_id", "")),
            "crew_id": str(data.get("crew_id", "")),
            "status": status,
            "deviation_reason": dev_reason,
            "notes": str(data.get("notes", "")),
            "created_at": now_iso,
            "recorded_by": str(data.get("recorded_by", "controller"))
        }
        
        if not df.empty and "block_id" in df.columns:
            mask = (df["block_id"].astype(str) == block_id) | (df["execution_id"].astype(str) == execution_id)
            if mask.any():
                # Update existing row
                for col, val in record.items():
                    if col not in df.columns:
                        df[col] = ""
                    df.loc[mask, col] = val
            else:
                df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
        else:
            df = pd.DataFrame([record])
            
        self.repo.write_csv(df)
        
        # Also sync to output outcomes csv for feedback engine legacy support
        try:
            outcomes_repo = CSVRepository(self.outcomes_path)
            outcomes_repo.write_csv(df)
        except Exception as e:
            logger.debug(f"Could not sync execution_outcomes.csv: {e}")
            
        self._format_record_types(record)
        return cast(Dict[str, Any], sanitize_for_json(record))

    def compute_kpis(self) -> Dict[str, Any]:
        df = self._ensure_df()
        if df.empty:
            return {
                "total_executions": 0,
                "avg_variance": 0.0,
                "overrun_rate": 0.0,
                "block_wastage": None,
                "block_wastage_formatted": "N/A",
                "note": "No completed possession records"
            }
            
        # Non-active completed or finished possession records
        completed_records = df[df["status"].astype(str).str.upper().isin(["COMPLETED", "PARTIAL", "ABANDONED"])]
        
        total_executions = len(completed_records)
        if total_executions == 0:
            return {
                "total_executions": 0,
                "avg_variance": 0.0,
                "overrun_rate": 0.0,
                "block_wastage": None,
                "block_wastage_formatted": "N/A",
                "note": "No completed possession records"
            }
            
        variances = []
        overrun_count = 0
        total_unused_min = 0.0
        total_planned_min = 0.0
        
        for _, row in completed_records.iterrows():
            try:
                planned_dur = float(row.get("planned_duration", 120) or 120)
                actual_dur = float(row.get("actual_duration", planned_dur) or planned_dur)
                var = actual_dur - planned_dur
                variances.append(var)
                
                total_planned_min += planned_dur
                
                if var > 0:
                    overrun_count += 1
                elif var < 0:
                    total_unused_min += abs(var)
            except Exception:
                continue
                
        avg_variance = round(float(np.mean(variances)), 1) if variances else 0.0
        overrun_rate = round((overrun_count / max(1, total_executions)) * 100.0, 1)
        
        if total_planned_min > 0:
            block_wastage: Optional[float] = round((total_unused_min / total_planned_min) * 100.0, 1)
            block_wastage_formatted = f"{block_wastage}%"
        else:
            block_wastage = None
            block_wastage_formatted = "N/A"
            
        res = {
            "total_executions": total_executions,
            "avg_variance": avg_variance,
            "overrun_rate": overrun_rate,
            "block_wastage": block_wastage,
            "block_wastage_formatted": block_wastage_formatted,
            "note": "Under planned duration" if avg_variance < 0 else "Over planned duration"
        }
        return cast(Dict[str, Any], sanitize_for_json(res))

    def get_analytics(self) -> Dict[str, Any]:
        df = self._ensure_df()
        if df.empty:
            return {
                "planned_vs_actual": [],
                "status_distribution": [],
                "variance_trend": [],
                "top_deviation_reasons": []
            }
            
        # 1. Planned vs Actual Duration (latest 15 records)
        completed = df[df["status"].astype(str).str.upper().isin(["COMPLETED", "PARTIAL", "ABANDONED"])].copy()
        p_vs_a = []
        for _, row in completed.tail(15).iterrows():
            try:
                p_dur = int(float(row.get("planned_duration", 120) or 120))
                a_dur = int(float(row.get("actual_duration", p_dur) or p_dur))
                p_vs_a.append({
                    "block_id": str(row.get("block_id", "")),
                    "section_id": str(row.get("section_id", "")),
                    "planned_duration": p_dur,
                    "actual_duration": a_dur,
                    "variance": a_dur - p_dur
                })
            except Exception:
                pass
                
        # 2. Execution Status Distribution
        status_counts = df["status"].astype(str).str.upper().value_counts().to_dict()
        tot_all = len(df)
        status_dist = []
        for st, cnt in status_counts.items():
            status_dist.append({
                "status": str(st),
                "count": cnt,
                "percentage": round((float(cnt) / max(1, tot_all)) * 100.0, 1)
            })
            
        # 3. Variance Trend (grouped by day)
        trend_map: Dict[str, List[float]] = {}
        overrun_map: Dict[str, int] = {}
        
        for _, row in completed.iterrows():
            date_str = str(row.get("actual_start") or row.get("planned_start") or "")[:10]
            if not date_str:
                continue
            try:
                p_dur = float(row.get("planned_duration", 120) or 120)
                a_dur = float(row.get("actual_duration", p_dur) or p_dur)
                var = a_dur - p_dur
                trend_map.setdefault(date_str, []).append(var)
                if var > 0:
                    overrun_map[date_str] = overrun_map.get(date_str, 0) + 1
                else:
                    overrun_map.setdefault(date_str, 0)
            except Exception:
                pass
                
        variance_trend = []
        for date_key in sorted(trend_map.keys()):
            arr = trend_map[date_key]
            variance_trend.append({
                "date": date_key,
                "avg_variance": round(float(np.mean(arr)), 1),
                "overrun_count": overrun_map.get(date_key, 0)
            })
            
        # 4. Top Deviation Reasons
        reasons_df = df[df["deviation_reason"].astype(str).str.strip() != ""]
        reason_counts = reasons_df["deviation_reason"].astype(str).value_counts().to_dict()
        tot_reasons = len(reasons_df)
        top_reasons = []
        for r_name, r_cnt in reason_counts.items():
            r_str = str(r_name)
            if r_str and r_str != "nan":
                top_reasons.append({
                    "reason": r_str,
                    "count": r_cnt,
                    "percentage": round((float(r_cnt) / max(1, tot_reasons)) * 100.0, 1)
                })
                
        res = {
            "planned_vs_actual": p_vs_a,
            "status_distribution": status_dist,
            "variance_trend": variance_trend,
            "top_deviation_reasons": top_reasons
        }
        return cast(Dict[str, Any], sanitize_for_json(res))

    def _format_record_types(self, rec: Dict[str, Any]) -> None:
        for k, v in list(rec.items()):
            if pd.isna(v) if not isinstance(v, (list, tuple, dict)) else False:
                rec[k] = None
        for int_field in ["planned_duration", "completed_tasks", "total_tasks"]:
            v = rec.get(int_field)
            if v is not None and str(v) != "":
                try:
                    rec[int_field] = int(float(v))
                except Exception:
                    rec[int_field] = 0
            else:
                rec[int_field] = 0
        for optional_int in ["actual_duration", "variance_minutes"]:
            v = rec.get(optional_int)
            if v is not None and str(v) != "":
                try:
                    rec[optional_int] = int(float(v))
                except Exception:
                    rec[optional_int] = None
            else:
                rec[optional_int] = None
        v_comp = rec.get("completion_percentage")
        if v_comp is not None and str(v_comp) != "":
            try:
                rec["completion_percentage"] = float(v_comp)
            except Exception:
                rec["completion_percentage"] = 0.0
        else:
            rec["completion_percentage"] = 0.0
