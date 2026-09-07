/**
 * RailBlock AI — Backend ↔ Frontend Schema Adapters
 *
 * The backend uses CSV-derived field names that differ from the frontend's
 * domain model (src/types/index.ts).  All field name normalisation, type
 * coercion, and default-value injection lives HERE — never scattered across
 * individual stores or components.
 *
 * Provenance:
 *   "REAL"      — field value is taken directly from a raw OGD / real dataset
 *   "DERIVED"   — field value is computed by the backend from real inputs
 *   "SYNTHETIC" — field value is locally generated as a fallback
 */

import type {
  BlockPlan,
  BlockStatus,
  Department,
  DisruptionEvent,
  MaintenanceTask,
  PlannerLane,
  PriorityBreakdown,
  Severity,
  SourceSystem,
  TaskStatus,
  Machine,
  Crew,
  ResourceAvailability,
} from "@/types";
import type { BackendTask, TaskPriorityResponse } from "@/api/tasksApi";
import type { BackendBlockItem } from "@/api/blocksApi";
import type { BackendDisruptionEvent } from "@/api/disruptionsApi";
import type { BackendMachine, BackendCrew } from "@/api/resourcesApi";
import { sectionForKm } from "@/data/sections";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Convert "HH:MM" or "HH:MM:SS" or "YYYY-MM-DD HH:MM:SS" → minutes from 00:00 */
export function timeStrToMinutes(t?: string | null): number {
  if (!t) return 120; // default 02:00
  try {
    const timePart = t.includes(" ") ? t.split(" ")[1]! : t;
    const [h, m] = timePart.split(":").map(Number);
    return (h ?? 0) * 60 + (m ?? 0);
  } catch {
    return 120;
  }
}

