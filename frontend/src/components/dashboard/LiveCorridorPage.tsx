import { useEffect, useMemo, useState } from "react";
import { Pause, Play, AlertTriangle, TrainFront, Wrench, ShieldAlert, CloudRain } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { CorridorMap } from "@/components/map/CorridorMap";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AvailabilityBadge, ImpactBadge } from "@/components/common/StatusBadge";
import { useOperationsStore, type SimSpeed } from "@/stores/operationsStore";
import { usePlannerStore } from "@/stores/plannerStore";
import { useResourceStore } from "@/stores/resourceStore";
import { useDisruptionStore } from "@/stores/disruptionStore";
import { seasonalApi, type SectionSeasonalRisk } from "@/api/seasonalApi";
import { toHHMM } from "@/utils/dateUtils";

export function LiveCorridorPage() {
  const trains = useOperationsStore((s) => s.trains);
  const playing = useOperationsStore((s) => s.playing);
  const speed = useOperationsStore((s) => s.speed);
  const play = useOperationsStore((s) => s.play);
  const pause = useOperationsStore((s) => s.pause);
  const setSpeed = useOperationsStore((s) => s.setSpeed);
  const tick = useOperationsStore((s) => s.tick);
  const initLiveStream = useOperationsStore((s) => s.initLiveStream);

  const [weatherRisks, setWeatherRisks] = useState<SectionSeasonalRisk[]>([]);

  useEffect(() => {
    seasonalApi.getAllSectionRisks().then(setWeatherRisks).catch(() => {});
  }, []);

  const rawBlocks = usePlannerStore((s) => s.blocks);
  const blocks = useMemo(
    () => rawBlocks.filter((b) => ["APPROVED", "SCHEDULED", "ACTIVE"].includes(b.status)),
    [rawBlocks],
  );

  const machines = useResourceStore((s) => s.machines);
  const crews = useResourceStore((s) => s.crews);
  const disruptions = useDisruptionStore((s) => s.disruptions);

  useEffect(() => {
    initLiveStream();
  }, [initLiveStream]);

  useEffect(() => {
    if (!playing) return;
    const intervalMs = 1500 / speed;
    const id = setInterval(() => tick(), intervalMs);
    return () => clearInterval(id);
  }, [playing, speed, tick]);

  const delayed = useMemo(
    () => [...trains].filter((t) => t.delay_min > 0).sort((a, b) => b.delay_min - a.delay_min),
    [trains],
  );

  const activeMaintenance = useMemo(
    () => blocks.filter((b) => b.status === "ACTIVE" || b.status === "SCHEDULED"),
    [blocks],
  );

  const openDisruptions = useMemo(
    () => disruptions.filter((d) => d.status === "Open"),
    [disruptions],
  );

  return (
    <div className="h-full overflow-auto bg-background">
      <PageHeader
        title="Live Corridor Command Monitor"
        description="Real-time geographic train movements, active blocks, and resource tracking"
        crumbs={[{ label: "Command" }, { label: "Live Corridor" }]}
        badge={
          <span className="inline-flex items-center gap-1.5 rounded-full border border-info/30 bg-info/10 px-2.5 py-0.5 text-[11px] font-medium text-info">
            <span className="relative flex size-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-info opacity-75" />
              <span className="relative inline-flex size-2 rounded-full bg-info" />
            </span>
            SIMULATED LIVE FEED
          </span>
        }
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5 border-border bg-surface font-medium text-foreground hover:bg-surface-2"
              onClick={playing ? pause : play}
            >
              {playing ? (
                <Pause className="size-3.5 text-warn" aria-hidden />
              ) : (
                <Play className="size-3.5 text-ok" aria-hidden />
              )}
              {playing ? "Pause Stream" : "Resume Stream"}
            </Button>
            <Tabs value={String(speed)} onValueChange={(v) => setSpeed(Number(v) as SimSpeed)}>
              <TabsList className="h-8 border border-border bg-surface-2">
                <TabsTrigger
                  value="0.5"
                  className="text-xs font-mono data-[state=active]:bg-surface data-[state=active]:text-foreground"
                >
                  0.5x
                </TabsTrigger>
                <TabsTrigger
                  value="1"
                  className="text-xs font-mono data-[state=active]:bg-surface data-[state=active]:text-foreground"
                >
                  1x
                </TabsTrigger>
                <TabsTrigger
                  value="2"
                  className="text-xs font-mono data-[state=active]:bg-surface data-[state=active]:text-foreground"
                >
                  2x
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        }
      />

      <div className="space-y-4 p-4 lg:p-6">
        <CorridorMap
          trains={trains}
          blocks={blocks}
          machines={machines}
          heightClass="h-[400px]"
          className="shadow-sm"
        />

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          <Panel
            title="Scheduled & Active Blocks"
            icon={<Wrench className="size-3.5 text-primary" />}
            count={blocks.length}
          >
            {blocks.length === 0 ? (
              <p className="py-2 text-xs text-muted-foreground">No active blocks scheduled.</p>
            ) : (
              blocks.slice(0, 6).map((b) => (
                <div
                  key={`block-${b.block_id}`}
                  className="flex items-center justify-between rounded border border-border/80 bg-surface px-3 py-2 text-xs hover:border-border-strong"
                >
                  <div className="flex flex-col">
                    <span className="font-mono font-semibold text-foreground">{b.block_id}</span>
                    <span className="text-[11px] text-muted-foreground">
                      {b.lane} · {toHHMM(b.start_min)}–{toHHMM(b.start_min + b.duration_min)}
                    </span>
                  </div>
                  <span className="rounded bg-surface-2 px-2 py-0.5 font-mono text-[11px] font-medium text-foreground">
                    {b.status}
                  </span>
                </div>
              ))
            )}
          </Panel>

          <Panel
            title="Active Train Delays"
            icon={<TrainFront className="size-3.5 text-warn" />}
            count={delayed.length}
          >
            {delayed.length === 0 ? (
              <div className="flex items-center gap-2 py-3 text-xs text-ok">
                <span className="size-2 rounded-full bg-ok" />
                All corridor trains operating on schedule.
              </div>
            ) : (
              delayed.slice(0, 6).map((t, idx) => (
                <div
                  key={`delay-${t.train_number}-${idx}`}
                  className="flex items-center justify-between rounded border border-border/80 bg-surface px-3 py-2 text-xs hover:border-border-strong"
                >
                  <div className="flex flex-col">
                    <span className="font-medium text-foreground">
                      {t.name} ({t.train_number})
                    </span>
                    <span className="text-[11px] text-muted-foreground">
                      {t.category} · Near Km {t.km.toFixed(1)}
                    </span>
                  </div>
                  <span
                    className={`font-mono font-semibold px-2 py-0.5 rounded ${t.delay_min > 25 ? "bg-crit/10 text-crit" : "bg-warn/15 text-warn-foreground"}`}
                  >
                    +{t.delay_min}m late
                  </span>
                </div>
              ))
            )}
          </Panel>

          <Panel
            title="Disruption Alerts"
            icon={<AlertTriangle className="size-3.5 text-crit" />}
            count={openDisruptions.length}
          >
            {openDisruptions.length === 0 ? (
              <p className="py-2 text-xs text-muted-foreground">
                Zero unresolved corridor disruptions.
              </p>
            ) : (
              openDisruptions.slice(0, 10).map((d) => (
                <div
                  key={`disrupt-${d.event_id}`}
                  className="flex items-center justify-between rounded border border-crit/30 bg-crit/5 px-3 py-2 text-xs"
                >
                  <div className="flex flex-col">
                    <span className="font-semibold text-foreground">{d.type}</span>
                    <span className="text-[11px] text-muted-foreground">
                      {d.location} {d.train_number ? `· Train ${d.train_number}` : ""}
                    </span>
                  </div>
                  <span className="rounded bg-crit/15 px-2 py-0.5 text-[11px] font-semibold text-crit">
                    {d.severity}
                  </span>
                </div>
              ))
            )}
            {openDisruptions.length > 10 && (
              <p className="pt-1 text-center text-[11px] text-muted-foreground">
                Showing latest 10 of {openDisruptions.length} active disruptions
              </p>
            )}
          </Panel>

          <Panel
            title="Environmental & Weather Risk"
            icon={<CloudRain className="size-3.5 text-info" />}
            count={weatherRisks.filter((w) => w.risk_level !== "LOW").length}
          >
            {weatherRisks.length === 0 ? (
              <p className="py-2 text-xs text-muted-foreground">
                Connecting to environmental weather seam...
              </p>
            ) : weatherRisks.filter((w) => w.risk_level !== "LOW").length === 0 ? (
              <div className="flex items-center gap-2 py-2 text-xs text-ok">
                <span className="size-2 rounded-full bg-ok" />
                All 68 corridor sections within safe meteorological thresholds (SRS &lt; 40).
              </div>
            ) : (
              weatherRisks
                .filter((w) => w.risk_level !== "LOW")
                .slice(0, 5)
                .map((w) => (
                  <div
                    key={`sec-risk-${w.section_id}`}
                    className="flex items-center justify-between rounded border border-border/80 bg-surface px-3 py-2 text-xs"
                  >
                    <div className="flex flex-col">
                      <span className="font-semibold text-foreground">
                        {w.section_id} ({w.section_name})
                      </span>
                      <span className="text-[11px] text-muted-foreground">
                        {w.season_name} · Vuln {w.vulnerability_score}
                      </span>
                    </div>
                    <span
                      className={`rounded px-2 py-0.5 font-mono text-[11px] font-semibold ${
                        w.hard_safety_exclusion
                          ? "bg-crit/20 text-crit"
                          : w.risk_level === "CRITICAL"
                          ? "bg-crit/15 text-crit"
                          : "bg-warn/15 text-warn-foreground"
                      }`}
                    >
                      SRS {w.srs}
                    </span>
                  </div>
                ))
            )}
          </Panel>

          <Panel
            title="Track Machine Fleet"
            icon={<Wrench className="size-3.5 text-info" />}
            count={machines.length}
          >
            {machines.slice(0, 6).map((m) => (
              <div
                key={`mach-${m.resource_id}`}
                className="flex items-center justify-between rounded border border-border/80 bg-surface px-3 py-2 text-xs hover:border-border-strong"
              >
                <div className="flex flex-col">
                  <span className="font-mono font-medium text-foreground">{m.resource_id}</span>
                  <span className="text-[11px] text-muted-foreground">
                    {m.type} · Base {m.base_depot ?? m.home_depot}
                  </span>
                </div>
                <AvailabilityBadge status={m.availability} />
              </div>
            ))}
          </Panel>

          <Panel
            title="Specialized Crew Gangs"
            icon={<ShieldAlert className="size-3.5 text-primary" />}
            count={crews.length}
          >
            {crews.slice(0, 6).map((c) => (
              <div
                key={`crew-${c.crew_id}`}
                className="flex items-center justify-between rounded border border-border/80 bg-surface px-3 py-2 text-xs hover:border-border-strong"
              >
                <div className="flex flex-col">
                  <span className="font-mono font-medium text-foreground">{c.crew_id}</span>
                  <span className="text-[11px] text-muted-foreground">
                    {c.department} · {c.base_station ?? c.depot}
                  </span>
                </div>
                <AvailabilityBadge status={c.availability} />
              </div>
            ))}
          </Panel>

          <Panel
            title="Active Maintenance Windows"
            icon={<Wrench className="size-3.5 text-ok" />}
            count={activeMaintenance.length}
          >
            {activeMaintenance.length === 0 ? (
              <p className="py-2 text-xs text-muted-foreground">
                No maintenance blocks currently taking track possession.
              </p>
            ) : (
              activeMaintenance.map((b) => (
                <div
                  key={`act-${b.block_id}`}
                  className="flex items-center justify-between rounded border border-border/80 bg-surface px-3 py-2 text-xs hover:border-border-strong"
                >
                  <div className="flex flex-col">
                    <span className="font-mono font-medium text-foreground">{b.block_id}</span>
                    <span className="text-[11px] text-muted-foreground">
                      Km {b.from_km}–{b.to_km} ({b.section_id})
                    </span>
                  </div>
                  <ImpactBadge impact={b.train_impact} />
                </div>
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
  count,
  children,
}: {
  title: string;
  icon?: React.ReactNode;
  count?: number;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col rounded-lg border border-border bg-surface shadow-xs">
      <div className="flex items-center justify-between border-b border-border/70 bg-surface-2/60 px-3.5 py-2.5">
        <div className="flex items-center gap-2">
          {icon}
          <span className="text-xs font-semibold uppercase tracking-wider text-foreground">
            {title}
          </span>
        </div>
        {typeof count === "number" && (
          <span className="rounded-full bg-border/80 px-2 py-0.5 font-mono text-[10px] font-semibold text-muted-foreground">
            {count}
          </span>
        )}
      </div>
      <div className="space-y-2 p-3">{children}</div>
    </div>
  );
}
