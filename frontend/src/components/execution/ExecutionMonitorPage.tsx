/**
 * Execution Monitor Page — Closed-Loop Maintenance Execution System
 *
 * Implements the closed-loop execution feedback loop for RailBlock AI:
 *   AI RECOMMENDS → CONTROLLER APPROVES → FIELD EXECUTES → ACTUAL OUTCOME RECORDED → FEEDBACK TO FUTURE PLANNING
 *
 * Sections:
 *   1. Closed-Loop Feedback KPI Cards
 *   2. Active Field Possessions Cards
 *   3. Execution Analytics Charts (Planned vs Actual, Status Distribution, Variance Trend, Top Reasons)
 *   4. Recent Execution Records Table (Filterable by status, Searchable)
 *   5. Record Outcome Dialog (Modal for entering field actuals)
 *   6. Feedback Lifecycle Bottom Banner
 */

import { useEffect, useState, useMemo } from "react";
import {
  Activity,
  BarChart3,
  CheckCircle2,
  Clock,
  Gauge,
  ListChecks,
  RefreshCw,
  Plus,
  AlertTriangle,
  TrendingDown,
  TrendingUp,
  PieChart as PieChartIcon,
  Search,
  Filter,
} from "lucide-react";
import { toast } from "sonner";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from "recharts";

import { PageHeader } from "@/components/common/PageHeader";
import {
  executionApi,
  type ExecutionRecord,
  type ActiveExecution,
  type ExecutionKPIs,
  type ExecutionAnalyticsData,
  type RecordOutcomePayload,
} from "@/api/executionApi";

// -- Status Badges -------------------------------------------------------------
const STATUS_STYLES: Record<string, { bg: string; text: string; border: string }> = {
  SCHEDULED: { bg: "bg-blue-500/10", text: "text-blue-400", border: "border-blue-500/30" },
  ACTIVE: { bg: "bg-emerald-500/15 animate-pulse", text: "text-emerald-400", border: "border-emerald-500/40" },
  COMPLETED: { bg: "bg-green-500/10", text: "text-green-400", border: "border-green-500/30" },
  PARTIAL: { bg: "bg-amber-500/10", text: "text-amber-400", border: "border-amber-500/30" },
  ABANDONED: { bg: "bg-red-500/10", text: "text-red-400", border: "border-red-500/30" },
};

const DEFAULT_STATUS_STYLE = { bg: "bg-surface", text: "text-foreground", border: "border-border" };

const DEVIATION_REASONS = [
  { value: "TRAIN_DELAY", label: "Train Delay" },
  { value: "MACHINE_DELAY", label: "Machine Failure / Delay" },
  { value: "CREW_UNAVAILABLE", label: "Crew Unavailable" },
  { value: "WEATHER", label: "Adverse Weather" },
  { value: "EMERGENCY_DEFECT", label: "Emergency Track Defect" },
  { value: "RESOURCE_CONFLICT", label: "Resource Conflict" },
  { value: "BLOCK_OVERRUN", label: "Block Overrun" },
  { value: "OTHER", label: "Other Operational Reason" },
] as const;

// -- KPI Card Component --------------------------------------------------------
function KPICard({
  icon: Icon,
  label,
  value,
  unit,
  subtext,
  note,
  trend,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  unit?: string;
  subtext?: string;
  note?: string;
  trend?: "up" | "down" | "neutral";
}) {
  return (
    <div className="flex flex-col justify-between gap-2 rounded-lg border border-border bg-surface p-4 shadow-sm transition-all hover:border-border-strong">
      <div className="flex items-center justify-between">
        <span className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
          <Icon className="size-4 shrink-0 text-primary" aria-hidden />
          {label}
        </span>
        {trend && (
          <span className="flex items-center text-xs">
            {trend === "down" ? (
              <TrendingDown className="size-4 text-emerald-400" />
            ) : trend === "up" ? (
              <TrendingUp className="size-4 text-amber-400" />
            ) : null}
          </span>
        )}
      </div>

      <div className="my-1">
        <div className="flex items-baseline gap-1.5">
          <span className="text-3xl font-bold tabular-nums text-foreground">{value}</span>
          {unit && <span className="text-sm font-medium text-muted-foreground">{unit}</span>}
        </div>
        {subtext && <p className="mt-0.5 text-xs font-semibold text-foreground/80">{subtext}</p>}
      </div>

      {note && <p className="text-[11px] text-muted-foreground">{note}</p>}
    </div>
  );
}