/** Convert minutes-from-midnight → "HH:MM" */
export function minutesToTimeStr(min: number): string {
  const h = Math.floor(min / 60) % 24;
  const m = min % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

function coerceSeverity(v?: string | null): Severity {
  if (v === "A" || v === "B" || v === "C") return v;
  const up = (v ?? "").toUpperCase();
  if (up === "CRITICAL" || up === "HIGH") return "A";
  if (up === "MEDIUM" || up === "WARNING") return "B";
  return "C";
}

function coerceDepartment(v?: string | null): Department {
  if (v === "Engineering" || v === "TRD" || v === "S&T") return v;
  const up = (v ?? "").toUpperCase();
  if (up.includes("TRD") || up.includes("TRACTION")) return "TRD";
  if (up.includes("S&T") || up.includes("SIGNAL") || up.includes("TELECOM")) return "S&T";
  return "Engineering";
}

function coerceTaskStatus(v?: string | null): TaskStatus {
  const norm: Record<string, TaskStatus> = {
    pending: "Pending",
    scheduled: "Scheduled",
    "in progress": "In Progress",
    inprogress: "In Progress",
    completed: "Completed",
    deferred: "Deferred",
  };
  return norm[(v ?? "").toLowerCase()] ?? "Pending";
}

function coerceSourceSystem(v?: string | null): SourceSystem {
  const up = (v ?? "").toUpperCase();
  if (up === "TMS" || up === "SMMS" || up === "TDMS" || up === "COA" || up === "RESOURCES")
    return up as SourceSystem;
  if (up.includes("TMS")) return "TMS";
  if (up.includes("SMMS")) return "SMMS";
  if (up.includes("TDMS")) return "TDMS";
  return "TMS";
}

function syntheticPriorityBreakdown(score: number): PriorityBreakdown {
  const base = score / 5; // scale to per-factor avg
  return {
    severity: Math.min(100, base * 1.2),
    overdue_risk: Math.min(100, base * 1.1),
    traffic_impact: Math.min(100, base * 0.9),
    asset_criticality: Math.min(100, base),
    deferral_risk: Math.min(100, base * 0.8),
  };
}

// ---------------------------------------------------------------------------
// Task Adapter
// ---------------------------------------------------------------------------

/**
 * Adapts a backend `BackendTask` record to the frontend `MaintenanceTask` type.
 *
 * Key field mappings:
 *   severity_class       → severity
 *   deferred_count       → previous_deferrals
 *   estimated_duration_minutes → required_duration_min
 *   mapped_chainage_km   → from_km / to_km (approximate)
 *   traffic_density      → used to derive traffic_impact within breakdown
 */
export function adaptBackendTask(raw: BackendTask): MaintenanceTask {
  const severity = coerceSeverity(raw.severity_class ?? raw.severity);
  const department = coerceDepartment(raw.department);
  const status = coerceTaskStatus(raw.status);
  const source = coerceSourceSystem(raw.source_system);
  const priorityScore = raw.priority_score ?? raw.criticality_score ?? 50;
  const fromKm = raw.mapped_chainage_km ?? 0;

  return {
    task_id: raw.task_id,
    source_system: source,
    department,
    asset: raw.location_reference_id ?? raw.location_reference_type ?? "Track Asset",
    asset_criticality: Math.round(priorityScore),
    section_id: raw.section_id,
    from_km: fromKm,
    to_km: fromKm + 2, // approximate 2 km extent when not provided
    location_label: raw.section_id,
    defect: raw.defect_type ?? raw.defect ?? "Maintenance Required",
    severity,
    overdue_days: raw.overdue_days ?? 0,
    previous_deferrals: raw.deferred_count ?? raw.previous_deferrals ?? 0,
    required_duration_min: raw.estimated_duration_minutes ?? 120,
    required_resource: raw.required_resource_type ?? "P-Way Gang",
    status,
    priority_score: Math.round(priorityScore),
    priority_breakdown: syntheticPriorityBreakdown(priorityScore),
    recommended_block_id: null,
    reported_on: new Date().toISOString().slice(0, 10),
    history: [],
    ...(raw.mast_number ? { mast_number: raw.mast_number } : {}),
    ...(raw.signal_id ? { signal_id: raw.signal_id } : {}),
  };
}

/**
 * Merges MDPS priority breakdown from the backend priority endpoint into
 * an already-adapted task.
 */
export function mergePriorityBreakdown(
  task: MaintenanceTask,
  priority: TaskPriorityResponse,
): MaintenanceTask {
  const comp = priority.components;
  return {
    ...task,
    priority_score: Math.round(priority.priority_score),
    priority_breakdown: comp
      ? {
          severity: comp.severity,
          overdue_risk: comp.overdue_days,
          traffic_impact: comp.traffic_density,
          asset_criticality: task.asset_criticality,
          deferral_risk: comp.deferrals,
        }
      : task.priority_breakdown,
  };
}

// ---------------------------------------------------------------------------
// Block Adapter
// ---------------------------------------------------------------------------

function coerceBlockStatus(v?: string | null): BlockStatus {
  const norm: Record<string, BlockStatus> = {
    draft: "DRAFT",
    "ai recommended": "AI RECOMMENDED",
    "ai_recommended": "AI RECOMMENDED",
    "pending approval": "PENDING APPROVAL",
    "pending_approval": "PENDING APPROVAL",
    approved: "APPROVED",
    scheduled: "SCHEDULED",
    active: "ACTIVE",
    completed: "COMPLETED",
    rejected: "REJECTED",
  };
  return norm[(v ?? "").toLowerCase()] ?? "DRAFT";
}

function inferLane(departments?: string | string[] | null): PlannerLane {
  const depts = Array.isArray(departments)
    ? departments
    : (departments ?? "").split(/[;,]/).map((d) => d.trim());

  const hasEng = depts.some((d) => d.toLowerCase().includes("engineering"));
  const hasTrd = depts.some((d) => d.toLowerCase().includes("trd"));
  const hasSt = depts.some((d) => d.toLowerCase().includes("s&t") || d.toLowerCase().includes("signal"));

  if (hasEng && hasTrd && hasSt) return "Integrated";
  if (hasEng && (hasTrd || hasSt)) return "Integrated";
  if (hasTrd && hasSt) return "Integrated";
  if (hasTrd) return "TRD";
  if (hasSt) return "S&T";
  return "Engineering";
}

function parseDepartments(departments?: string | string[] | null): Department[] {
  const raw = Array.isArray(departments)
    ? departments
    : (departments ?? "").split(/[;,]/).map((d) => d.trim()).filter(Boolean);
  return raw.map(coerceDepartment);
}

/**
 * Adapts a backend `BackendBlockItem` to the frontend `BlockPlan` type.
 *
 * Key conversions:
 *   start_time "HH:MM" → start_min (int)
 *   duration_minutes    → duration_min (int)
 *   departments string  → Department[] + PlannerLane
 *   status string       → BlockStatus enum
 */
export function adaptBackendBlock(raw: BackendBlockItem): BlockPlan {
  const startMin = raw.start_min ?? timeStrToMinutes(raw.start_time);
  const durationMin = raw.duration_min ?? raw.duration_minutes ?? 120;
  const status = coerceBlockStatus(raw.status);
  const departments = parseDepartments(raw.departments);
  const lane = inferLane(raw.departments);

  const taskIds = Array.isArray(raw.tasks)
    ? raw.tasks
    : (raw.tasks ?? "").split(/[;,]/).map((t: string) => t.trim()).filter(Boolean);

  return {
    block_id: raw.block_id,
    section_id: raw.section_id,
    lane,
    departments,
    task_ids: taskIds,
    start_min: startMin,
    duration_min: durationMin,
    date: raw.date ?? new Date().toISOString().slice(0, 10),
    status,
    ai_generated: status === "AI RECOMMENDED" || status === "DRAFT",
    locked: status === "APPROVED" || status === "ACTIVE",
    utilization: raw.utilization ?? raw.optimization_score ?? 0,
    train_impact: "Medium",
    train_conflicts: [],
    from_km: raw.from_km ?? 0,
    to_km: raw.to_km ?? 0,
    resource_ids: [],
    ...(raw.reason ? { reason: raw.reason } : {}),
  };
}

// ---------------------------------------------------------------------------
// Disruption Adapter
// ---------------------------------------------------------------------------

/**
 * Adapts a backend `BackendDisruptionEvent` to the frontend `DisruptionEvent`.
 *
 * Key mappings:
 *   event_type   → type
 *   delay_minutes → delay_min
 *   severity     → normalised "Critical" | "Warning" | "Info"
 */
export function adaptBackendDisruption(raw: BackendDisruptionEvent): DisruptionEvent {
  type FrontendType = DisruptionEvent["type"];
  const typeMap: Record<string, FrontendType> = {
    train_delay: "Train Delay",
    "train delay": "Train Delay",
    asset_failure: "Asset Failure",
    "asset failure": "Asset Failure",
    weather: "Weather",
    resource_breakdown: "Resource Breakdown",
    "resource breakdown": "Resource Breakdown",
  };

  type SeverityLevel = "Critical" | "Warning" | "Info";
  const sevMap: Record<string, SeverityLevel> = {
    critical: "Critical",
    high: "Critical",
    warning: "Warning",
    medium: "Warning",
    info: "Info",
    low: "Info",
  };

  const type: FrontendType =
    typeMap[(raw.event_type ?? "").toLowerCase()] ?? "Train Delay";
  const severity: SeverityLevel =
    sevMap[(raw.severity ?? "").toLowerCase()] ?? "Warning";

  type StatusType = "Open" | "Rescheduled" | "Dismissed";
  const statusMap: Record<string, StatusType> = {
    open: "Open",
    rescheduled: "Rescheduled",
    dismissed: "Dismissed",
    resolved: "Rescheduled",
  };
  const status: StatusType =
    statusMap[(raw.status ?? "").toLowerCase()] ?? "Open";

  return {
    event_id: raw.event_id,
    type,
    detected_at: raw.detected_at ?? new Date().toTimeString().slice(0, 5),
    delay_min: raw.delay_minutes ?? 0,
    section_id: raw.section_id,
    location: raw.location ?? raw.section_id,
    affected_block_id: raw.affected_block_id ?? null,
    original_window: "—",
    available_window: raw.delay_minutes ? `Reduced by ${raw.delay_minutes} min` : "Unknown",
    status,
    severity,
    ...(raw.train_number ? { train_number: raw.train_number } : {}),
  };
}

// ---------------------------------------------------------------------------
// Resource Adapters
// ---------------------------------------------------------------------------

export function adaptBackendMachine(raw: BackendMachine): Machine {
  const section = raw.km !== undefined ? sectionForKm(raw.km) : null;
  const avail = (raw.availability as ResourceAvailability) ?? "Available";

  return {
    resource_id: raw.resource_id,
    type: raw.type,
    department: coerceDepartment(raw.department),
    home_depot: raw.home_depot,
    base_depot: raw.home_depot,
    current_location: raw.current_location,
    km: raw.km ?? section?.from_km ?? 0,
    availability: avail,
    last_updated: raw.last_updated ?? new Date().toISOString(),
    assigned_task_id: raw.assigned_task_id ?? null,
    utilization: raw.utilization ?? 0,
  };
}

export function adaptBackendCrew(raw: BackendCrew): Crew {
  type ShiftType = "Day 08–20" | "Night 20–08";
  const shiftMap: Record<string, ShiftType> = {
    day: "Day 08–20",
    night: "Night 20–08",
    "08-20": "Day 08–20",
    "20-08": "Night 20–08",
  };
  const shift: ShiftType =
    shiftMap[Object.keys(shiftMap).find((k) => raw.shift?.toLowerCase().includes(k)) ?? ""] ??
    "Day 08–20";

  const avail = (raw.availability as ResourceAvailability) ?? "Available";

  return {
    crew_id: raw.crew_id,
    department: coerceDepartment(raw.department),
    depot: raw.depot,
    base_station: raw.depot,
    shift,
    headcount: raw.headcount,
    availability: avail,
    assigned_block_id: raw.assigned_block_id ?? null,
    km: raw.km ?? 0,
    utilization: raw.utilization ?? 0,
  };
}

// ---------------------------------------------------------------------------
// Provenance helpers
// ---------------------------------------------------------------------------

export type DataProvenance = "REAL" | "DERIVED" | "SYNTHETIC";

export interface ProvenanceInfo {
  source: DataProvenance;
  label: string;
  description: string;
}

export const PROVENANCE: Record<DataProvenance, ProvenanceInfo> = {
  REAL: {
    source: "REAL",
    label: "REAL",
    description: "Data sourced directly from railway operational datasets (OGD/TMS/SMMS/TDMS)",
  },
  DERIVED: {
    source: "DERIVED",
    label: "DERIVED",
    description: "Data computed/processed from real datasets by the RailBlock AI backend",
  },
  SYNTHETIC: {
    source: "SYNTHETIC",
    label: "SYNTHETIC",
    description: "Locally generated demonstration data — backend unavailable or not yet run",
  },
};
