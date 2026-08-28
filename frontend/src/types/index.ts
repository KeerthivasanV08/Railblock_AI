/** RailBlock AI — core domain types (synthetic demo domain model). */

export type Department = "Engineering" | "TRD" | "S&T";
export type Severity = "A" | "B" | "C";
export type TaskStatus = "Pending" | "Scheduled" | "In Progress" | "Completed" | "Deferred";
export type SourceSystem = "TMS" | "SMMS" | "TDMS" | "COA" | "RESOURCES";

export interface Station {
  station_code: string;
  name: string;
  km: number;
  lat: number;
  lng: number;
  major: boolean;
}

export interface BlockSection {
  section_id: string;
  from_station: string;
  to_station: string;
  from_km: number;
  to_km: number;
  traffic_density: number; // 0-100
  double_line: boolean;
}

export type TrainCategory = "Passenger" | "Express" | "Freight";

export interface Train {
  train_number: string;
  name: string;
  category: TrainCategory;
  direction: "UP" | "DOWN";
  section_id: string;
  km: number;
  speed_kmph: number;
  delay_min: number;
  origin: string;
  destination: string;
  scheduled_dep: string; // HH:mm
  scheduled_arr: string; // HH:mm
}

export interface MaintenanceTask {
  task_id: string;
  source_system: SourceSystem;
  department: Department;
  asset: string;
  asset_criticality: number; // 0-100
  section_id: string;
  from_km: number;
  to_km: number;
  location_label: string;
  defect: string;
  severity: Severity;
  overdue_days: number;
  previous_deferrals: number;
  required_duration_min: number;
  required_resource: string;
  status: TaskStatus;
  priority_score: number;
  priority_breakdown: PriorityBreakdown;
  recommended_block_id: string | null;
  mast_number?: string;
  signal_id?: string;
  reported_on: string; // ISO
  history: { date: string; note: string }[];
}

export interface PriorityBreakdown {
  severity: number;
  overdue_risk: number;
  traffic_impact: number;
  asset_criticality: number;
  deferral_risk: number;
}

export type BlockStatus =
  | "DRAFT"
  | "AI RECOMMENDED"
  | "PENDING APPROVAL"
  | "APPROVED"
  | "SCHEDULED"
  | "ACTIVE"
  | "COMPLETED"
  | "REJECTED";

export type PlannerLane =
  "Passenger" | "Express" | "Freight" | "Engineering" | "TRD" | "S&T" | "Integrated";

export interface BlockPlan {
  block_id: string;
  section_id: string;
  lane: PlannerLane;
  departments: Department[];
  task_ids: string[];
  start_min: number; // minutes from 00:00 of plan date
  duration_min: number;
  date: string; // yyyy-MM-dd
  status: BlockStatus;
  ai_generated: boolean;
  locked: boolean;
  utilization: number; // 0-100
  train_impact: "Low" | "Medium" | "High";
  train_conflicts: string[];
  from_km: number;
  to_km: number;
  reason?: string;
  resource_ids: string[];
}

export interface TrainPath {
  id: string;
  train_number: string;
  lane: PlannerLane;
  start_min: number;
  duration_min: number;
  section_id: string;
  from_km: number;
  to_km: number;
}

export type ConflictType =
  | "TRAIN_OVERLAP"
  | "BLOCK_OVERLAP"
  | "MACHINE_UNAVAILABLE"
  | "CREW_UNAVAILABLE"
  | "WINDOW_TOO_SHORT"
  | "CRITICAL_TASK_UNFITTED";

export interface Conflict {
  id: string;
  type: ConflictType;
  block_id: string;
  entity: string;
  window: string;
  severity: "Critical" | "Warning";
  message: string;
  suggestions: { start_min: number; duration_min: number; label: string }[];
}

export type ResourceAvailability = "Available" | "Assigned" | "Under Maintenance" | "Unavailable";

export interface Machine {
  resource_id: string;
  type: string;
  department: Department;
  home_depot: string;
  current_location: string;
  km: number;
  availability: ResourceAvailability;
  last_updated: string;
  assigned_task_id: string | null;
  utilization: number;
}

export interface Crew {
  crew_id: string;
  department: Department;
  depot: string;
  shift: "Day 08–20" | "Night 20–08";
  headcount: number;
  availability: ResourceAvailability;
  assigned_block_id: string | null;
  km: number;
  utilization: number;
}

export interface DisruptionEvent {
  event_id: string;
  type: "Train Delay" | "Asset Failure" | "Weather" | "Resource Breakdown";
  detected_at: string;
  train_number?: string;
  delay_min: number;
  section_id: string;
  location: string;
  affected_block_id: string | null;
  original_window: string;
  available_window: string;
  status: "Open" | "Rescheduled" | "Dismissed";
  severity: "Critical" | "Warning" | "Info";
}

export interface RescheduleOption {
  id: string;
  label: string;
  start_min: number;
  duration_min: number;
  train_impact: "Low" | "Medium" | "High";
  maintenance_impact: string;
  resource_impact: string;
  utilization: number;
  confidence: number;
  added_train_delay_min: number;
}

export interface AIRecommendation {
  recommendation_id: string;
  block_id: string;
  section_id: string;
  start_min: number;
  duration_min: number;
  departments: Department[];
  task_ids: string[];
  priority: number;
  utilization: number;
  train_impact: "Low" | "Medium" | "High";
  confidence: number;
  status: "Pending" | "Approved" | "Rejected" | "Modified";
  reasons: string[];
  factors: { label: string; value: number }[];
  date: string;
}

export type NotificationType =
  | "Critical Defect"
  | "Train Delay"
  | "Block Conflict"
  | "Resource Conflict"
  | "AI Recommendation"
  | "Approval Required"
  | "Disruption"
  | "System Alert";

export interface AppNotification {
  id: string;
  type: NotificationType;
  title: string;
  body: string;
  at: string;
  read: boolean;
  href: string;
  severity: "Critical" | "Warning" | "Info";
}

export interface AuditEvent {
  id: string;
  at: string;
  role: string;
  action: string;
  entity: string;
  result: "Success" | "Failed";
  detail?: string;
}

export type DemoRole =
  | "Control Office Operator"
  | "Section Controller"
  | "DRM / Divisional Officer"
  | "Engineering Planner"
  | "TRD Planner"
  | "S&T Planner"
  | "Field Maintenance Team"
  | "System Administrator";

export interface TrendPoint {
  label: string;
  value: number;
  secondary?: number;
}

export interface AnalyticsKPI {
  label: string;
  value: number;
  unit: "%" | "count" | "min" | "score";
  trend: number; // +/- delta vs previous period
  status: "ok" | "warn" | "crit";
}

export interface DepartmentWorkload {
  department: Department;
  open: number;
  completed: number;
  overdue: number;
}

export interface BeforeAfterMetric {
  label: string;
  before: number;
  after: number;
  unit: "%" | "count" | "min";
  betterWhenLower: boolean;
}

export interface ReportDefinition {
  id: string;
  title: string;
  category:
    | "Weekly Block Plan"
    | "Monthly Rolling Plan"
    | "Maintenance Summary"
    | "Resource Utilization"
    | "Disruption Summary"
    | "AI Recommendation Summary"
    | "Audit Report";
  description: string;
  generated_at: string;
  rows: number;
}
