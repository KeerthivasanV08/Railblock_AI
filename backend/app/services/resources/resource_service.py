"""
Live Resource Inventory, Allocation & Monitoring Service for RailBlock AI.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd
from app.config.settings import settings
from app.repositories.resource_repository import ResourceRepository
from app.repositories.csv_repository import CSVRepository
from app.utils.csv_utils import sanitize_for_json


class ResourceService:
    def __init__(self):
        self.repo = ResourceRepository()
        self.weekly_repo = CSVRepository(settings.OUTPUT_DATA_ROOT / "weekly_block_plan.csv")
        self.rolling_repo = CSVRepository(settings.OUTPUT_DATA_ROOT / "rolling_26week_block_plan.csv")

    @staticmethod
    def _infer_machine_department(mch_type: str) -> str:
        t = mch_type.lower()
        if "tower" in t or "ohe" in t or "trd" in t:
            return "TRD"
        if "signal" in t or "point" in t or "telecom" in t or "s&t" in t:
            return "S&T"
        return "Engineering"

    def _get_active_block_allocations(self) -> pd.DataFrame:
        """Loads all scheduled/proposed blocks from weekly and rolling plans."""
        dfs = []
        if self.weekly_repo.file_exists():
            wdf = self.weekly_repo.read_csv()
            if not wdf.empty:
                dfs.append(wdf)
        if self.rolling_repo.file_exists():
            rdf = self.rolling_repo.read_csv()
            if not rdf.empty:
                dfs.append(rdf)
        if not dfs:
            return pd.DataFrame()
        combined = pd.concat(dfs, ignore_index=True)
        if "block_id" in combined.columns:
            combined = combined.drop_duplicates(subset=["block_id"])
        return combined

    def get_machines_paginated(
        self,
        page: int = 1,
        page_size: int = 50,
        resource_type: Optional[str] = None
    ) -> Dict[str, Any]:
        df = self.repo.get_machines()
        if df.empty:
            return {"items": [], "page": page, "page_size": page_size, "total": 0, "pages": 0}

        if resource_type:
            df = df[df["resource_type"].astype(str).str.lower() == resource_type.strip().lower()]

        blocks_df = self._get_active_block_allocations()
        
        # Build machine assignment map from scheduled blocks
        assignment_map = {}
        if not blocks_df.empty and "resources" in blocks_df.columns:
            for _, b in blocks_df.iterrows():
                res_str = str(b.get("resources", "")).lower()
                b_id = str(b.get("block_id", ""))
                task_id = str(b.get("task_ids", b_id))
                for _, m in df.iterrows():
                    m_id = str(m.get("resource_id", ""))
                    m_type = str(m.get("resource_type", "")).lower()
                    if m_id not in assignment_map and (m_type in res_str or m_id in res_str):
                        assignment_map[m_id] = {
                            "assigned_task_id": task_id,
                            "assigned_block_id": b_id,
                            "utilization": round(float(b.get("utilization", 0.85) or 0.85) * (100 if float(b.get("utilization", 0.85) or 0.85) <= 1.0 else 1), 1)
                        }

        records = []
        for idx, row in df.iterrows():
            m_id = str(row.get("resource_id", f"MCH_{int(str(idx))+1:04d}"))
            m_type = str(row.get("resource_type", "Tower Wagon"))
            depot = str(row.get("home_depot", "Central Depot"))
            is_avail = bool(row.get("is_available", True))
            dept = self._infer_machine_department(m_type)
            
            assignment = assignment_map.get(m_id)
            if assignment:
                avail_status = "Assigned"
                task_assigned = assignment["assigned_task_id"]
                utilization = assignment["utilization"]
            elif is_avail:
                avail_status = "Available"
                task_assigned = None
                utilization = 72.5
            else:
                avail_status = "Maintenance"
                task_assigned = None
                utilization = 0.0

            records.append({
                "resource_id": m_id,
                "type": m_type,
                "resource_type": m_type,
                "department": dept,
                "home_depot": depot,
                "current_location": depot,
                "availability": avail_status,
                "status": avail_status,
                "last_updated": str(row.get("last_updated", "2026-09-01 08:00:00")),
                "assigned_task_id": task_assigned,
                "utilization": utilization
            })

        total = len(records)
        start = (page - 1) * page_size
        end = start + page_size
        items = sanitize_for_json(records[start:end])
        pages = (total + page_size - 1) // page_size if page_size > 0 else 1

        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": pages
        }

    def get_crews_paginated(
        self,
        page: int = 1,
        page_size: int = 50,
        department: Optional[str] = None
    ) -> Dict[str, Any]:
        df = self.repo.get_crews()
        if df.empty:
            return {"items": [], "page": page, "page_size": page_size, "total": 0, "pages": 0}

        if department:
            depts = [d.strip().lower() for d in department.split(",") if d.strip()]
            df = df[df["department"].astype(str).str.lower().isin(depts)]

        blocks_df = self._get_active_block_allocations()
        
        # Build crew assignment map
        crew_assignment_map = {}
        if not blocks_df.empty and "crew" in blocks_df.columns:
            for _, b in blocks_df.iterrows():
                crew_str = str(b.get("crew", "")).lower()
                b_id = str(b.get("block_id", ""))
                for _, c in df.iterrows():
                    c_id = str(c.get("crew_id", "")).lower()
                    c_dept = str(c.get("department", "")).lower()
                    if c_id not in crew_assignment_map and (c_id in crew_str or c_dept in crew_str):
                        crew_assignment_map[str(c.get("crew_id", ""))] = {
                            "assigned_block_id": b_id,
                            "utilization": round(float(b.get("utilization", 0.85) or 0.85) * (100 if float(b.get("utilization", 0.85) or 0.85) <= 1.0 else 1), 1)
                        }

        records = []
        for idx, row in df.iterrows():
            c_id = str(row.get("crew_id", f"CREW_{int(str(idx))+1:04d}"))
            c_dept = str(row.get("department", "Engineering"))
            depot = str(row.get("home_depot", "Depot"))
            st_start = str(row.get("shift_start", "08:00:00"))[:5]
            st_end = str(row.get("shift_end", "16:00:00"))[:5]
            is_avail = bool(row.get("is_available", True))
            headcount = int(row.get("headcount", 8))

            shift_label = f"Day {st_start}–{st_end}" if "08" in st_start or "06" in st_start else f"Night {st_start}–{st_end}"

            assignment = crew_assignment_map.get(c_id)
            if assignment:
                avail_status = "Assigned"
                block_assigned = assignment["assigned_block_id"]
                utilization = assignment["utilization"]
            elif is_avail:
                avail_status = "Available"
                block_assigned = None
                utilization = 78.0
            else:
                avail_status = "Off Duty"
                block_assigned = None
                utilization = 0.0

            records.append({
                "crew_id": c_id,
                "department": c_dept,
                "depot": depot,
                "home_depot": depot,
                "shift": shift_label,
                "headcount": headcount,
                "availability": avail_status,
                "status": avail_status,
                "assigned_block_id": block_assigned,
                "utilization": utilization
            })

        total = len(records)
        start = (page - 1) * page_size
        end = start + page_size
        items = sanitize_for_json(records[start:end])
        pages = (total + page_size - 1) // page_size if page_size > 0 else 1

        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": pages
        }

    def get_resource_calendar(self, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """Returns unified calendar allocations across machinery and crews."""
        blocks_df = self._get_active_block_allocations()
        machines_df = self.repo.get_machines()
        crews_df = self.repo.get_crews()

        calendar_rows = []

        if not blocks_df.empty:
            for _, b in blocks_df.iterrows():
                b_id = str(b.get("block_id", "RB-001"))
                p_date = str(b.get("plan_date", b.get("start_time", "2026-09-01"))).split(" ")[0]
                st_time = str(b.get("start_time", "10:00:00")).split(" ")[-1][:5]
                end_time = str(b.get("end_time", "13:00:00")).split(" ")[-1][:5]
                status = str(b.get("status", "PROPOSED"))
                depts = str(b.get("departments", "Engineering"))
                util = round(float(b.get("utilization", 0.85) or 0.85) * (100 if float(b.get("utilization", 0.85) or 0.85) <= 1.0 else 1), 1)
                task_id = str(b.get("task_ids", "Maintenance Window"))
                res_type = str(b.get("resources", "Heavy Machinery"))
                crew_name = str(b.get("crew", f"Crew {depts}"))

                calendar_rows.append({
                    "resource": f"{res_type} ({b_id})",
                    "resource_id": f"RES-{b_id}",
                    "resource_type": "Machine",
                    "type_name": res_type,
                    "department": depts.split(";")[0],
                    "date": p_date,
                    "start_time": st_time,
                    "end_time": end_time,
                    "availability": "Assigned",
                    "assignment": f"Block {b_id} · Task {task_id}",
                    "block_id": b_id,
                    "status": status,
                    "utilization": util,
                })

                calendar_rows.append({
                    "resource": f"{crew_name} ({b_id})",
                    "resource_id": f"CRW-{b_id}",
                    "resource_type": "Crew",
                    "type_name": crew_name,
                    "department": depts.split(";")[0],
                    "date": p_date,
                    "start_time": st_time,
                    "end_time": end_time,
                    "availability": "Assigned",
                    "assignment": f"Field Execution · {b_id}",
                    "block_id": b_id,
                    "status": status,
                    "utilization": util,
                })

        if len(calendar_rows) < 10 and not machines_df.empty:
            for idx, m in machines_df.head(10).iterrows():
                m_id = str(m.get("resource_id", f"MCH_{idx:03d}"))
                m_type = str(m.get("resource_type", "Machine"))
                dept = self._infer_machine_department(m_type)
                calendar_rows.append({
                    "resource": f"{m_id} · {m_type}",
                    "resource_id": m_id,
                    "resource_type": "Machine",
                    "type_name": m_type,
                    "department": dept,
                    "date": "2026-09-01",
                    "start_time": "08:00",
                    "end_time": "16:00",
                    "availability": "Available",
                    "assignment": "Standby / Routine Maintenance",
                    "block_id": "—",
                    "status": "AVAILABLE",
                    "utilization": 65.0,
                })

        total = len(calendar_rows)
        start = (page - 1) * page_size
        end = start + page_size
        items = sanitize_for_json(calendar_rows[start:end])
        pages = (total + page_size - 1) // page_size if page_size > 0 else 1

        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": pages
        }

    def get_live_resources(self) -> Dict[str, Any]:
        mch_res = self.get_machines_paginated(page=1, page_size=200)
        crew_res = self.get_crews_paginated(page=1, page_size=200)

        avail_mch = sum(1 for m in mch_res["items"] if m["availability"] in ("Available", "Assigned"))
        avail_crew = sum(1 for c in crew_res["items"] if c["availability"] in ("Available", "Assigned"))

        return {
            "status": "SUCCESS",
            "machines": mch_res["items"],
            "machinery": mch_res["items"],
            "crews": crew_res["items"],
            "available_machine_count": avail_mch,
            "available_crew_count": avail_crew,
            "total_machines": mch_res["total"],
            "total_crews": crew_res["total"]
        }

