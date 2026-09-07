import { useEffect, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { ArrowRight, Brain, History, MapPin, Sparkles } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/States";
import { DepartmentBadge, PriorityBadge, SeverityBadge } from "@/components/common/DomainBadges";
import { TaskStatusBadge } from "@/components/common/StatusBadge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { sectionById } from "@/data/sections";
import { explainPriority } from "@/utils/scoring";
import { useTaskStore } from "@/stores/taskStore";
import { usePlannerStore } from "@/stores/plannerStore";
import { tasksApi, type TaskPriorityResponse } from "@/api";
import type { PriorityBreakdown } from "@/types";

const BREAKDOWN_LABELS: Record<keyof PriorityBreakdown, string> = {
  severity: "Severity",
  overdue_risk: "Overdue Risk",
  traffic_impact: "Traffic Impact",
  asset_criticality: "Asset Criticality",
  deferral_risk: "Deferral Risk",
};

const BREAKDOWN_MAX: Record<keyof PriorityBreakdown, number> = {
  severity: 40,
  overdue_risk: 30,
  traffic_impact: 16,
  asset_criticality: 10,
  deferral_risk: 12,
};

export function TaskDetailPage({ taskId }: { taskId: string }) {
  const task = useTaskStore((s) => s.tasks.find((t) => t.task_id === taskId));
  const setBlockSelection = usePlannerStore((s) => s.select);
  const navigate = useNavigate();

  const [backendPriority, setBackendPriority] = useState<TaskPriorityResponse | null>(null);
  const [loadingBackend, setLoadingBackend] = useState(false);

  useEffect(() => {
    if (!taskId) return;
    let isMounted = true;
    setLoadingBackend(true);
    tasksApi
      .getTaskPriority(taskId)
      .then((data) => {
        if (isMounted) setBackendPriority(data);
      })
      .catch(() => {
        // Graceful fallback to local priority calculation
      })
      .finally(() => {
        if (isMounted) setLoadingBackend(false);
      });
    return () => {
      isMounted = false;
    };
  }, [taskId]);

  if (!task) {
    return (
      <div className="flex h-full flex-col">
        <PageHeader
          title="Task not found"
          crumbs={[{ label: "Maintenance Tasks", to: "/tasks" }, { label: taskId }]}
        />
        <EmptyState
          className="m-6"
          title={`No task with ID ${taskId}`}
          description="It may have been reassigned or removed from the synthetic dataset."
        />
      </div>
    );
  }

  const section = sectionById(task.section_id);

  return (
    <div className="flex h-full flex-col overflow-auto">
      <PageHeader
        title={task.task_id}
        description={`${task.defect} · ${task.location_label}`}
        crumbs={[{ label: "Maintenance Tasks", to: "/tasks" }, { label: task.task_id }]}
        badge={<TaskStatusBadge status={task.status} />}
        actions={
          task.recommended_block_id && (
            <Button
              size="sm"
              className="gap-1.5"
              onClick={() => {
                setBlockSelection(task.recommended_block_id);
                navigate({ to: "/planner" });
              }}
            >
              View Recommended Block <ArrowRight className="size-3.5" aria-hidden />
            </Button>
          )
        }
      />

      <div className="grid flex-1 grid-cols-1 gap-4 p-4 lg:grid-cols-[1.1fr_1fr]">
        <div className="space-y-4">
          <div className="rounded-md border border-border bg-surface p-4">
            <div className="flex items-center justify-between">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                AI Priority Score
              </p>
              <span
                className={`rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
                  backendPriority
                    ? "bg-ok/10 text-ok border border-ok/20"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                {backendPriority ? "Backend MDPS Engine" : "Heuristic Rule Base"}
              </span>
            </div>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="font-mono text-4xl font-bold tabular-nums text-foreground">
                {backendPriority?.priority_score ?? task.priority_score}
              </span>
              <span className="text-sm text-muted-foreground">/ 100</span>
              <PriorityBadge
                score={backendPriority?.priority_score ?? task.priority_score}
                className="ml-2"
              />
              {backendPriority?.priority_band && (
                <span className="ml-auto font-mono text-xs font-semibold uppercase text-primary">
                  Band: {backendPriority.priority_band}
                </span>
              )}
            </div>

            <div className="mt-4 space-y-2.5">
              {(Object.keys(task.priority_breakdown) as (keyof PriorityBreakdown)[]).map((key) => {
                const value =
                  backendPriority?.components && key in backendPriority.components
                    ? (backendPriority.components as Record<string, number>)[key] ??
                      task.priority_breakdown[key]
                    : task.priority_breakdown[key];
                const max = BREAKDOWN_MAX[key];
                return (
                  <div key={key}>
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-foreground">{BREAKDOWN_LABELS[key]}</span>
                      <span className="font-mono text-muted-foreground">{value}</span>
                    </div>
                    <div className="mt-1 h-1.5 rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-primary"
                        style={{ width: `${Math.min(100, (value / max) * 100)}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="rounded-md border border-ai/30 bg-ai/5 p-4 space-y-2.5">
            <div className="flex items-center justify-between">
              <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-ai">
                <Sparkles className="size-3.5" aria-hidden />
                {backendPriority?.explanation ? "MDPS Safety & AI Justification" : "AI Explanation"}
              </p>
              {backendPriority?.model_version && (
                <span className="font-mono text-[10px] text-muted-foreground">
                  v{backendPriority.model_version}
                </span>
              )}
            </div>

            <p className="text-sm leading-relaxed text-foreground">
              {backendPriority?.explanation?.summary ?? explainPriority(task)}
            </p>

            {backendPriority?.explanation?.risk_drivers &&
              backendPriority.explanation.risk_drivers.length > 0 && (
                <div className="pt-1">
                  <p className="text-[11px] font-medium text-muted-foreground mb-1">Risk Drivers:</p>
                  <div className="flex flex-wrap gap-1.5">
                    {backendPriority.explanation.risk_drivers.map((driver, i) => (
                      <span
                        key={i}
                        className="rounded bg-ai/10 border border-ai/20 px-2 py-0.5 text-[11px] text-foreground font-mono"
                      >
                        {driver}
                      </span>
                    ))}
                  </div>
                </div>
              )}

            {backendPriority?.explanation?.safety_justification && (
              <div className="mt-2 rounded bg-surface/80 border border-border p-2.5 text-xs text-muted-foreground">
                <span className="font-semibold text-foreground">Safety Protocol: </span>
                {backendPriority.explanation.safety_justification}
              </div>
            )}
          </div>

          <div className="rounded-md border border-border bg-surface p-4">
            <p className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              <History className="size-3.5" aria-hidden /> Defect History
            </p>
            <div className="space-y-2">
              {task.history.map((h, i) => (
                <div key={i} className="flex gap-2 text-xs">
                  <span className="w-20 shrink-0 font-mono text-muted-foreground">{h.date}</span>
                  <span className="text-foreground">{h.note}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-md border border-border bg-surface p-4">
            <p className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              <MapPin className="size-3.5" aria-hidden /> Location &amp; Asset
            </p>
            <dl className="grid grid-cols-2 gap-y-2 text-xs">
              <Row label="Section" value={task.section_id} />
              <Row label="Chainage" value={task.location_label} />
              <Row label="Department" value={<DepartmentBadge department={task.department} />} />
              <Row label="Source System" value={task.source_system} />
              <Row label="Asset" value={task.asset} />
              <Row label="Asset Criticality" value={`${task.asset_criticality}/100`} />
              <Row label="Severity" value={<SeverityBadge severity={task.severity} />} />
              <Row
                label="Traffic Density (section)"
                value={`${section?.traffic_density ?? "—"}%`}
              />
              {task.mast_number && <Row label="Mast Number" value={task.mast_number} />}
              {task.signal_id && <Row label="Signal ID" value={task.signal_id} />}
            </dl>
          </div>

          <Separator />

          <div className="rounded-md border border-border bg-surface p-4">
            <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              Planning
            </p>
            <dl className="grid grid-cols-2 gap-y-2 text-xs">
              <Row
                label="Overdue"
                value={task.overdue_days > 0 ? `${task.overdue_days} days` : "On schedule"}
              />
              <Row label="Previous Deferrals" value={String(task.previous_deferrals)} />
              <Row label="Required Duration" value={`${task.required_duration_min} min`} />
              <Row label="Required Resource" value={task.required_resource} />
              <Row
                label="Recommended Block"
                value={task.recommended_block_id ?? "Not yet clustered"}
              />
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <>
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="text-right font-medium text-foreground">{value}</dd>
    </>
  );
}
