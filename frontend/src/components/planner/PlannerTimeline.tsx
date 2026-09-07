import { useMemo, useRef, useState } from "react";
import { Lock, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { toHHMM } from "@/utils/dateUtils";
import type { BlockPlan, Conflict, PlannerLane, TrainPath } from "@/types";

const PLAN_START = 6 * 60;
const PLAN_END = 20 * 60;
const PX_PER_MIN = 3.4;
const LANES: PlannerLane[] = [
  "Passenger",
  "Express",
  "Freight",
  "Engineering",
  "TRD",
  "S&T",
  "Integrated",
];
const ROW_HEIGHT = 46;

const LANE_COLOR: Record<PlannerLane, string> = {
  Passenger: "#0ea5e9",
  Express: "#2563eb",
  Freight: "#64748b",
  Engineering: "#3b82f6",
  TRD: "#f59e0b",
  "S&T": "#10b981",
  Integrated: "#8b5cf6",
};

const LANE_BG: Record<PlannerLane, string> = {
  Passenger: "rgba(14, 165, 233, 0.12)",
  Express: "rgba(37, 99, 235, 0.12)",
  Freight: "rgba(100, 116, 139, 0.12)",
  Engineering: "rgba(59, 130, 246, 0.15)",
  TRD: "rgba(245, 158, 11, 0.15)",
  "S&T": "rgba(16, 185, 129, 0.15)",
  Integrated: "rgba(139, 92, 246, 0.16)",
};

function xForMin(min: number) {
  return (Math.max(PLAN_START, Math.min(PLAN_END, min)) - PLAN_START) * PX_PER_MIN;
}

interface PlannerTimelineProps {
  blocks: BlockPlan[];
  trainPaths: TrainPath[];
  conflictsByBlock: Record<string, Conflict[]>;
  selectedBlockId: string | null;
  onSelect: (id: string) => void;
  onMove: (id: string, start_min: number) => void;
  onResize: (id: string, duration_min: number) => void;
  nowMin?: number | undefined;
}

export function PlannerTimeline({
  blocks,
  trainPaths,
  conflictsByBlock,
  selectedBlockId,
  onSelect,
  onMove,
  onResize,
  nowMin,
}: PlannerTimelineProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [drag, setDrag] = useState<{
    id: string;
    mode: "move" | "resize";
    startX: number;
    origStart: number;
    origDuration: number;
  } | null>(null);

  const totalWidth = (PLAN_END - PLAN_START) * PX_PER_MIN;
  const hours = useMemo(() => {
    const arr: number[] = [];
    for (let m = PLAN_START; m <= PLAN_END; m += 60) arr.push(m);
    return arr;
  }, []);

  const blocksByLane = useMemo(() => {
    const map = new Map<PlannerLane, BlockPlan[]>();
    for (const lane of LANES) map.set(lane, []);
    for (const b of blocks) map.get(b.lane)?.push(b);
    return map;
  }, [blocks]);

  const pathsByLane = useMemo(() => {
    const map = new Map<PlannerLane, TrainPath[]>();
    for (const lane of LANES) map.set(lane, []);
    for (const p of trainPaths) map.get(p.lane)?.push(p);
    return map;
  }, [trainPaths]);

  const onPointerMove = (e: PointerEvent) => {
    setDrag((current) => {
      if (!current) return current;
      const deltaPx = e.clientX - current.startX;
      const deltaMin = Math.round(deltaPx / PX_PER_MIN / 15) * 15;
      if (current.mode === "move") {
        onMove(current.id, current.origStart + deltaMin);
      } else {
        onResize(current.id, Math.max(30, current.origDuration + deltaMin));
      }
      return current;
    });
  };

  const endDrag = () => {
    setDrag(null);
    window.removeEventListener("pointermove", onPointerMove);
    window.removeEventListener("pointerup", endDrag);
  };

  const startDrag = (mode: "move" | "resize", block: BlockPlan) => (e: React.PointerEvent) => {
    if (block.locked) return;
    e.stopPropagation();
    onSelect(block.block_id);
    setDrag({
      id: block.block_id,
      mode,
      startX: e.clientX,
      origStart: block.start_min,
      origDuration: block.duration_min,
    });
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", endDrag);
  };

  return (
    <div className="flex flex-col overflow-hidden rounded-md border border-border bg-surface">
      <div className="overflow-x-auto">
        <div style={{ width: totalWidth + 140 }}>
          {/* Time ruler */}
          <div className="sticky top-0 z-10 flex border-b border-border bg-surface-2">
            <div className="sticky left-0 z-20 w-[140px] shrink-0 border-r border-border bg-surface-2 px-2 py-1.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
              TIME →
            </div>
            <div className="relative h-7 flex-1" style={{ width: totalWidth }}>
              {hours.map((h) => (
                <div
                  key={h}
                  className="absolute top-0 h-full border-l border-border/70 pl-1 text-[10px] text-muted-foreground"
                  style={{ left: xForMin(h) }}
                >
                  {toHHMM(h)}
                </div>
              ))}
            </div>
          </div>

          <div ref={containerRef} className="relative">
            {nowMin !== undefined && nowMin >= PLAN_START && nowMin <= PLAN_END && (
              <div
                className="pointer-events-none absolute top-0 z-10 h-full border-l-2 border-dashed border-primary/70"
                style={{ left: 140 + xForMin(nowMin) }}
              />
            )}
            {LANES.map((lane) => (
              <div
                key={lane}
                className="flex border-b border-border last:border-b-0"
                style={{ height: ROW_HEIGHT }}
              >
                <div className="sticky left-0 z-10 flex w-[140px] shrink-0 items-center border-r border-border bg-surface px-2 text-[11px] font-medium text-foreground">
                  {lane}
                </div>
                <div className="relative flex-1" style={{ width: totalWidth }}>
                  {pathsByLane.get(lane)?.map((p) => (
                    <div
                      key={p.id}
                      className="absolute top-1/2 h-1.5 -translate-y-1/2 rounded-full bg-muted-foreground/25"
                      style={{
                        left: xForMin(p.start_min),
                        width: Math.max(
                          4,
                          xForMin(p.start_min + p.duration_min) - xForMin(p.start_min),
                        ),
                      }}
                      title={`Train ${p.train_number}`}
                    />
                  ))}
                  {blocksByLane.get(lane)?.map((b) => {
                    const conflicts = conflictsByBlock[b.block_id] ?? [];
                    const hasConflict = conflicts.length > 0;
                    const left = xForMin(b.start_min);
                    const width = Math.max(10, xForMin(b.start_min + b.duration_min) - left);
                    const isSelected = selectedBlockId === b.block_id;
                    return (
                      <div
                        key={b.block_id}
                        role="button"
                        tabIndex={0}
                        onClick={() => onSelect(b.block_id)}
                        onPointerDown={startDrag("move", b)}
                        className={cn(
                          "absolute top-1.5 flex h-8 items-center gap-1 overflow-hidden rounded border px-1.5 text-[11px] font-medium text-foreground shadow-sm transition-shadow",
                          b.locked ? "cursor-not-allowed" : "cursor-grab active:cursor-grabbing",
                          hasConflict ? "border-crit ring-1 ring-crit/60" : "border-border-strong",
                          isSelected && "ring-2 ring-primary",
                        )}
                        style={{
                          left,
                          width,
                          backgroundColor: LANE_BG[b.lane] || "rgba(59, 130, 246, 0.15)",
                          borderLeftWidth: "4px",
                          borderLeftColor: LANE_COLOR[b.lane] || "#3b82f6",
                        }}
                      >
                        {b.ai_generated && (
                          <Sparkles className="size-3 shrink-0 text-ai" aria-hidden />
                        )}
                        {b.locked && <Lock className="size-3 shrink-0" aria-hidden />}
                        <span className="truncate">
                          {b.block_id} · {toHHMM(b.start_min)}–
                          {toHHMM(b.start_min + b.duration_min)}
                        </span>
                        {!b.locked && (
                          <div
                            onPointerDown={startDrag("resize", b)}
                            className="absolute right-0 top-0 h-full w-1.5 cursor-ew-resize bg-foreground/10 hover:bg-foreground/30"
                          />
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
