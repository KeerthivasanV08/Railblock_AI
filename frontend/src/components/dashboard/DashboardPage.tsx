import { useMemo } from "react";
import { useNavigate } from "@tanstack/react-router";
import {
  AlertOctagon,
  CalendarClock,
  CheckCircle2,
  ClipboardList,
  Gauge,
  Layers,
  Sparkles,
  Timer,
  TrainFront,
  Wrench,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { KPICard } from "@/components/common/KPICard";
import { CorridorMap } from "@/components/map/CorridorMap";
import { DepartmentBadge } from "@/components/common/DomainBadges";
import { ImpactBadge, StatusBadge } from "@/components/common/StatusBadge";
import { useTaskStore } from "@/stores/taskStore";
import { usePlannerStore } from "@/stores/plannerStore";
import { useRecommendationStore } from "@/stores/recommendationStore";
import { useDisruptionStore } from "@/stores/disruptionStore";
import { useOperationsStore } from "@/stores/operationsStore";
import { useResourceStore } from "@/stores/resourceStore";
import { toHHMM } from "@/utils/dateUtils";

export function DashboardPage() {
  const navigate = useNavigate();
  const tasks = useTaskStore((s) => s.tasks);
  const blocks = usePlannerStore((s) => s.blocks);
  const selectBlock = usePlannerStore((s) => s.select);
  const machines = useResourceStore((s) => s.machines);
  const recommendations = useRecommendationStore((s) => s.recommendations);
  const disruptions = useDisruptionStore((s) => s.disruptions);
  const trains = useOperationsStore((s) => s.trains);

  const criticalTasks = useMemo(
    () => tasks.filter((t) => t.severity === "A" && t.status !== "Completed"),
    [tasks],
  );
  const overdueTasks = useMemo(
    () => tasks.filter((t) => t.overdue_days > 0 && t.status !== "Completed"),
    [tasks],
  );
  const activeBlocks = useMemo(
    () => blocks.filter((b) => ["APPROVED", "SCHEDULED", "ACTIVE"].includes(b.status)),
    [blocks],
  );
  const integratedBlocks = useMemo(() => blocks.filter((b) => b.lane === "Integrated"), [blocks]);
  const avgUtilization = useMemo(
    () =>
      blocks.length ? Math.round(blocks.reduce((s, b) => s + b.utilization, 0) / blocks.length) : 0,
    [blocks],
  );
  const pendingApprovals = useMemo(
    () =>
      blocks.filter((b) => b.status === "PENDING APPROVAL" || b.status === "AI RECOMMENDED").length,
    [blocks],
  );
  const delayedTrains = useMemo(
    () =>
      trains
        .filter((t) => t.delay_min > 0)
        .sort((a, b) => b.delay_min - a.delay_min)
        .slice(0, 5),
    [trains],
  );
  const upcomingBlocks = useMemo(
    () => [...blocks].sort((a, b) => a.start_min - b.start_min).slice(0, 5),
    [blocks],
  );
  const criticalMaintenance = useMemo(() => criticalTasks.slice(0, 5), [criticalTasks]);
  const aiInsights = useMemo(() => recommendations.slice(0, 4), [recommendations]);
  const openDisruptions = useMemo(
    () => disruptions.filter((d) => d.status === "Open"),
    [disruptions],
  );

  return (
    <div className="h-full overflow-auto bg-background">
      <PageHeader
        title="Railway Operations Command Centre"
        description="New Delhi – Kanpur Corridor · Multi-Department Integrated Maintenance & Real-time Decision Support"
        crumbs={[{ label: "Command" }, { label: "Command Dashboard" }]}
        badge={
          <span className="inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary/5 px-2.5 py-0.5 text-[11px] font-medium text-primary">
            <ShieldCheck className="size-3.5 text-primary" />
            SYNTHETIC DEMO ENVIRONMENT
          </span>
        }
      />

      <div className="space-y-5 p-4 lg:p-6">
        {/* KPI Strip */}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 xl:grid-cols-8">
          <KPICard
            label="Asset Availability"
            value="94.2%"
            icon={Gauge}
            trendLabel="+1.2%"
            trendDirection="up"
            tone="ok"
            statusLabel="Operational"
            onClick={() => navigate({ to: "/analytics" })}
          />
          <KPICard
            label="Active Blocks"
            value={String(activeBlocks.length)}
            icon={Layers}
            trendLabel="+2 Today"
            trendDirection="up"
            tone="info"
            statusLabel="Active"
            onClick={() => navigate({ to: "/planner" })}
          />
          <KPICard
            label="Critical Defects"
            value={String(criticalTasks.length)}
            icon={AlertOctagon}
            trendLabel="Sev A"
            trendDirection="down"
            tone="crit"
            statusLabel="Priority"
            onClick={() => navigate({ to: "/tasks" })}
          />
          <KPICard
            label="Overdue Tasks"
            value={overdueTasks.length.toLocaleString()}
            icon={Timer}
            trendLabel="-2.1%"
            trendDirection="down"
            tone="warn"
            statusLabel="Attention"
            onClick={() => navigate({ to: "/tasks" })}
          />
          <KPICard
            label="Block Utilization"
            value={`${avgUtilization}%`}
            icon={Gauge}
            trendLabel="+4.5%"
            trendDirection="up"
            tone="ok"
            statusLabel="Optimized"
            onClick={() => navigate({ to: "/planner" })}
          />
          <KPICard
            label="Integrated Blocks"
            value={String(integratedBlocks.length)}
            icon={Sparkles}
            trendLabel="Multi-Dept"
            trendDirection="up"
            tone="ai"
            statusLabel="AI Cluster"
            onClick={() => navigate({ to: "/planner" })}
          />
          <KPICard
            label="Potential Saved"
            value={`${integratedBlocks.length * 65} min`}
            icon={CalendarClock}
            trendLabel="This week"
            trendDirection="up"
            tone="ok"
            statusLabel="Simulated"
            onClick={() => navigate({ to: "/analytics" })}
          />
          <KPICard
            label="Pending Approvals"
            value={String(pendingApprovals)}
            icon={ClipboardList}
            trendLabel="Controller"
            trendDirection="flat"
            tone="warn"
            statusLabel="Review Needed"
            onClick={() => navigate({ to: "/recommendations" })}
          />
        </div>

        {/* Centerpiece Map */}
        <CorridorMap
          trains={trains}
          blocks={blocks}
          criticalTasks={criticalTasks}
          machines={machines}
          onSelect={(sel) => {
            if (sel.kind === "block") {
              selectBlock(sel.id);
              navigate({ to: "/planner" });
            }
            if (sel.kind === "task") {
              navigate({ to: "/tasks/$taskId", params: { taskId: sel.id } });
            }
            if (sel.kind === "train" || sel.kind === "station" || sel.kind === "machine") {
              navigate({ to: "/live" });
            }
          }}
          heightClass="h-[360px]"
        />

        {/* Operational Overview Panels Grid */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2 xl:grid-cols-3">
          <Panel
            title="Upcoming Maintenance Blocks"
            icon={<Layers className="size-4 text-primary" />}
            onSeeAll={() => navigate({ to: "/planner" })}
          >
            {upcomingBlocks.map((b) => (
              <button
                key={`dash-block-${b.block_id}`}
                onClick={() => {
                  selectBlock(b.block_id);
                  navigate({ to: "/planner" });
                }}
                className="flex w-full items-center justify-between gap-2 rounded-md border border-border/80 bg-surface px-3 py-2 text-left text-xs transition-colors hover:border-border-strong hover:bg-surface-2"
              >
                <div className="flex flex-col">
                  <span className="font-mono font-bold text-foreground">{b.block_id}</span>
                  <span className="text-[11px] text-muted-foreground">
                    {b.lane} · {toHHMM(b.start_min)}–{toHHMM(b.start_min + b.duration_min)}
                  </span>
                </div>
                <StatusBadge
                  label={b.status}
                  tone={
                    b.status === "APPROVED" ? "ok" : b.status === "AI RECOMMENDED" ? "ai" : "warn"
                  }
                />
              </button>
            ))}
          </Panel>

          <Panel
            title="Train Delay Alerts"
            icon={<TrainFront className="size-4 text-warn" />}
            onSeeAll={() => navigate({ to: "/live" })}
          >
            {delayedTrains.length === 0 ? (
              <div className="flex items-center gap-2 py-4 text-xs text-ok">
                <span className="size-2 rounded-full bg-ok" />
                All corridor trains operating on schedule.
              </div>
            ) : (
              delayedTrains.map((t, idx) => (
                <button
                  key={`dash-delay-${t.train_number}-${idx}`}
                  onClick={() => navigate({ to: "/live" })}
                  className="flex w-full items-center justify-between gap-2 rounded-md border border-border/80 bg-surface px-3 py-2 text-left text-xs transition-colors hover:border-border-strong hover:bg-surface-2"
                >
                  <div className="flex flex-col">
                    <span className="font-semibold text-foreground">
                      {t.name} ({t.train_number})
                    </span>
                    <span className="text-[11px] text-muted-foreground">
                      {t.category} · Near Km {t.km.toFixed(1)}
                    </span>
                  </div>
                  <span
                    className={`font-mono font-bold px-2 py-0.5 rounded ${t.delay_min > 20 ? "bg-crit/10 text-crit" : "bg-warn/15 text-warn-foreground"}`}
                  >
                    +{t.delay_min} min
                  </span>
                </button>
              ))
            )}
          </Panel>

          <Panel
            title="Critical Maintenance Backlog"
            icon={<AlertOctagon className="size-4 text-crit" />}
            onSeeAll={() => navigate({ to: "/tasks" })}
          >
            {criticalMaintenance.map((t) => (
              <button
                key={`dash-crit-${t.task_id}`}
                onClick={() => navigate({ to: "/tasks/$taskId", params: { taskId: t.task_id } })}
                className="flex w-full items-center justify-between gap-2 rounded-md border border-border/80 bg-surface px-3 py-2 text-left text-xs transition-colors hover:border-border-strong hover:bg-surface-2"
              >
                <div className="flex flex-col truncate pr-2">
                  <span className="truncate font-mono font-semibold text-foreground">
                    {t.task_id} · {t.defect}
                  </span>
                  <span className="text-[11px] text-muted-foreground">
                    {t.location_label} · Overdue {t.overdue_days}d
                  </span>
                </div>
                <DepartmentBadge department={t.department} />
              </button>
            ))}
          </Panel>

          <Panel
            title="AI Planning Insights"
            icon={<Sparkles className="size-4 text-ai" />}
            onSeeAll={() => navigate({ to: "/recommendations" })}
          >
            {aiInsights.map((r) => (
              <button
                key={`dash-rec-${r.recommendation_id}`}
                onClick={() =>
                  navigate({
                    to: "/recommendations/$recommendationId",
                    params: { recommendationId: r.recommendation_id },
                  })
                }
                className="flex w-full items-center justify-between gap-2 rounded-md border border-ai/25 bg-ai/5 px-3 py-2 text-left text-xs transition-colors hover:bg-ai/10"
              >
                <div className="flex flex-col">
                  <span className="font-mono font-bold text-foreground">Block {r.block_id}</span>
                  <span className="text-[11px] text-muted-foreground">
                    {r.departments.join(" + ")} · Score {r.priority_score}
                  </span>
                </div>
                <ImpactBadge impact={r.train_impact} />
              </button>
            ))}
          </Panel>

          <Panel
            title="Corridor Disruption Triage"
            icon={<AlertTriangle className="size-4 text-crit" />}
            onSeeAll={() => navigate({ to: "/disruptions" })}
          >
            {openDisruptions.length === 0 ? (
              <p className="py-4 text-xs text-muted-foreground">
                Zero active corridor disruptions.
              </p>
            ) : (
              openDisruptions.map((d) => (
                <button
                  key={`dash-disrupt-${d.event_id}`}
                  onClick={() =>
                    navigate({ to: "/disruptions/$eventId", params: { eventId: d.event_id } })
                  }
                  className="flex w-full items-center justify-between gap-2 rounded-md border border-crit/25 bg-crit/5 px-3 py-2 text-left text-xs transition-colors hover:bg-crit/10"
                >
                  <div className="flex flex-col">
                    <span className="font-semibold text-foreground">
                      {d.type} {d.train_number ? `· Train ${d.train_number}` : ""}
                    </span>
                    <span className="text-[11px] text-muted-foreground">
                      {d.location} · {d.severity}
                    </span>
                  </div>
                  <span className="rounded bg-crit/15 px-2 py-0.5 font-bold text-crit">Triage</span>
                </button>
              ))
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}

function Panel({
  title,
  icon,
  onSeeAll,
  children,
}: {
  title: string;
  icon?: React.ReactNode;
  onSeeAll: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col rounded-xl border border-border bg-surface shadow-xs">
      <div className="flex items-center justify-between border-b border-border/70 bg-surface-2/60 px-4 py-2.5">
        <div className="flex items-center gap-2">
          {icon}
          <span className="text-xs font-bold uppercase tracking-wider text-foreground">
            {title}
          </span>
        </div>
        <button
          onClick={onSeeAll}
          className="flex items-center gap-1 text-[11px] font-semibold text-primary transition-colors hover:underline"
        >
          View all
          <ArrowRight className="size-3" />
        </button>
      </div>
      <div className="space-y-2 p-3">{children}</div>
    </div>
  );
}
