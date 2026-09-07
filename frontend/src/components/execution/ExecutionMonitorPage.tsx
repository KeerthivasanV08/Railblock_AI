/**
 * Execution Monitor Page
 *
 * Shows active field possessions and closed-loop feedback metrics from
 * the backend ExecutionMonitor and ExecutionFeedbackEngine services.
 *
 * Data: DERIVED — computed from planned vs. actual execution records in
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

// ── KPI tile ────────────────────────────────────────────────────────────────
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

// ── Main page ────────────────────────────────────────────────────────────────
export function ExecutionMonitorPage() {
  const [active, setActive] = useState<ActiveExecution[]>([]);
  const [metrics, setMetrics] = useState<ExecutionMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
      setError("Backend unavailable — execution data not loaded.");
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

  return (
    <div className="flex h-full flex-col overflow-auto">
      <PageHeader
        title="Execution Monitor"
        description="Closed-loop feedback — planned vs. actual field possession data · DERIVED from execution records"
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

        {/* ── Closed-loop KPIs ── */}
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
                value={metrics.avg_duration_variance_min?.toFixed(1) ?? "—"}
                unit="min"
                note="Positive = overrun"
              />
              <KPITile
                icon={BarChart3}
                label="Overrun Rate"
                value={metrics.overrun_rate_pct?.toFixed(1) ?? "—"}
                unit="%"
                note="Executions exceeding planned window"
              />
              <KPITile
                icon={Gauge}
                label="Block Wastage"
                value={metrics.block_wastage_pct?.toFixed(1) ?? "—"}
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

        {/* ── Active executions ── */}
        <section>
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Active Field Possessions
          </h2>
          {loading ? (
            <p className="py-8 text-center text-sm text-muted-foreground">Loading…</p>
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
                <div
                  key={ex.block_id}
                  className="flex items-center justify-between gap-4 rounded border border-border bg-surface px-4 py-3"
                >
                  <div className="flex items-center gap-3">
                    <Activity className="size-4 text-ok animate-pulse" aria-hidden />
                    <div>
                      <p className="font-mono text-sm font-semibold text-foreground">
                        {ex.block_id}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {ex.section_id}
                        {ex.department && ` · ${ex.department}`}
                        {ex.started_at && ` · Started ${ex.started_at}`}
                      </p>
                    </div>
                  </div>
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
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
