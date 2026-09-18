/**
 * Execution Monitor Page
 *
 * Shows active field possessions and closed-loop feedback metrics from
 * the backend ExecutionMonitor and ExecutionFeedbackEngine services.
 *
 * Data: DERIVED -- computed from planned vs. actual execution records in
 *       execution_outcomes.csv and weekly_block_plan.csv.
 */

import { useEffect, useState } from "react";
import {
  Activity,
  BarChart3,
  CheckCircle2,
  Clock,
  Gauge,
  ListChecks,
  RefreshCw,
} from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/common/PageHeader";
import { executionApi, type ActiveExecution, type ExecutionMetrics } from "@/api";

// -- KPI tile ------------------------------------------------------------------
function KPITile({
  icon: Icon,
  label,
  value,
  unit,
  note,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  unit?: string;
  note?: string;
}) {
  return (
    <div className="flex flex-col gap-1 rounded-lg border border-border bg-surface p-4">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Icon className="size-3.5 shrink-0" aria-hidden />
        {label}
      </div>
      <p className="text-2xl font-bold tabular-nums text-foreground">
        {value}
        {unit && <span className="ml-1 text-sm font-normal text-muted-foreground">{unit}</span>}
      </p>
      {note && <p className="text-[11px] text-muted-foreground">{note}</p>}
    </div>
  );
}

// -- Outcome completion status options -----------------------------------------
const COMPLETION_STATUSES = [
  { value: "COMPLETED", label: "Completed", description: "All planned work finished within window" },
  { value: "PARTIAL", label: "Partial", description: "Work done but not fully completed" },
  { value: "ABANDONED", label: "Abandoned", description: "Block cancelled or could not proceed" },
] as const;

type CompletionStatus = "COMPLETED" | "PARTIAL" | "ABANDONED";

