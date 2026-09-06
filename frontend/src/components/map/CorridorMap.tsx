import { useMemo, useState, useEffect, useRef } from "react";
import {
  AlertTriangle,
  Layers,
  Maximize2,
  Minus,
  Navigation,
  Plus,
  RefreshCw,
  TrainFront,
  Wrench,
  ShieldAlert,
  Info,
  MapPin,
  Flame,
  Activity,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { CORRIDOR_END_KM, CORRIDOR_START_KM, STATIONS, kmToLatLng } from "@/data/stations";
import type { BlockPlan, Department, Machine, MaintenanceTask, Train } from "@/types";

export type MapEntitySelection =
  | { kind: "station"; id: string }
  | { kind: "train"; id: string }
  | { kind: "block"; id: string }
  | { kind: "task"; id: string }
  | { kind: "machine"; id: string };

interface CorridorMapProps {
  trains?: Train[];
  blocks?: BlockPlan[];
  criticalTasks?: MaintenanceTask[];
  machines?: Machine[];
  selected?: MapEntitySelection | null;
  onSelect?: (sel: MapEntitySelection) => void;
  className?: string;
  heightClass?: string;
}

const DEFAULT_LANE_COLOR = { fill: "#3b82f6", stroke: "#1d4ed8", label: "Engineering Block" };

const BLOCK_LANE_COLOR: Record<string, { fill: string; stroke: string; label: string }> = {
  Engineering: DEFAULT_LANE_COLOR,
  TRD: { fill: "#f59e0b", stroke: "#b45309", label: "Traction & OHE Block" },
  "S&T": { fill: "#10b981", stroke: "#047857", label: "Signal & Telecom Block" },
  Integrated: { fill: "#8b5cf6", stroke: "#6d28d9", label: "Integrated Mega-Block" },
  Passenger: { fill: "#0ea5e9", stroke: "#0369a1", label: "Passenger Slot" },
  Express: { fill: "#2563eb", stroke: "#1e40af", label: "Express Slot" },
  Freight: { fill: "#64748b", stroke: "#334155", label: "Freight Corridor" },
};

// Geographic bounds for Chennai Egmore to Thoothukudi Corridor
const BOUNDS = {
  minLng: 77.8,
  maxLng: 80.4,
  minLat: 8.7,
  maxLat: 13.2,
};

function projectGeo(lat: number, lng: number, width: number, height: number, paddingX = 60, paddingY = 50) {
  const innerWidth = width - paddingX * 2;
  const innerHeight = height - paddingY * 2;
  const x = paddingX + ((lng - BOUNDS.minLng) / (BOUNDS.maxLng - BOUNDS.minLng)) * innerWidth;
  // Invert Y because latitude increases northward
  const y = height - paddingY - ((lat - BOUNDS.minLat) / (BOUNDS.maxLat - BOUNDS.minLat)) * innerHeight;
  return { x, y };
}

function projectSchematic(km: number, width: number, height: number, paddingX = 60) {
  const innerWidth = width - paddingX * 2;
  const clampedKm = Math.max(CORRIDOR_START_KM, Math.min(CORRIDOR_END_KM, km));
  const x = paddingX + (clampedKm / CORRIDOR_END_KM) * innerWidth;
  const y = height / 2;
  return { x, y };
}

interface DefectCluster {
  id: string;
  centerKm: number;
  fromKm: number;
  toKm: number;
  count: number;
  sevACount: number;
  sevBCount: number;
  sevCCount: number;
  topTask?: MaintenanceTask | undefined;
  departments: Department[] | string[];
}

export function CorridorMap({
  trains = [],
  blocks = [],
  criticalTasks = [],
  machines = [],
  selected,
  onSelect,
  className,
  heightClass = "h-[420px]",
}: CorridorMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [viewMode, setViewMode] = useState<"geographic" | "schematic">("geographic");

  const [layers, setLayers] = useState({
    stations: true,
    trains: true,
    maintenance: true,
    blocks: true,
    machines: true,
    criticalOnly: false,
  });

  const toggle = (key: keyof typeof layers) => setLayers((s) => ({ ...s, [key]: !s[key] }));

  const SVG_WIDTH = 1200;
  const SVG_HEIGHT = 440;

  // Clustered defect representation to prevent overlapping 6,700 items into a blob
  const defectClusters = useMemo<DefectCluster[]>(() => {
    const sourceTasks = layers.criticalOnly
      ? criticalTasks.filter((t) => t.severity === "A")
      : criticalTasks;
    if (sourceTasks.length === 0) return [];

    const bucketSize = 18; // 18 km buckets along 440km corridor = ~24 clear clusters
    const buckets: Record<number, MaintenanceTask[]> = {};

    sourceTasks.forEach((task) => {
      const centerKm = (task.from_km + task.to_km) / 2;
      const bucketIdx = Math.floor(centerKm / bucketSize);
      if (!buckets[bucketIdx]) buckets[bucketIdx] = [];
      buckets[bucketIdx].push(task);
    });

    return Object.entries(buckets).map(([bIdxStr, tList]) => {
      const bIdx = Number(bIdxStr);
      const fromKm = bIdx * bucketSize;
      const toKm = Math.min(CORRIDOR_END_KM, (bIdx + 1) * bucketSize);
      const centerKm = (fromKm + toKm) / 2;
      const sevACount = tList.filter((t) => t.severity === "A").length;
      const sevBCount = tList.filter((t) => t.severity === "B").length;
      const sevCCount = tList.filter((t) => t.severity === "C").length;
      const sorted = [...tList].sort((a, b) => b.priority_score - a.priority_score);
      const depts = Array.from(new Set(tList.map((t) => t.department)));

      return {
        id: `cluster-km-${Math.round(centerKm)}`,
        centerKm,
        fromKm,
        toKm,
        count: tList.length,
        sevACount,
        sevBCount,
        sevCCount,
        topTask: sorted[0],
        departments: depts,
      };
    });
  }, [criticalTasks, layers.criticalOnly]);

  const delayedTrains = useMemo(() => trains.filter((t) => t.delay_min > 0), [trains]);

  // Coordinate projector helper based on current mode
  const getPoint = (km: number) => {
    if (viewMode === "schematic") {
      return projectSchematic(km, SVG_WIDTH, SVG_HEIGHT);
    }
    const geo = kmToLatLng(km);
    return projectGeo(geo.lat, geo.lng, SVG_WIDTH, SVG_HEIGHT);
  };

  // Build continuous track line path
  const corridorPath = useMemo(() => {
    if (viewMode === "schematic") {
      const pStart = projectSchematic(CORRIDOR_START_KM, SVG_WIDTH, SVG_HEIGHT);
      const pEnd = projectSchematic(CORRIDOR_END_KM, SVG_WIDTH, SVG_HEIGHT);
      return `M ${pStart.x.toFixed(1)},${pStart.y.toFixed(1)} L ${pEnd.x.toFixed(1)},${pEnd.y.toFixed(1)}`;
    }
    const points = STATIONS.map((s) => projectGeo(s.lat, s.lng, SVG_WIDTH, SVG_HEIGHT));
    if (points.length === 0) return "";
    return points.reduce(
      (acc, p, i) => `${acc} ${i === 0 ? "M" : "L"} ${p.x.toFixed(1)},${p.y.toFixed(1)}`,
      "",
    );
  }, [viewMode]);

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
  };

  const handleMouseUp = () => setIsDragging(false);

  const resetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  return (
    <div
      className={cn(
        "flex flex-col overflow-hidden rounded-xl border border-border bg-surface shadow-xs",
        className,
      )}
    >
      {/* Map Control Bar */}
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 border-b border-border bg-surface-2/80 px-4 py-2 text-xs">
        <div className="flex flex-wrap items-center gap-3">
          <span className="flex items-center gap-1.5 font-semibold text-foreground">
            <Layers className="size-3.5 text-primary" />
            Layers:
          </span>
          <LayerToggle
            label="Stations"
            count={STATIONS.length}
            checked={layers.stations}
            onChange={() => toggle("stations")}
          />
          <LayerToggle
            label="Live Trains"
            count={trains.length}
            checked={layers.trains}
            onChange={() => toggle("trains")}
          />
          <LayerToggle
            label="Maintenance"
            count={criticalTasks.length}
            checked={layers.maintenance}
            onChange={() => toggle("maintenance")}
          />
          <LayerToggle
            label="Blocks"
            count={blocks.length}
            checked={layers.blocks}
            onChange={() => toggle("blocks")}
          />
          <LayerToggle
            label="Machines"
            count={machines.length}
            checked={layers.machines}
            onChange={() => toggle("machines")}
          />
          <LayerToggle
            label="Critical Only"
            checked={layers.criticalOnly}
            onChange={() => toggle("criticalOnly")}
          />
        </div>

        <div className="flex items-center gap-1.5">
          <div className="mr-1 flex items-center rounded-md border border-border bg-surface p-0.5 shadow-2xs">
            <button
              onClick={() => setViewMode("geographic")}
              className={cn(
                "rounded px-2.5 py-0.5 text-[11px] font-medium transition-colors cursor-pointer",
                viewMode === "geographic"
                  ? "bg-primary text-primary-foreground font-semibold shadow-xs"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              Geographic
            </button>
            <button
              onClick={() => setViewMode("schematic")}
              className={cn(
                "rounded px-2.5 py-0.5 text-[11px] font-medium transition-colors cursor-pointer",
                viewMode === "schematic"
                  ? "bg-primary text-primary-foreground font-semibold shadow-xs"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              Schematic
            </button>
          </div>
          <Button
            variant="outline"
            size="icon"
            className="size-7 border-border bg-surface hover:bg-surface-2 cursor-pointer"
            onClick={() => setZoom((z) => Math.max(0.75, z - 0.25))}
            aria-label="Zoom out"
          >
            <Minus className="size-3.5" aria-hidden />
          </Button>
          <span className="min-w-8 text-center font-mono text-[11px] font-semibold text-muted-foreground">
            {Math.round(zoom * 100)}%
          </span>
          <Button
            variant="outline"
            size="icon"
            className="size-7 border-border bg-surface hover:bg-surface-2 cursor-pointer"
            onClick={() => setZoom((z) => Math.min(3.0, z + 0.25))}
            aria-label="Zoom in"
          >
            <Plus className="size-3.5" aria-hidden />
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="h-7 gap-1 border-border bg-surface px-2 text-[11px] hover:bg-surface-2 cursor-pointer"
            onClick={resetView}
            aria-label="Fit corridor"
          >
            <Maximize2 className="size-3" aria-hidden />
            Fit Corridor
          </Button>
        </div>
      </div>

      {/* Main Interactive Map Canvas */}
      <TooltipProvider delayDuration={100}>
        <div
          ref={containerRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          className={cn(
            "relative w-full overflow-hidden bg-slate-950 select-none cursor-grab active:cursor-grabbing",
            heightClass,
          )}
          style={{
            backgroundImage: "radial-gradient(#1e293b 1px, transparent 1px)",
            backgroundSize: "28px 28px",
          }}
        >
          {/* Corridor HUD Badge in Top Right to avoid collision with NDLS at (40, 40) */}
          <div className="absolute top-3 right-4 pointer-events-none z-10 hidden sm:flex flex-col items-end gap-0.5 rounded-md border border-slate-800 bg-slate-900/85 px-3 py-1.5 backdrop-blur-sm shadow-md">
            <span className="font-mono text-[10px] font-bold tracking-wider text-slate-200 uppercase">
              Northern / North Central Railway Corridor
            </span>
            <span className="text-[10px] text-slate-400 font-medium">
              New Delhi (NDLS, Km 0) ➔ Kanpur Central (CNB, Km 440) · Double Line Electrified
            </span>
          </div>

          <svg
            viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
            className="w-full h-full transition-transform duration-75"
            style={{
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              transformOrigin: "center center",
            }}
          >
            <defs>
              <filter id="glowOk" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="0" dy="1" stdDeviation="2" floodColor="#10b981" floodOpacity="0.4" />
              </filter>
              <filter id="glowCrit" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="0" dy="1" stdDeviation="3" floodColor="#ef4444" floodOpacity="0.6" />
              </filter>
              <filter id="glowBlock" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="0" dy="1" stdDeviation="2" floodColor="#8b5cf6" floodOpacity="0.4" />
              </filter>
            </defs>

            {/* Geographical Terrain / River Alignment (only in geographic mode) */}
            {viewMode === "geographic" && (
              <>
                <path
                  d="M 120,40 Q 280,120 450,180 T 800,280 T 1150,380"
                  fill="none"
                  stroke="#1e3a5f"
                  strokeWidth="18"
                  strokeLinecap="round"
                  opacity="0.35"
                />
                <text x="520" y="210" fill="#3b82f6" opacity="0.5" fontSize="10" fontWeight="600" fontStyle="italic">
                  Yamuna River Basin
                </text>
              </>
            )}

            {/* Main Railway Double-Track Lines */}
            {/* Base ballast bed */}
            <path
              d={corridorPath}
              fill="none"
              stroke="#0f172a"
              strokeWidth="10"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            {/* Outer track casing */}
            <path
              d={corridorPath}
              fill="none"
              stroke="#334155"
              strokeWidth="6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            {/* Inner track ties */}
            <path
              d={corridorPath}
              fill="none"
              stroke="#94a3b8"
              strokeWidth="2.5"
              strokeDasharray="5 5"
              strokeLinecap="butt"
              strokeLinejoin="round"
            />

            {/* Maintenance Blocks Overlay */}
            {layers.blocks &&
              blocks.map((b) => {
                const p1 = getPoint(b.from_km);
                const p2 = getPoint(b.to_km);
                const laneColor = (b.lane ? BLOCK_LANE_COLOR[b.lane] : null) ?? DEFAULT_LANE_COLOR;
                const isSelected = selected?.kind === "block" && selected.id === b.block_id;

                return (
                  <Tooltip key={`block-geo-${b.block_id}`}>
                    <TooltipTrigger asChild>
                      <g
                        className="cursor-pointer transition-transform hover:scale-105"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelect?.({ kind: "block", id: b.block_id });
                        }}
                      >
                        <line
                          x1={p1.x}
                          y1={p1.y}
                          x2={p2.x}
                          y2={p2.y}
                          stroke={laneColor.fill}
                          strokeWidth={isSelected ? 14 : 10}
                          strokeOpacity={isSelected ? 0.95 : 0.8}
                          strokeLinecap="round"
                          filter="url(#glowBlock)"
                        />
                        <line
                          x1={p1.x}
                          y1={p1.y}
                          x2={p2.x}
                          y2={p2.y}
                          stroke="#ffffff"
                          strokeWidth={2}
                          strokeDasharray="4 4"
                        />
                      </g>
                    </TooltipTrigger>
                    <TooltipContent className="bg-slate-900 text-slate-100 shadow-xl border-slate-700">
                      <div className="space-y-1 text-xs">
                        <div className="flex items-center gap-1.5 font-bold text-violet-400">
                          <Wrench className="size-3.5" />
                          Block {b.block_id}
                        </div>
                        <p className="font-medium text-slate-200">
                          {b.lane} · {b.status}
                        </p>
                        <p className="text-[11px] text-slate-400">
                          Km {b.from_km.toFixed(1)}–{b.to_km.toFixed(1)} · Duration {b.duration_min}m
                        </p>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                );
              })}

            {/* Stations Layer */}
            {layers.stations &&
              STATIONS.map((s) => {
                const pos = getPoint(s.km);
                const isSelected = selected?.kind === "station" && selected.id === s.station_code;

                return (
                  <g
                    key={`station-${s.station_code}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelect?.({ kind: "station", id: s.station_code });
                    }}
                    className="cursor-pointer"
                  >
                    {/* Station Node Dot */}
                    <circle
                      cx={pos.x}
                      cy={pos.y}
                      r={s.major ? 7 : 5}
                      fill={s.major ? "#38bdf8" : "#f8fafc"}
                      stroke={isSelected ? "#f59e0b" : "#0f172a"}
                      strokeWidth={isSelected ? 3 : 2}
                    />
                    {s.major && <circle cx={pos.x} cy={pos.y} r={3} fill="#0369a1" />}

                    {/* Station Label Badge */}
                    <rect
                      x={pos.x - (s.major ? 24 : 18)}
                      y={pos.y - (s.major ? 26 : 22)}
                      width={s.major ? 48 : 36}
                      height={15}
                      rx={3}
                      fill="#0f172a"
                      fillOpacity={0.92}
                      stroke={s.major ? "#38bdf8" : "#475569"}
                      strokeWidth={s.major ? 1.25 : 0.75}
                    />
                    <text
                      x={pos.x}
                      y={pos.y - (s.major ? 15 : 11)}
                      textAnchor="middle"
                      fontSize={s.major ? 9.5 : 8}
                      fontWeight={s.major ? 700 : 600}
                      fill="#f8fafc"
                    >
                      {s.station_code}
                    </text>
                    <text
                      x={pos.x}
                      y={pos.y + 16}
                      textAnchor="middle"
                      fontSize={7.5}
                      fontWeight={500}
                      fill="#94a3b8"
                    >
                      Km {s.km}
                    </text>
                  </g>
                );
              })}

            {/* Maintenance Defects Layer (Clustered & Capped) */}
            {layers.maintenance &&
              defectClusters.map((c) => {
                const pos = getPoint(c.centerKm);
                const hasSevA = c.sevACount > 0;
                const markerColor = hasSevA ? "#ef4444" : c.sevBCount > 0 ? "#f59e0b" : "#94a3b8";

                return (
                  <Tooltip key={c.id}>
                    <TooltipTrigger asChild>
                      <g
                        transform={`translate(${pos.x} ${pos.y + 9})`}
                        className="cursor-pointer hover:scale-125 transition-transform"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (c.topTask) {
                            onSelect?.({ kind: "task", id: c.topTask.task_id });
                          }
                        }}
                      >
                        {hasSevA && (
                          <circle
                            cx="0"
                            cy="0"
                            r="9"
                            fill="#ef4444"
                            opacity="0.3"
                            className="animate-ping"
                          />
                        )}
                        <circle
                          cx="0"
                          cy="0"
                          r={hasSevA ? 6 : 5}
                          fill={markerColor}
                          stroke="#ffffff"
                          strokeWidth={1.5}
                          filter={hasSevA ? "url(#glowCrit)" : undefined}
                        />
                        {/* Cluster count pill for 2+ defects */}
                        {c.count > 1 && (
                          <rect
                            x="4"
                            y="-9"
                            width="14"
                            height="10"
                            rx="3"
                            fill="#0f172a"
                            stroke={markerColor}
                            strokeWidth="0.75"
                          />
                        )}
                        {c.count > 1 && (
                          <text
                            x="11"
                            y="-1.5"
                            textAnchor="middle"
                            fontSize="7"
                            fontWeight="700"
                            fill="#ffffff"
                          >
                            {c.count > 99 ? "99+" : c.count}
                          </text>
                        )}
                      </g>
                    </TooltipTrigger>
                    <TooltipContent className="bg-slate-900 text-slate-100 shadow-xl border-slate-700">
                      <div className="space-y-1.5 text-xs max-w-xs">
                        <div className="flex items-center justify-between gap-2 font-bold text-red-400">
                          <span className="flex items-center gap-1">
                            <AlertTriangle className="size-3.5" />
                            Defect Cluster: Km {Math.round(c.fromKm)}–{Math.round(c.toKm)}
                          </span>
                          <span className="rounded bg-red-950 px-1.5 py-0.5 text-[10px] text-red-300 font-mono">
                            {c.count} tasks
                          </span>
                        </div>
                        <p className="font-medium text-slate-200 text-[11px]">
                          Top: {c.topTask ? `${c.topTask.defect} (Sev ${c.topTask.severity})` : "Track Defect"}
                        </p>
                        <div className="flex items-center gap-2 text-[10px] text-slate-400 border-t border-slate-800 pt-1">
                          <span>Sev A: {c.sevACount}</span>
                          <span>Sev B: {c.sevBCount}</span>
                          <span>Depts: {c.departments.join(", ")}</span>
                        </div>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                );
              })}

            {/* Machines Layer */}
            {layers.machines &&
              machines.map((m) => {
                const pos = getPoint(m.km);
                const isSelected = selected?.kind === "machine" && selected.id === m.resource_id;

                return (
                  <Tooltip key={`mach-marker-${m.resource_id}`}>
                    <TooltipTrigger asChild>
                      <g
                        transform={`translate(${pos.x} ${pos.y - 12})`}
                        className="cursor-pointer hover:scale-125 transition-transform"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelect?.({ kind: "machine", id: m.resource_id });
                        }}
                      >
                        <rect
                          x="-6"
                          y="-6"
                          width="12"
                          height="12"
                          rx="2.5"
                          fill="#3b82f6"
                          stroke={isSelected ? "#f59e0b" : "#ffffff"}
                          strokeWidth={1.5}
                        />
                        <path d="M-2 -2 L2 2 M-2 2 L2 -2" stroke="#ffffff" strokeWidth="1" />
                      </g>
                    </TooltipTrigger>
                    <TooltipContent className="bg-slate-900 text-slate-100 shadow-xl border-slate-700">
                      <div className="space-y-1 text-xs">
                        <p className="font-bold text-blue-400">
                          {m.resource_id} · {m.type}
                        </p>
                        <p className="text-[11px] text-slate-300">
                          Base: {m.base_depot ?? m.home_depot} · {m.availability} (Near Km {m.km.toFixed(1)})
                        </p>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                );
              })}

            {/* Real-time Moving Trains Layer with directional track offset */}
            {layers.trains &&
              trains.map((t) => {
                const basePos = getPoint(t.km);
                const isSelected = selected?.kind === "train" && selected.id === t.train_number;
                const isDelayed = t.delay_min > 0;
                const isSevere = t.delay_min > 25;
                const isUp = t.direction === "UP";

                // Directional offset: UP trains on top line (-6px), DOWN trains on bottom line (+6px)
                const offsetY = isUp ? -6 : 6;
                const posX = basePos.x;
                const posY = basePos.y + offsetY;
                const trainColor = isSevere ? "#ef4444" : isDelayed ? "#f59e0b" : "#10b981";

                return (
                  <Tooltip key={`train-geo-${t.train_number}`}>
                    <TooltipTrigger asChild>
                      <g
                        transform={`translate(${posX} ${posY}) scale(${isUp ? -1 : 1} 1)`}
                        className="cursor-pointer hover:scale-125 transition-transform"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelect?.({ kind: "train", id: t.train_number });
                        }}
                      >
                        {/* Directional train arrowhead */}
                        <polygon
                          points="-7,-4 6,0 -7,4"
                          fill={trainColor}
                          stroke="#ffffff"
                          strokeWidth={1.25}
                          filter={isDelayed ? "url(#glowCrit)" : "url(#glowOk)"}
                        />
                        {isSelected && (
                          <circle
                            cx="0"
                            cy="0"
                            r="9"
                            fill="none"
                            stroke="#38bdf8"
                            strokeWidth="2"
                            strokeDasharray="3 2"
                          />
                        )}
                      </g>
                    </TooltipTrigger>
                    <TooltipContent className="bg-slate-900 text-slate-100 shadow-xl border-slate-700">
                      <div className="space-y-1 text-xs">
                        <div className="flex items-center justify-between gap-3 font-bold">
                          <span className="flex items-center gap-1.5 text-slate-100">
                            <TrainFront className="size-3.5 text-sky-400" />
                            {t.name} ({t.train_number})
                          </span>
                          <span
                            className={cn(
                              "font-mono text-[11px] font-semibold",
                              isDelayed ? "text-amber-400" : "text-emerald-400",
                            )}
                          >
                            {isDelayed ? `+${t.delay_min}m` : "On-Time"}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-300">
                          {t.category} · {t.direction} line ➔ {t.destination} · Near Km {t.km.toFixed(1)}
                        </p>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                );
              })}
          </svg>
        </div>
      </TooltipProvider>

      {/* Map Legend & Summary Footer */}
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 border-t border-border bg-surface-2/60 px-4 py-2 text-[11px] text-muted-foreground">
        <div className="flex flex-wrap items-center gap-4">
          <LegendItem swatch="#10b981" label="On-Time Train (UP/DOWN)" />
          <LegendItem swatch="#f59e0b" label="Delayed (+5-25m)" />
          <LegendItem swatch="#ef4444" label="Severe Delay / Defect" />
          <LegendItem swatch="#3b82f6" label="Engineering Block / Machine" />
          <LegendItem swatch="#8b5cf6" label="Integrated Mega-Block" />
          <LegendItem swatch="#38bdf8" label="Major Station" />
        </div>

        <div className="flex items-center gap-3 font-medium text-foreground">
          <span className="inline-flex items-center gap-1.5">
            <TrainFront className="size-3.5 text-primary" />
            <strong className="font-mono">{trains.length}</strong> Trains ({delayedTrains.length} delayed)
          </span>
          <span className="inline-flex items-center gap-1.5">
            <Wrench className="size-3.5 text-info" />
            <strong className="font-mono">{blocks.length}</strong> Blocks
          </span>
          <span className="inline-flex items-center gap-1.5">
            <AlertTriangle className="size-3.5 text-crit" />
            <strong className="font-mono">{criticalTasks.length}</strong> Defects ({defectClusters.length} clusters)
          </span>
        </div>
      </div>
    </div>
  );
}

function LayerToggle({
  label,
  count,
  checked,
  onChange,
}: {
  label: string;
  count?: number;
  checked: boolean;
  onChange: () => void;
}) {
  return (
    <label className="flex items-center gap-1.5 cursor-pointer text-muted-foreground hover:text-foreground font-medium select-none">
      <Checkbox
        checked={checked}
        onCheckedChange={onChange}
        className="size-3.5 border-border data-[state=checked]:bg-primary data-[state=checked]:border-primary"
      />
      <span>{label}</span>
      {typeof count === "number" && (
        <span className="rounded bg-surface-2 px-1 py-0.2 text-[10px] font-mono text-foreground/80 font-semibold border border-border/50">
          {count}
        </span>
      )}
    </label>
  );
}

function LegendItem({ swatch, label }: { swatch: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        className="size-2.5 rounded-full border border-black/20 shadow-2xs shrink-0"
        style={{ backgroundColor: swatch }}
        aria-hidden
      />
      <span className="text-foreground/80 font-medium">{label}</span>
    </span>
  );
}
