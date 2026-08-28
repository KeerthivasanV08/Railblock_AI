import { useEffect } from "react";
import { toast } from "sonner";
import { AlertTriangle, Check, PlayCircle } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/States";
import { Button } from "@/components/ui/button";
import { ImpactBadge, StatusBadge } from "@/components/common/StatusBadge";
import { cn } from "@/lib/utils";
import { toHHMM } from "@/utils/dateUtils";
import { useDisruptionStore } from "@/stores/disruptionStore";
import { usePlannerStore } from "@/stores/plannerStore";

export function DisruptionDetailPage({ eventId }: { eventId: string }) {
  const event = useDisruptionStore((s) => s.disruptions.find((e) => e.event_id === eventId));
  const options = useDisruptionStore((s) => s.optionsByEvent[eventId]);
  const selectedOption = useDisruptionStore((s) => s.selectedOptionByEvent[eventId]);
  const simulation = useDisruptionStore((s) => s.simulationByEvent[eventId]);
  const { ensureOptions, selectOption, simulate, applyReschedule } = useDisruptionStore();
  const block = usePlannerStore((s) =>
    s.blocks.find((b) => b.block_id === event?.affected_block_id),
  );

  useEffect(() => {
    if (eventId) ensureOptions(eventId);
  }, [eventId, ensureOptions]);

  if (!event) {
    return (
      <div className="flex h-full flex-col">
        <PageHeader
          title="Disruption not found"
          crumbs={[{ label: "Self-Healing Console", to: "/disruptions" }, { label: eventId }]}
        />
        <EmptyState className="m-6" title={`No disruption event ${eventId}`} />
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col overflow-auto">
      <PageHeader
        title={`${event.type} — ${event.event_id}`}
        description={event.location}
        crumbs={[{ label: "Self-Healing Console", to: "/disruptions" }, { label: event.event_id }]}
        badge={
          <StatusBadge
            label={event.status}
            tone={
              event.status === "Open" ? "crit" : event.status === "Rescheduled" ? "ok" : "neutral"
            }
          />
        }
      />

      <div className="grid flex-1 grid-cols-1 gap-4 p-4 lg:grid-cols-[1fr_1fr]">
        <div className="space-y-4">
          <div className="rounded-md border border-crit/30 bg-crit/5 p-4">
            <p className="flex items-center gap-1.5 text-sm font-semibold text-crit">
              <AlertTriangle className="size-4" aria-hidden /> {event.type.toUpperCase()} DETECTED
            </p>
            <dl className="mt-2 grid grid-cols-2 gap-y-1.5 text-xs">
              {event.train_number && <Row label="Train" value={event.train_number} />}
              {event.delay_min > 0 && <Row label="Delay" value={`${event.delay_min} min`} />}
              <Row label="Location" value={event.location} />
              <Row label="Affected Block" value={event.affected_block_id ?? "—"} />
              <Row
                label="Original Window"
                value={
                  block
                    ? `${toHHMM(block.start_min)}–${toHHMM(block.start_min + block.duration_min)}`
                    : event.original_window
                }
              />
              <Row label="Available Window" value={event.available_window} />
            </dl>
          </div>

          {simulation && (
            <div className="rounded-md border border-border bg-surface p-4">
              <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                Simulation result
              </p>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="rounded border border-border bg-surface-2 p-2.5">
                  <p className="text-[10px] uppercase text-muted-foreground">Before</p>
                  <p className="mt-1 font-mono font-semibold">
                    {toHHMM(simulation.before.start_min)}–
                    {toHHMM(simulation.before.start_min + simulation.before.duration_min)}
                  </p>
                </div>
                <div className="rounded border border-ok/30 bg-ok/10 p-2.5">
                  <p className="text-[10px] uppercase text-muted-foreground">After</p>
                  <p className="mt-1 font-mono font-semibold">
                    {toHHMM(simulation.after.start_min)}–
                    {toHHMM(simulation.after.start_min + simulation.after.duration_min)}
                  </p>
                </div>
              </div>
              <dl className="mt-3 grid grid-cols-2 gap-y-1.5 text-xs">
                <Row
                  label="Train Delay"
                  value={`+${simulation.option.added_train_delay_min} min`}
                />
                <Row label="Maintenance" value={simulation.option.maintenance_impact} />
                <Row label="Resources" value={simulation.option.resource_impact} />
                <Row label="Conflict" value="Resolved" />
              </dl>
            </div>
          )}
        </div>

        <div className="space-y-3">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            AI Alternatives (RL Rescheduler)
          </p>
          {(options ?? []).map((opt, i) => (
            <button
              key={opt.id}
              onClick={() => selectOption(event.event_id, opt.id)}
              className={cn(
                "block w-full rounded-md border p-3 text-left transition-colors",
                selectedOption === opt.id
                  ? "border-primary ring-1 ring-primary"
                  : "border-border hover:border-border-strong",
              )}
            >
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-foreground">
                  Option {String.fromCharCode(65 + i)} — {opt.label}
                </p>
                <ImpactBadge impact={opt.train_impact} />
              </div>
              <div className="mt-1.5 grid grid-cols-2 gap-1 text-[11px] text-muted-foreground">
                <span>Utilization {opt.utilization}%</span>
                <span>Confidence {opt.confidence}%</span>
                <span>Maintenance: {opt.maintenance_impact}</span>
                <span>Resources: {opt.resource_impact}</span>
              </div>
            </button>
          ))}

          <div className="flex gap-2 pt-1">
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5"
              disabled={!selectedOption}
              onClick={() => simulate(event.event_id)}
            >
              <PlayCircle className="size-3.5" aria-hidden /> Simulate
            </Button>
            <Button
              size="sm"
              className="gap-1.5 bg-ok text-ok-foreground hover:bg-ok/90"
              disabled={!selectedOption || event.status !== "Open"}
              onClick={() => {
                applyReschedule(event.event_id);
                toast.success("AI rescheduling simulation applied.", {
                  description: `${event.event_id} rescheduled successfully.`,
                });
              }}
            >
              <Check className="size-3.5" aria-hidden /> Apply Reschedule
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="text-right font-medium text-foreground">{value}</dd>
    </>
  );
}
