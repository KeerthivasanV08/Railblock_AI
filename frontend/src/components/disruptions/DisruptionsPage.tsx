import { useNavigate } from "@tanstack/react-router";
import { AlertTriangle, ChevronRight, Clock } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/States";
import { StatusBadge } from "@/components/common/StatusBadge";
import { useDisruptionStore } from "@/stores/disruptionStore";

const STATUS_TONE = { Open: "crit", Rescheduled: "ok", Dismissed: "neutral" } as const;
const SEVERITY_TONE = { Critical: "crit", Warning: "warn", Info: "info" } as const;

export function DisruptionsPage() {
  const disruptions = useDisruptionStore((s) => s.disruptions);
  const navigate = useNavigate();

  return (
    <div className="flex h-full flex-col overflow-auto">
      <PageHeader
        title="Disruption / Self-Healing Console"
        description="RL Rescheduler v1.0-demo — detects disruptions and proposes self-healing reschedule alternatives"
        crumbs={[{ label: "Disruption" }, { label: "Self-Healing Console" }]}
      />
      <div className="flex-1 space-y-3 p-4">
        {disruptions.length === 0 ? (
          <EmptyState
            title="No active disruptions"
            description="The corridor is currently operating without detected disruptions."
            icon={AlertTriangle}
          />
        ) : (
          disruptions.map((d) => (
            <button
              key={d.event_id}
              onClick={() =>
                navigate({ to: "/disruptions/$eventId", params: { eventId: d.event_id } })
              }
              className="flex w-full items-center justify-between gap-3 rounded-md border border-border bg-surface p-4 text-left transition-colors hover:border-border-strong hover:bg-surface-2"
            >
              <div className="flex items-start gap-3">
                <AlertTriangle
                  className={`mt-0.5 size-4 shrink-0 ${d.severity === "Critical" ? "text-crit" : "text-warn"}`}
                  aria-hidden
                />
                <div>
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-semibold text-foreground">
                      {d.type.toUpperCase()} {d.train_number ? `— TRAIN ${d.train_number}` : ""}
                    </p>
                    <StatusBadge label={d.status} tone={STATUS_TONE[d.status]} />
                    <StatusBadge label={d.severity} tone={SEVERITY_TONE[d.severity]} />
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {d.location} ·{" "}
                    {d.affected_block_id
                      ? `Affects block ${d.affected_block_id}`
                      : "No linked block"}
                    {d.delay_min > 0 && ` · Delay ${d.delay_min} min`}
                  </p>
                  <p className="mt-1 flex items-center gap-1 text-[11px] text-muted-foreground">
                    <Clock className="size-3" aria-hidden /> Detected {d.detected_at}
                  </p>
                </div>
              </div>
              <ChevronRight className="size-4 shrink-0 text-muted-foreground" aria-hidden />
            </button>
          ))
        )}
      </div>
    </div>
  );
}