// -- Record Outcome Dialog -----------------------------------------------------
function RecordOutcomeDialog({
  execution,
  onClose,
  onSuccess,
}: {
  execution: ActiveExecution;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [status, setStatus] = useState<CompletionStatus>("COMPLETED");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const trimmedNotes = notes.trim();
      await executionApi.recordOutcome(execution.block_id, {
        completion_status: status,
        recorded_by: "Field Operator",
        ...(trimmedNotes ? { notes: trimmedNotes } : {}),
      });
      toast.success("Outcome Recorded", {
        description: `Block ${execution.block_id} marked as ${status}.`,
      });
      onSuccess();
    } catch {
      toast.error("Record Outcome Failed", {
        description: "Could not reach backend. Verify the server is running and retry.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      role="dialog"
      aria-modal="true"
      aria-label={`Record outcome for block ${execution.block_id}`}
    >
      <div className="w-full max-w-md rounded-lg border border-border bg-background shadow-xl">
        {/* Header */}
        <div className="border-b border-border px-5 py-4">
          <p className="text-sm font-semibold text-foreground">Record Field Outcome</p>
          <p className="mt-0.5 font-mono text-xs text-muted-foreground">
            Block {execution.block_id} &middot; {execution.section_id}
            {execution.department ? ` \u00b7 ${execution.department}` : ""}
          </p>
        </div>

        <div className="space-y-4 px-5 py-4">
          {/* Completion status */}
          <div>
            <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              Completion Status
            </p>
            <div className="space-y-2">
              {COMPLETION_STATUSES.map((opt) => (
                <label
                  key={opt.value}
                  className={`flex cursor-pointer items-start gap-3 rounded border px-3 py-2.5 transition-colors ${
                    status === opt.value
                      ? "border-primary bg-primary/5"
                      : "border-border bg-surface hover:border-border-strong"
                  }`}
                >
                  <input
                    type="radio"
                    name="completion_status"
                    value={opt.value}
                    checked={status === opt.value}
                    onChange={() => setStatus(opt.value)}
                    className="mt-0.5 shrink-0 accent-primary"
                  />
                  <span>
                    <span className="block text-xs font-semibold text-foreground">{opt.label}</span>
                    <span className="block text-[11px] text-muted-foreground">
                      {opt.description}
                    </span>
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Notes */}
          <div>
            <label
              htmlFor="outcome-notes"
              className="mb-1.5 block text-[11px] font-semibold uppercase tracking-wide text-muted-foreground"
            >
              Notes (optional)
            </label>
            <textarea
              id="outcome-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Describe any issues, delays, or observations..."
              rows={3}
              className="w-full resize-none rounded border border-border bg-surface px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 border-t border-border px-5 py-3">
          <button
            onClick={onClose}
            disabled={submitting}
            className="rounded border border-border bg-surface px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-surface-2 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            id={`record-outcome-submit-${execution.block_id}`}
            onClick={() => void handleSubmit()}
            disabled={submitting}
            className="rounded bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {submitting ? "Recording..." : "Record Outcome"}
          </button>
        </div>
      </div>
    </div>
  );
}

// -- Active Execution Card -----------------------------------------------------
function ActiveExecutionCard({
  ex,
  onRecordOutcome,
}: {
  ex: ActiveExecution;
  onRecordOutcome: (ex: ActiveExecution) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-4 rounded border border-border bg-surface px-4 py-3">
      <div className="flex min-w-0 items-center gap-3">
        <Activity className="size-4 shrink-0 animate-pulse text-ok" aria-hidden />
        <div className="min-w-0">
          <p className="font-mono text-sm font-semibold text-foreground">{ex.block_id}</p>
          <p className="truncate text-xs text-muted-foreground">
            {ex.section_id}
            {ex.department && ` \u00b7 ${ex.department}`}
            {ex.started_at && ` \u00b7 Started ${ex.started_at}`}
          </p>
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-4">
        <div className="text-right">
          {ex.elapsed_min !== undefined && (
            <p className="text-sm font-semibold tabular-nums text-foreground">
              {ex.elapsed_min} min elapsed
            </p>
          )}
          {ex.planned_duration_min !== undefined && (
            <p className="text-xs text-muted-foreground">
              of {ex.planned_duration_min} min planned
            </p>
          )}
        </div>

        {/* Human-in-the-loop: record actual outcome */}
        <button
          id={`record-outcome-${ex.block_id}`}
          onClick={() => onRecordOutcome(ex)}
          className="rounded border border-border bg-surface-2 px-2.5 py-1.5 text-[11px] font-medium text-foreground transition-colors hover:border-border-strong hover:bg-surface"
          title="Record actual field outcome for this block"
        >
          Record Outcome
        </button>
      </div>
    </div>
  );
}

// -- Main page ----------------------------------------------------------------
export function ExecutionMonitorPage() {
  const [active, setActive] = useState<ActiveExecution[]>([]);
  const [metrics, setMetrics] = useState<ExecutionMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [outcomeTarget, setOutcomeTarget] = useState<ActiveExecution | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [execRes, metricsRes] = await Promise.all([
        executionApi.getActiveExecutions(),
        executionApi.getExecutionMetrics(),
      ]);
      setActive(execRes.active_executions ?? []);
      setMetrics(metricsRes.metrics ?? null);
    } catch {
      setError("Backend unavailable -- execution data not loaded.");
      toast.error("Execution Monitor", {
        description: "Could not reach backend. Showing empty state.",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchData();
  }, []);

  const handleOutcomeSuccess = () => {
    setOutcomeTarget(null);
    // Refresh so the completed execution drops off the active list
    void fetchData();
  };

  return (
    <div className="flex h-full flex-col overflow-auto">
      <PageHeader
        title="Execution Monitor"
        description="Closed-loop feedback -- planned vs. actual field possession data. DERIVED from execution records"
        crumbs={[{ label: "Execution" }, { label: "Monitor" }]}
        actions={
          <button
            id="execution-refresh"
            onClick={() => void fetchData()}
            className="flex items-center gap-1.5 rounded border border-border bg-surface px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-surface-2"
          >
            <RefreshCw className="size-3.5" aria-hidden /> Refresh
          </button>
        }
      />

      <div className="flex-1 space-y-6 p-4">
        {error && (
          <div className="rounded border border-warn/40 bg-warn/5 px-4 py-3 text-sm text-warn">
            {error}
          </div>
        )}

        {/* Closed-loop KPIs */}
        {metrics && (
          <section>
            <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Closed-Loop Feedback KPIs
            </h2>
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              <KPITile
                icon={ListChecks}
                label="Total Executions"
                value={metrics.total_executions}
                note="Recorded field outcomes"
              />
              <KPITile
                icon={Clock}
                label="Avg Duration Variance"
                value={metrics.avg_duration_variance_min?.toFixed(1) ?? "--"}
                unit="min"
                note="Positive = overrun"
              />
              <KPITile
                icon={BarChart3}
                label="Overrun Rate"
                value={metrics.overrun_rate_pct?.toFixed(1) ?? "--"}
                unit="%"
                note="Executions exceeding planned window"
              />
              <KPITile
                icon={Gauge}
                label="Block Wastage"
                value={metrics.block_wastage_pct?.toFixed(1) ?? "--"}
                unit="%"
                note="Unused possession time"
              />
            </div>
            {typeof metrics.sections_with_learned_buffers === "number" && (
              <p className="mt-2 text-[11px] text-muted-foreground">
                <span className="font-semibold text-foreground">
                  {metrics.sections_with_learned_buffers}
                </span>{" "}
                corridor sections have learned buffer modifiers applied.
              </p>
            )}
          </section>
        )}

        {/* Active executions */}
        <section>
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Active Field Possessions
          </h2>
          {loading ? (
            <p className="py-8 text-center text-sm text-muted-foreground">Loading...</p>
          ) : active.length === 0 ? (
            <div className="flex flex-col items-center gap-3 rounded-lg border border-border bg-surface py-12 text-center">
              <CheckCircle2 className="size-8 text-ok" aria-hidden />
              <p className="text-sm font-medium text-foreground">No active possessions</p>
              <p className="text-xs text-muted-foreground">
                No maintenance blocks are currently active in the field.
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {active.map((ex) => (
                <ActiveExecutionCard
                  key={ex.block_id}
                  ex={ex}
                  onRecordOutcome={setOutcomeTarget}
                />
              ))}
            </div>
          )}
          <p className="mt-3 text-[11px] text-muted-foreground">
            Use <strong>Record Outcome</strong> to submit planned-vs-actual field execution data.
            AI RECOMMENDS &rarr; HUMAN APPROVES (Planner) &rarr; FIELD EXECUTES &rarr; OUTCOME RECORDED HERE.
          </p>
        </section>
      </div>

      {/* Record Outcome Dialog -- rendered at root level to avoid layout clipping */}
      {outcomeTarget && (
        <RecordOutcomeDialog
          execution={outcomeTarget}
          onClose={() => setOutcomeTarget(null)}
          onSuccess={handleOutcomeSuccess}
        />
      )}
    </div>
  );
}