// -- Record Outcome Dialog -----------------------------------------------------
function RecordOutcomeDialog({
  initialData,
  onClose,
  onSuccess,
}: {
  initialData?: Partial<ExecutionRecord> | ActiveExecution | null;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const isEditing = !!initialData?.execution_id;

  const [blockId, setBlockId] = useState(initialData?.block_id || "RB-1042");
  const [sectionId, setSectionId] = useState(initialData?.section_id || "SEC_021");
  const [department, setDepartment] = useState(initialData?.department || "Engineering+TRD");
  
  const [plannedStart, setPlannedStart] = useState(
    initialData?.planned_start || "2026-09-24T10:00:00"
  );
  const [plannedEnd, setPlannedEnd] = useState(
    initialData?.planned_end || "2026-09-24T12:00:00"
  );
  
  const [actualStart, setActualStart] = useState(
    initialData?.actual_start || (initialData as ActiveExecution)?.started_at || "2026-09-24T10:08:00"
  );
  const [actualEnd, setActualEnd] = useState(
    initialData?.actual_end || "2026-09-24T12:35:00"
  );
  
  const [completedTasks, setCompletedTasks] = useState<number>(
    initialData?.completed_tasks ?? 4
  );
  const [totalTasks, setTotalTasks] = useState<number>(
    initialData?.total_tasks ?? 5
  );
  
  const [machineUsed, setMachineUsed] = useState(
    initialData?.machine_id || "BCM-02"
  );
  const [crewUsed, setCrewUsed] = useState(
    initialData?.crew_id || "Crew-17"
  );
  
  const [status, setStatus] = useState<ExecutionRecord["status"]>(
    (initialData?.status as ExecutionRecord["status"]) || "COMPLETED"
  );
  
  const [deviationReason, setDeviationReason] = useState<string>(
    initialData?.deviation_reason || ""
  );
  
  const [notes, setNotes] = useState(initialData?.notes || "");
  const [submitting, setSubmitting] = useState(false);

  // Auto-calculate completion %
  const completionPercentage = useMemo(() => {
    if (!totalTasks || totalTasks <= 0) return 0;
    return Math.round((completedTasks / totalTasks) * 100);
  }, [completedTasks, totalTasks]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const payload: RecordOutcomePayload = {
        block_id: blockId,
        section_id: sectionId,
        department,
        planned_start: plannedStart,
        planned_end: plannedEnd,
        actual_start: actualStart,
        actual_end: actualEnd,
        completed_tasks: completedTasks,
        total_tasks: totalTasks,
        machine_id: machineUsed,
        crew_id: crewUsed,
        status,
        deviation_reason: deviationReason || undefined,
        notes: notes.trim() || undefined,
        recorded_by: "controller",
      };

      if (isEditing && initialData?.execution_id) {
        await executionApi.updateExecutionRecord(initialData.execution_id, payload);
        toast.success("Outcome Updated", {
          description: `Updated record for ${blockId}.`,
        });
      } else {
        await executionApi.createExecutionRecord(payload);
        toast.success("Outcome Recorded", {
          description: `Successfully logged outcome for ${blockId} (${status}).`,
        });
      }
      onSuccess();
    } catch {
      toast.error("Saving Failed", {
        description: "Could not save outcome record. Please verify backend connection.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-xs"
      role="dialog"
      aria-modal="true"
      aria-label="Record Field Outcome Dialog"
    >
      <div className="w-full max-w-xl max-h-[90vh] overflow-y-auto rounded-xl border border-border bg-background shadow-2xl">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-border px-6 py-4 bg-surface/50">
          <div>
            <h3 className="text-base font-bold text-foreground">
              {isEditing ? "Edit Execution Outcome" : "Record Field Outcome"}
            </h3>
            <p className="font-mono text-xs text-muted-foreground mt-0.5">
              Block ID: {blockId} &middot; Closed-Loop Feedback Entry
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded p-1 text-muted-foreground hover:bg-surface hover:text-foreground"
          >
            &times;
          </button>
        </div>

        {/* Modal Body */}
        <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4 px-6 py-5">
          {/* Row 1: Block ID, Section, Department */}
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Block ID
              </label>
              <input
                type="text"
                value={blockId}
                onChange={(e) => setBlockId(e.target.value)}
                required
                className="w-full font-mono rounded border border-border bg-surface px-3 py-1.5 text-xs text-foreground focus:border-primary focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Section ID
              </label>
              <input
                type="text"
                value={sectionId}
                onChange={(e) => setSectionId(e.target.value)}
                required
                className="w-full font-mono rounded border border-border bg-surface px-3 py-1.5 text-xs text-foreground focus:border-primary focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Department
              </label>
              <input
                type="text"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                required
                className="w-full rounded border border-border bg-surface px-3 py-1.5 text-xs text-foreground focus:border-primary focus:outline-none"
              />
            </div>
          </div>

          {/* Row 2: Status Selection */}
          <div>
            <label className="block text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
              Execution Status
            </label>
            <div className="grid grid-cols-5 gap-2">
              {(["SCHEDULED", "ACTIVE", "COMPLETED", "PARTIAL", "ABANDONED"] as const).map((st) => {
                const styleObj = STATUS_STYLES[st] ?? DEFAULT_STATUS_STYLE;
                return (
                  <button
                    type="button"
                    key={st}
                    onClick={() => setStatus(st)}
                    className={`rounded border px-2 py-2 text-center text-xs font-semibold transition-all ${
                      status === st
                        ? `${styleObj.bg} ${styleObj.text} ${styleObj.border} ring-1 ring-primary/40`
                        : "border-border bg-surface text-muted-foreground hover:bg-surface-2"
                    }`}
                  >
                    {st}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Row 3: Actual Timestamps */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Actual Start Time
              </label>
              <input
                type="text"
                value={actualStart}
                onChange={(e) => setActualStart(e.target.value)}
                placeholder="2026-09-24T10:08:00"
                className="w-full font-mono rounded border border-border bg-surface px-3 py-1.5 text-xs text-foreground focus:border-primary focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Actual End Time
              </label>
              <input
                type="text"
                value={actualEnd}
                onChange={(e) => setActualEnd(e.target.value)}
                placeholder="2026-09-24T12:35:00"
                className="w-full font-mono rounded border border-border bg-surface px-3 py-1.5 text-xs text-foreground focus:border-primary focus:outline-none"
              />
            </div>
          </div>

          {/* Row 4: Tasks Completed / Total & Progress */}
          <div className="grid grid-cols-3 gap-3 items-end">
            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Completed Tasks
              </label>
              <input
                type="number"
                min="0"
                value={completedTasks}
                onChange={(e) => setCompletedTasks(parseInt(e.target.value) || 0)}
                className="w-full rounded border border-border bg-surface px-3 py-1.5 text-xs text-foreground focus:border-primary focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Total Tasks
              </label>
              <input
                type="number"
                min="1"
                value={totalTasks}
                onChange={(e) => setTotalTasks(parseInt(e.target.value) || 1)}
                className="w-full rounded border border-border bg-surface px-3 py-1.5 text-xs text-foreground focus:border-primary focus:outline-none"
              />
            </div>

            <div className="rounded border border-border bg-surface/50 p-2 text-center">
              <span className="block text-[10px] uppercase font-semibold text-muted-foreground">Completion</span>
              <span className="text-sm font-bold text-primary">{completionPercentage}%</span>
            </div>
          </div>

          {/* Row 5: Machine & Crew */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Machine Used
              </label>
              <input
                type="text"
                value={machineUsed}
                onChange={(e) => setMachineUsed(e.target.value)}
                placeholder="BCM-02, CSM-04"
                className="w-full font-mono rounded border border-border bg-surface px-3 py-1.5 text-xs text-foreground focus:border-primary focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Crew Used
              </label>
              <input
                type="text"
                value={crewUsed}
                onChange={(e) => setCrewUsed(e.target.value)}
                placeholder="Crew-17"
                className="w-full font-mono rounded border border-border bg-surface px-3 py-1.5 text-xs text-foreground focus:border-primary focus:outline-none"
              />
            </div>
          </div>

          {/* Row 6: Deviation Reason */}
          <div>
            <label className="block text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Deviation / Variance Reason
            </label>
            <select
              value={deviationReason}
              onChange={(e) => setDeviationReason(e.target.value)}
              className="w-full rounded border border-border bg-surface px-3 py-1.5 text-xs text-foreground focus:border-primary focus:outline-none"
            >
              <option value="">-- Select Reason (if delayed or partial) --</option>
              {DEVIATION_REASONS.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>

          {/* Row 7: Notes */}
          <div>
            <label className="block text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Notes & Observations
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Detail any site constraints, speed restrictions imposed, or machine breakdown reasons..."
              rows={3}
              className="w-full resize-none rounded border border-border bg-surface px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none"
            />
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-end gap-3 border-t border-border pt-4 mt-6">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="rounded border border-border bg-surface px-4 py-2 text-xs font-medium text-foreground transition-colors hover:bg-surface-2 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="rounded bg-primary px-4 py-2 text-xs font-semibold text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              {submitting ? "Saving Outcome..." : "Save Outcome"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// -- Main Page Component -------------------------------------------------------
export function ExecutionMonitorPage() {
  const [records, setRecords] = useState<ExecutionRecord[]>([]);
  const [active, setActive] = useState<ActiveExecution[]>([]);
  const [kpis, setKpis] = useState<ExecutionKPIs | null>(null);
  const [analytics, setAnalytics] = useState<ExecutionAnalyticsData | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Search
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [dialogTarget, setDialogTarget] = useState<Partial<ExecutionRecord> | ActiveExecution | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [recordsRes, activeRes, kpisRes, analyticsRes] = await Promise.all([
        executionApi.getExecutionRecords(),
        executionApi.getActiveExecutions(),
        executionApi.getExecutionKPIs(),
        executionApi.getExecutionAnalytics(),
      ]);

      setRecords(recordsRes.records ?? []);
      setActive(activeRes.active_executions ?? []);
      setKpis(kpisRes);
      setAnalytics(analyticsRes);
    } catch {
      setError("Backend connection offline — displaying simulated closed-loop feedback data.");
      // Fallback data if backend is unreachable
      setKpis({
        total_executions: 23,
        avg_variance: -8.0,
        overrun_rate: 12.0,
        block_wastage: 6.5,
        block_wastage_formatted: "6.5%",
        note: "Under planned duration",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchData();
  }, []);

  const handleOpenNewDialog = () => {
    setDialogTarget({
      block_id: `RB-${1050 + records.length}`,
      section_id: "SEC_021",
      department: "Engineering+TRD",
      planned_start: "2026-09-24T10:00:00",
      planned_end: "2026-09-24T12:00:00",
      actual_start: "2026-09-24T10:08:00",
      actual_end: "2026-09-24T12:35:00",
      completed_tasks: 4,
      total_tasks: 5,
      machine_id: "BCM-02",
      crew_id: "Crew-17",
      status: "COMPLETED",
    });
    setIsDialogOpen(true);
  };

  const handleOpenEditDialog = (record: ExecutionRecord | ActiveExecution) => {
    setDialogTarget(record);
    setIsDialogOpen(true);
  };

  const handleDialogSuccess = () => {
    setIsDialogOpen(false);
    setDialogTarget(null);
    void fetchData();
  };

  // Filter records
  const filteredRecords = useMemo(() => {
    return records.filter((r) => {
      const matchesStatus = statusFilter === "ALL" || r.status === statusFilter;
      const matchesSearch =
        searchQuery === "" ||
        r.block_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.section_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.department.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (r.deviation_reason && r.deviation_reason.toLowerCase().includes(searchQuery.toLowerCase()));
      return matchesStatus && matchesSearch;
    });
  }, [records, statusFilter, searchQuery]);

  // Color constants for Recharts
  const PIE_COLORS = ["#22c55e", "#38bdf8", "#f59e0b", "#ef4444", "#a855f7"];

  const avgVar = kpis?.avg_variance ?? -8;
  const isAvgVarNegative = avgVar < 0;

  return (
    <div className="flex h-full flex-col overflow-auto bg-background text-foreground">
      {/* Header */}
      <PageHeader
        title="Field Execution Monitor"
        description="Closed-loop maintenance feedback system — planned vs. actual outcomes, variance analysis, and learning for future planning"
        crumbs={[{ label: "Execution" }, { label: "Monitor & Feedback" }]}
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={() => void fetchData()}
              className="flex items-center gap-1.5 rounded border border-border bg-surface px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-surface-2"
            >
              <RefreshCw className={`size-3.5 ${loading ? "animate-spin" : ""}`} aria-hidden /> Refresh
            </button>
            <button
              onClick={handleOpenNewDialog}
              className="flex items-center gap-1.5 rounded bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground transition-opacity hover:opacity-90"
            >
              <Plus className="size-3.5" aria-hidden /> Record Outcome
            </button>
          </div>
        }
      />

      <div className="flex-1 space-y-6 p-4 md:p-6">
        {error && (
          <div className="flex items-center gap-2 rounded border border-warn/40 bg-warn/10 px-4 py-3 text-xs font-medium text-warn">
            <AlertTriangle className="size-4 shrink-0" />
            {error}
          </div>
        )}

        {/* SECTION 1: Closed-Loop KPI Cards */}
        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <BarChart3 className="size-4 text-primary" /> Closed-Loop Feedback KPIs
            </h2>
            <span className="text-[11px] text-muted-foreground">Updated from field outcomes</span>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {/* Card 1: Total Executions */}
            <KPICard
              icon={ListChecks}
              label="Total Executions"
              value={kpis?.total_executions ?? 23}
              subtext="Recorded field outcomes"
              note="Closed-loop records in dataset"
            />

            {/* Card 2: Average Variance */}
            <KPICard
              icon={Clock}
              label="Average Variance"
              value={`${avgVar > 0 ? "+" : ""}${avgVar} min`}
              subtext={isAvgVarNegative ? "Under planned duration" : "Over planned duration"}
              note={
                isAvgVarNegative
                  ? "Average execution finished earlier than planned"
                  : "Average execution exceeded planned window"
              }
              trend={isAvgVarNegative ? "down" : "up"}
            />

            {/* Card 3: Overrun Rate */}
            <KPICard
              icon={BarChart3}
              label="Overrun Rate"
              value={kpis?.overrun_rate !== undefined ? `${kpis.overrun_rate}%` : "12%"}
              subtext="Executions exceeding plan"
              note="Formula: (actual > planned) / total_executions"
              trend={(kpis?.overrun_rate ?? 12) > 15 ? "up" : "neutral"}
            />

            {/* Card 4: Block Wastage */}
            <KPICard
              icon={Gauge}
              label="Block Wastage"
              value={
                kpis?.block_wastage !== null && kpis?.block_wastage !== undefined
                  ? `${kpis.block_wastage}%`
                  : kpis?.block_wastage_formatted || "6.5%"
              }
              subtext="Unused possession time"
              note={
                kpis?.block_wastage === null
                  ? "No completed possession records"
                  : "Formula: (unused_min / planned_min)"
              }
            />
          </div>
        </section>

        {/* SECTION 2: Active Possessions */}
        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <Activity className="size-4 text-emerald-400" /> Active Field Possessions
            </h2>
            <span className="text-[11px] font-mono text-emerald-400">
              {active.length} ACTIVE IN FIELD
            </span>
          </div>

          {loading ? (
            <div className="rounded-lg border border-border bg-surface p-8 text-center text-xs text-muted-foreground">
              Loading active possessions...
            </div>
          ) : active.length === 0 ? (
            <div className="flex flex-col items-center gap-2 rounded-lg border border-border bg-surface py-10 text-center">
              <CheckCircle2 className="size-8 text-emerald-500/80" aria-hidden />
              <p className="text-sm font-semibold text-foreground">No Active Possessions</p>
              <p className="text-xs text-muted-foreground">
                There are no live maintenance blocks currently executing in the corridor.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              {active.map((ex) => (
                <div
                  key={ex.block_id}
                  className="flex flex-col justify-between gap-3 rounded-lg border border-emerald-500/30 bg-surface p-4 shadow-sm"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-base font-bold text-foreground">{ex.block_id}</span>
                        <span className="rounded border border-emerald-500/40 bg-emerald-500/10 px-2 py-0.5 font-mono text-[10px] font-bold text-emerald-400 animate-pulse">
                          ACTIVE
                        </span>
                      </div>
                      <p className="mt-0.5 text-xs text-muted-foreground">
                        Section: <span className="font-semibold text-foreground">{ex.section_id}</span> &middot; Dept:{" "}
                        <span className="font-semibold text-foreground">{ex.department || "Engineering+TRD"}</span>
                      </p>
                    </div>

                    <button
                      onClick={() => handleOpenEditDialog(ex)}
                      className="rounded border border-border bg-surface-2 px-2.5 py-1 text-xs font-semibold text-foreground transition-colors hover:border-primary hover:bg-primary/10"
                    >
                      Record Outcome
                    </button>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs border-t border-border/50 pt-3">
                    <div>
                      <span className="text-[11px] text-muted-foreground block">Planned Window</span>
                      <span className="font-mono text-foreground font-medium">
                        {ex.planned_start ? ex.planned_start.slice(11, 16) : "10:00"} &ndash;{" "}
                        {ex.planned_end ? ex.planned_end.slice(11, 16) : "12:00"}
                      </span>
                    </div>

                    <div>
                      <span className="text-[11px] text-muted-foreground block">Actual Start</span>
                      <span className="font-mono text-emerald-400 font-medium">
                        {ex.actual_start ? ex.actual_start.slice(11, 16) : ex.started_at || "10:08"} &ndash; ongoing
                      </span>
                    </div>

                    <div>
                      <span className="text-[11px] text-muted-foreground block">Crew Assigned</span>
                      <span className="font-mono text-foreground">{ex.crew_id || "Crew-17"}</span>
                    </div>

                    <div>
                      <span className="text-[11px] text-muted-foreground block">Machine Deployed</span>
                      <span className="font-mono text-foreground">{ex.machine_id || "BCM-02"}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* SECTION 3: Execution Analytics Charts */}
        {analytics && (
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                <PieChartIcon className="size-4 text-primary" /> Closed-Loop Execution Analytics
              </h2>
              <span className="text-[11px] text-muted-foreground">Historical Variance & Disruption Patterns</span>
            </div>

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              {/* Chart 1: Planned vs Actual Duration */}
              <div className="rounded-lg border border-border bg-surface p-4">
                <h3 className="text-xs font-bold text-foreground mb-1">1. Planned vs Actual Duration</h3>
                <p className="text-[11px] text-muted-foreground mb-3">Comparing duration (minutes) across recent executions</p>
                <div className="h-60 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={analytics.planned_vs_actual} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                      <XAxis dataKey="block_id" stroke="#71717a" tick={{ fontSize: 10 }} interval={0} angle={-45} textAnchor="end" />
                      <YAxis stroke="#71717a" tick={{ fontSize: 10 }} />
                      <Tooltip contentStyle={{ backgroundColor: "#18181b", borderColor: "#27272a", fontSize: "12px" }} />
                      <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "10px" }} />
                      <Bar dataKey="planned_duration" name="Planned (min)" fill="#38bdf8" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="actual_duration" name="Actual (min)" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Chart 2: Execution Status Distribution */}
              <div className="rounded-lg border border-border bg-surface p-4">
                <h3 className="text-xs font-bold text-foreground mb-1">2. Execution Status Distribution</h3>
                <p className="text-[11px] text-muted-foreground mb-3">Share of completed, partial, abandoned & active blocks</p>
                <div className="h-60 w-full flex items-center justify-center">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={analytics.status_distribution}
                        dataKey="count"
                        nameKey="status"
                        cx="50%"
                        cy="50%"
                        outerRadius={75}
                        innerRadius={40}
                        paddingAngle={4}
                        label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                      >
                        {analytics.status_distribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={{ backgroundColor: "#18181b", borderColor: "#27272a", fontSize: "12px" }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Chart 3: Variance Trend */}
              <div className="rounded-lg border border-border bg-surface p-4">
                <h3 className="text-xs font-bold text-foreground mb-1">3. Variance Trend Over Time</h3>
                <p className="text-[11px] text-muted-foreground mb-3">Average daily duration variance (minutes)</p>
                <div className="h-60 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={analytics.variance_trend} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                      <XAxis dataKey="date" stroke="#71717a" tick={{ fontSize: 10 }} />
                      <YAxis stroke="#71717a" tick={{ fontSize: 10 }} />
                      <Tooltip contentStyle={{ backgroundColor: "#18181b", borderColor: "#27272a", fontSize: "12px" }} />
                      <Line type="monotone" dataKey="avg_variance" name="Avg Variance (min)" stroke="#22c55e" strokeWidth={2} dot={{ r: 4 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Chart 4: Top Deviation Reasons */}
              <div className="rounded-lg border border-border bg-surface p-4">
                <h3 className="text-xs font-bold text-foreground mb-1">4. Top Deviation & Delay Reasons</h3>
                <p className="text-[11px] text-muted-foreground mb-3">Primary root causes behind block overrun & partial execution</p>
                <div className="h-60 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={analytics.top_deviation_reasons} layout="vertical" margin={{ top: 10, right: 10, left: 30, bottom: 10 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                      <XAxis type="number" stroke="#71717a" tick={{ fontSize: 10 }} />
                      <YAxis type="category" dataKey="reason" stroke="#71717a" tick={{ fontSize: 10 }} width={100} />
                      <Tooltip contentStyle={{ backgroundColor: "#18181b", borderColor: "#27272a", fontSize: "12px" }} />
                      <Bar dataKey="count" name="Incidents" fill="#ef4444" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* SECTION 4: Recent Execution Table */}
        <section className="space-y-3">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <ListChecks className="size-4 text-primary" /> Execution Records Table
            </h2>

            {/* Filter and Search controls */}
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-2.5 top-2 size-3.5 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Search Block, Section..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="rounded border border-border bg-surface pl-8 pr-3 py-1 text-xs text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none w-48"
                />
              </div>

              <div className="flex items-center gap-1.5 rounded border border-border bg-surface px-2.5 py-1 text-xs text-muted-foreground">
                <Filter className="size-3.5" />
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="bg-transparent text-xs text-foreground focus:outline-none cursor-pointer"
                >
                  <option value="ALL">All Statuses</option>
                  <option value="COMPLETED">Completed</option>
                  <option value="PARTIAL">Partial</option>
                  <option value="ABANDONED">Abandoned</option>
                  <option value="ACTIVE">Active</option>
                  <option value="SCHEDULED">Scheduled</option>
                </select>
              </div>
            </div>
          </div>

          {/* Table */}
          <div className="overflow-hidden rounded-lg border border-border bg-surface shadow-xs">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-foreground">
                <thead className="border-b border-border bg-surface-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                  <tr>
                    <th className="px-4 py-3">Block ID</th>
                    <th className="px-4 py-3">Section</th>
                    <th className="px-4 py-3">Department</th>
                    <th className="px-4 py-3">Planned</th>
                    <th className="px-4 py-3">Actual</th>
                    <th className="px-4 py-3">Variance</th>
                    <th className="px-4 py-3">Completion %</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Reason</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {filteredRecords.length === 0 ? (
                    <tr>
                      <td colSpan={10} className="px-4 py-8 text-center text-xs text-muted-foreground">
                        No execution records found.
                      </td>
                    </tr>
                  ) : (
                    filteredRecords.map((r) => {
                      const style = STATUS_STYLES[r.status] ?? DEFAULT_STATUS_STYLE;
                      const varVal = r.variance_minutes;
                      const varFormatted =
                        varVal === undefined || varVal === null
                          ? "--"
                          : varVal > 0
                          ? `+${varVal} min`
                          : `${varVal} min`;

                      const plannedStr = `${r.planned_start ? r.planned_start.slice(11, 16) : "10:00"}-${
                        r.planned_end ? r.planned_end.slice(11, 16) : "12:00"
                      }`;
                      const actualStr = r.actual_start
                        ? `${r.actual_start.slice(11, 16)}-${r.actual_end ? r.actual_end.slice(11, 16) : "ongoing"}`
                        : "--";

                      return (
                        <tr key={r.execution_id || r.block_id} className="transition-colors hover:bg-surface-2/70">
                          <td className="px-4 py-3 font-mono font-semibold text-foreground">{r.block_id}</td>
                          <td className="px-4 py-3 font-mono text-muted-foreground">{r.section_id}</td>
                          <td className="px-4 py-3 text-muted-foreground">{r.department}</td>
                          <td className="px-4 py-3 font-mono text-xs">{plannedStr}</td>
                          <td className="px-4 py-3 font-mono text-xs">{actualStr}</td>
                          <td className="px-4 py-3 font-mono text-xs font-semibold">
                            {varVal !== undefined && varVal !== null ? (
                              <span className={varVal > 0 ? "text-amber-400" : varVal < 0 ? "text-emerald-400" : "text-muted-foreground"}>
                                {varFormatted}
                              </span>
                            ) : (
                              <span className="text-muted-foreground">--</span>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <div className="h-1.5 w-16 overflow-hidden rounded-full bg-surface-2">
                                <div
                                  className="h-full bg-primary"
                                  style={{ width: `${Math.min(100, r.completion_percentage || 0)}%` }}
                                />
                              </div>
                              <span className="font-mono text-xs text-muted-foreground">
                                {r.completion_percentage !== undefined ? `${Math.round(r.completion_percentage)}%` : "0%"}
                              </span>
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <span className={`inline-flex rounded border px-2 py-0.5 font-mono text-[10px] font-bold ${style.bg} ${style.text} ${style.border}`}>
                              {r.status}
                            </span>
                          </td>
                          <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                            {r.deviation_reason ? (
                              <span className="rounded bg-surface-2 px-1.5 py-0.5 text-[10px] font-semibold text-foreground">
                                {r.deviation_reason}
                              </span>
                            ) : (
                              "--"
                            )}
                          </td>
                          <td className="px-4 py-3 text-right">
                            <button
                              onClick={() => handleOpenEditDialog(r)}
                              className="rounded border border-border bg-surface px-2 py-1 text-[11px] font-medium text-foreground transition-colors hover:border-primary hover:bg-surface-2"
                            >
                              Edit Outcome
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* SECTION 5: Closed-Loop Lifecycle Bottom Banner */}
        <div className="rounded-lg border border-primary/30 bg-primary/5 p-4 text-center">
          <p className="font-mono text-xs font-semibold tracking-wide text-primary">
            AI RECOMMENDS &rarr; CONTROLLER APPROVES &rarr; FIELD EXECUTES &rarr; ACTUAL OUTCOME RECORDED &rarr; FEEDBACK TO FUTURE PLANNING
          </p>
          <p className="mt-1 text-[11px] text-muted-foreground">
            Closed-Loop Maintenance Lifecycle &middot; Continuous learning calibrates future corridor section buffers automatically.
          </p>
        </div>
      </div>

      {/* Record Outcome Dialog Modal */}
      {isDialogOpen && (
        <RecordOutcomeDialog
          initialData={dialogTarget}
          onClose={() => {
            setIsDialogOpen(false);
            setDialogTarget(null);
          }}
          onSuccess={handleDialogSuccess}
        />
      )}
    </div>
  );
}
