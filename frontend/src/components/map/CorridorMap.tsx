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
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { CORRIDOR_END_KM, CORRIDOR_START_KM, STATIONS, kmToLatLng } from "@/data/stations";
import type { BlockPlan, Machine, MaintenanceTask, Train } from "@/types";

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

const BLOCK_LANE_COLOR: Record<string, { fill: string; stroke: string; label: string }> = {
  Engineering: { fill: "#3b82f6", stroke: "#1d4ed8", label: "Engineering Block" },
  TRD: { fill: "#f59e0b", stroke: "#b45309", label: "Traction & OHE Block" },
  "S&T": { fill: "#10b981", stroke: "#047857", label: "Signal & Telecom Block" },
  Integrated: { fill: "#8b5cf6", stroke: "#6d28d9", label: "Integrated Mega-Block" },
  Passenger: { fill: "#0ea5e9", stroke: "#0369a1", label: "Passenger Slot" },
  Express: { fill: "#2563eb", stroke: "#1e40af", label: "Express Slot" },
  Freight: { fill: "#64748b", stroke: "#334155", label: "Freight Corridor" },
};

// Geographic bounds for New Delhi to Kanpur Corridor
const BOUNDS = {
  minLng: 77.0,
  maxLng: 80.5,
  minLat: 26.2,
  maxLat: 28.9,
};

function projectGeo(lat: number, lng: number, width: number, height: number, padding = 40) {
  const innerWidth = width - padding * 2;
  const innerHeight = height - padding * 2;
  const x = padding + ((lng - BOUNDS.minLng) / (BOUNDS.maxLng - BOUNDS.minLng)) * innerWidth;
  // Invert Y because latitude increases northward
  const y =
    height - padding - ((lat - BOUNDS.minLat) / (BOUNDS.maxLat - BOUNDS.minLat)) * innerHeight;
  return { x, y };
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
    disruptions: true,
    criticalOnly: false,
    trackDetails: true,
  });

  const toggle = (key: keyof typeof layers) => setLayers((s) => ({ ...s, [key]: !s[key] }));

  const visibleTasks = useMemo(
    () => (layers.criticalOnly ? criticalTasks.filter((t) => t.severity === "A") : criticalTasks),
    [criticalTasks, layers.criticalOnly],
  );

  const delayedTrains = useMemo(() => trains.filter((t) => t.delay_min > 0), [trains]);

  // Dimension helpers for geographic projection
  const SVG_WIDTH = 1200;
  const SVG_HEIGHT = 450;

  // Build corridor GeoJSON/SVG line path through actual stations
  const corridorPath = useMemo(() => {
    const points = STATIONS.map((s) => projectGeo(s.lat, s.lng, SVG_WIDTH, SVG_HEIGHT));
    if (points.length === 0) return "";
    return points.reduce(
      (acc, p, i) => `${acc} ${i === 0 ? "M" : "L"} ${p.x.toFixed(1)},${p.y.toFixed(1)}`,
      "",
    );
  }, []);

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
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 border-b border-border bg-surface-2/70 px-4 py-2.5 text-xs">
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
            count={visibleTasks.length}
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
          <div className="mr-2 flex items-center rounded-md border border-border bg-surface p-0.5">
            <button
              onClick={() => setViewMode("geographic")}
              className={cn(
                "rounded px-2 py-0.5 text-[11px] font-medium transition-colors",
                viewMode === "geographic"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              Geographic
            </button>
            <button
              onClick={() => setViewMode("schematic")}
              className={cn(
                "rounded px-2 py-0.5 text-[11px] font-medium transition-colors",
                viewMode === "schematic"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              Schematic
            </button>
          </div>
          <Button
            variant="outline"
            size="icon"
            className="size-7 border-border bg-surface hover:bg-surface-2"
            onClick={() => setZoom((z) => Math.max(0.8, z - 0.25))}
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
            className="size-7 border-border bg-surface hover:bg-surface-2"
            onClick={() => setZoom((z) => Math.min(3.5, z + 0.25))}
            aria-label="Zoom in"
          >
            <Plus className="size-3.5" aria-hidden />
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="h-7 gap-1 border-border bg-surface px-2 text-[11px] hover:bg-surface-2"
            onClick={resetView}
            aria-label="Fit corridor"
          >
            <Maximize2 className="size-3" aria-hidden />
            Fit Corridor
          </Button>
        </div>
      </div>

      {/* Main Interactive Geographic Map Canvas */}
      <TooltipProvider delayDuration={100}>
        <div
          ref={containerRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          className={cn(
            "relative w-full overflow-hidden bg-slate-50 select-none cursor-grab active:cursor-grabbing",
            heightClass,
          )}
          style={{
            backgroundImage: "radial-gradient(#e2e8f0 1px, transparent 1px)",
            backgroundSize: "24px 24px",
          }}
        >
          {/* Map Watermark / Geographic Context */}
          <div className="absolute top-3 left-4 pointer-events-none z-10 flex flex-col gap-0.5">
            <span className="font-mono text-[11px] font-bold tracking-wider text-slate-800 uppercase">
              Northern / North Central Railway Corridor
            </span>
            <span className="text-[11px] text-slate-700 font-medium">
              New Delhi (NDLS, Km 0.0) ➔ Kanpur Central (CNB, Km 440.0) · Double Line Electrified
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
              {/* Railway track tie pattern */}
              <pattern
                id="trackPattern"
                width="12"
                height="12"
                patternUnits="userSpaceOnUse"
                patternTransform="rotate(45)"
              >
                <line x1="0" y1="0" x2="0" y2="12" stroke="#64748b" strokeWidth="2.5" />
              </pattern>
              {/* Drop shadows */}
              <filter id="mapShadow" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.15" />
              </filter>
            </defs>

            {/* Geographical Terrain / River Reference (Yamuna & Ganga alignment) */}
            <path
              d="M 120,40 Q 280,120 450,180 T 800,280 T 1150,380"
              fill="none"
              stroke="#bfdbfe"
              strokeWidth="16"
              strokeLinecap="round"
              opacity="0.45"
            />
            <text x="520" y="210" fill="#93c5fd" fontSize="10" fontWeight="600" fontStyle="italic">
              Yamuna River Basin
            </text>

            {/* Main Double-Track Railway Line (Casing + Track Ties) */}
            {/* Outer track casing */}
            <path
              d={corridorPath}
              fill="none"
              stroke="#1e293b"
              strokeWidth="7"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            {/* Inner track ties */}
            <path
              d={corridorPath}
              fill="none"
              stroke="#ffffff"
              strokeWidth="3.5"
              strokeDasharray="6 5"
              strokeLinecap="butt"
              strokeLinejoin="round"
            />

            {/* Maintenance Blocks Overlay */}
            {layers.blocks &&
              blocks.map((b) => {
                const geoStart = kmToLatLng(b.from_km);
                const geoEnd = kmToLatLng(b.to_km);
                const p1 = projectGeo(geoStart.lat, geoStart.lng, SVG_WIDTH, SVG_HEIGHT);
                const p2 = projectGeo(geoEnd.lat, geoEnd.lng, SVG_WIDTH, SVG_HEIGHT);
                const laneColor = BLOCK_LANE_COLOR[b.lane] || BLOCK_LANE_COLOR.Engineering;
                const isSelected = selected?.kind === "block" && selected.id === b.block_id;

                const dx = p2.x - p1.x;
                const dy = p2.y - p1.y;
                const len = Math.max(12, Math.hypot(dx, dy));

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
                          strokeOpacity={isSelected ? 0.95 : 0.75}
                          strokeLinecap="round"
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
                    <TooltipContent className="bg-surface text-foreground shadow-lg border-border">
                      <div className="space-y-1 text-xs">
                        <div className="flex items-center gap-1.5 font-bold text-primary">
                          <Wrench className="size-3.5" />
                          Block {b.block_id}
                        </div>
                        <p className="font-medium text-slate-700">
                          {b.lane} · {b.status}
                        </p>
                        <p className="text-[11px] text-muted-foreground">
                          Km {b.from_km.toFixed(1)}–{b.to_km.toFixed(1)} · Duration {b.duration_min}
                          m
                        </p>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                );
              })}

            {/* Stations Layer */}
            {layers.stations &&
              STATIONS.map((s) => {
                const pos = projectGeo(s.lat, s.lng, SVG_WIDTH, SVG_HEIGHT);
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
                    {/* Station Node Marker */}
                    <circle
                      cx={pos.x}
                      cy={pos.y}
                      r={s.major ? 8 : 5.5}
                      fill={s.major ? "#1e3a8a" : "#ffffff"}
                      stroke={isSelected ? "#f59e0b" : "#0f172a"}
                      strokeWidth={isSelected ? 3 : 2}
                      filter="url(#mapShadow)"
                    />
                    {s.major && <circle cx={pos.x} cy={pos.y} r={3.5} fill="#ffffff" />}

                    {/* Station Label & Chainage */}
                    <rect
                      x={pos.x - (s.major ? 28 : 22)}
                      y={pos.y - (s.major ? 28 : 24)}
                      width={s.major ? 56 : 44}
                      height={16}
                      rx={3}
                      fill="#ffffff"
                      fillOpacity={0.92}
                      stroke="#cbd5e1"
                      strokeWidth={0.75}
                    />
                    <text
                      x={pos.x}
                      y={pos.y - (s.major ? 17 : 13)}
                      textAnchor="middle"
                      fontSize={s.major ? 10 : 8.5}
                      fontWeight={s.major ? 700 : 600}
                      fill="#0f172a"
                    >
                      {s.station_code}
                    </text>
                    <text
                      x={pos.x}
                      y={pos.y + 18}
                      textAnchor="middle"
                      fontSize={8}
                      fontWeight={500}
                      fill="#64748b"
                    >
                      Km {s.km}
                    </text>
                  </g>
                );
              })}

            {/* Maintenance Tasks / Critical Defects Layer */}
            {layers.maintenance &&
              visibleTasks.map((t, idx) => {
                const centerKm = (t.from_km + t.to_km) / 2;
                const geo = kmToLatLng(centerKm);
                const pos = projectGeo(geo.lat, geo.lng, SVG_WIDTH, SVG_HEIGHT);
                const isSelected = selected?.kind === "task" && selected.id === t.task_id;
                const isCritical = t.severity === "A";

                return (
                  <Tooltip key={`task-marker-${t.task_id}-${idx}`}>
                    <TooltipTrigger asChild>
                      <g
                        transform={`translate(${pos.x} ${pos.y + 10})`}
                        className="cursor-pointer hover:scale-125 transition-transform"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelect?.({ kind: "task", id: t.task_id });
                        }}
                      >
                        {isCritical && (
                          <circle
                            cx="0"
                            cy="0"
                            r="8"
                            fill="#ef4444"
                            opacity="0.3"
                            className="animate-ping"
                          />
                        )}
                        <circle
                          cx="0"
                          cy="0"
                          r={isCritical ? 5.5 : 4}
                          fill={isCritical ? "#ef4444" : t.severity === "B" ? "#f59e0b" : "#64748b"}
                          stroke="#ffffff"
                          strokeWidth={1.5}
                          filter="url(#mapShadow)"
                        />
                      </g>
                    </TooltipTrigger>
                    <TooltipContent className="bg-surface text-foreground shadow-lg border-border">
                      <div className="space-y-1 text-xs">
                        <div className="flex items-center gap-1 font-bold text-crit">
                          <AlertTriangle className="size-3.5" />
                          {t.task_id} (Sev {t.severity})
                        </div>
                        <p className="font-medium">{t.defect}</p>
                        <p className="text-[11px] text-muted-foreground">
                          {t.department} · {t.location_label}
                        </p>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                );
              })}

            {/* Machines / Heavy Equipment Layer */}
            {layers.machines &&
              machines.map((m, idx) => {
                const geo = kmToLatLng(m.km);
                const pos = projectGeo(geo.lat, geo.lng, SVG_WIDTH, SVG_HEIGHT);
                const isSelected = selected?.kind === "machine" && selected.id === m.resource_id;

                return (
                  <Tooltip key={`mach-marker-${m.resource_id}-${idx}`}>
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
                          filter="url(#mapShadow)"
                        />
                        <path d="M-2 -2 L2 2 M-2 2 L2 -2" stroke="#ffffff" strokeWidth="1" />
                      </g>
                    </TooltipTrigger>
                    <TooltipContent className="bg-surface text-foreground shadow-lg border-border">
                      <div className="space-y-1 text-xs">
                        <p className="font-bold text-primary">
                          {m.resource_id} · {m.type}
                        </p>
                        <p className="text-[11px] text-muted-foreground">
                          Base: {m.base_depot} · {m.availability}
                        </p>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                );
              })}

            {/* Real-time Moving Trains Layer */}
            {layers.trains &&
              trains.map((t, idx) => {
                const geo = kmToLatLng(t.km);
                const pos = projectGeo(geo.lat, geo.lng, SVG_WIDTH, SVG_HEIGHT);
                const isSelected = selected?.kind === "train" && selected.id === t.train_number;
                const isDelayed = t.delay_min > 0;
                const isSevere = t.delay_min > 25;
                const isUp = t.direction === "UP";

                const trainColor = isSevere ? "#ef4444" : isDelayed ? "#f59e0b" : "#10b981";

                return (
                  <Tooltip key={`train-geo-${t.train_number}-${idx}`}>
                    <TooltipTrigger asChild>
                      <g
                        transform={`translate(${pos.x} ${pos.y}) scale(${isUp ? -1 : 1} 1)`}
                        className="cursor-pointer hover:scale-125 transition-transform"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelect?.({ kind: "train", id: t.train_number });
                        }}
                      >
                        {/* Train Arrow Body */}
                        <polygon
                          points="-8,-5 7,0 -8,5"
                          fill={trainColor}
                          stroke="#ffffff"
                          strokeWidth={1.25}
                          filter="url(#mapShadow)"
                        />
                        {isSelected && (
                          <circle
                            cx="0"
                            cy="0"
                            r="10"
                            fill="none"
                            stroke="#2563eb"
                            strokeWidth="2"
                            strokeDasharray="3 2"
                          />
                        )}
                      </g>
                    </TooltipTrigger>
                    <TooltipContent className="bg-surface text-foreground shadow-lg border-border">
                      <div className="space-y-1 text-xs">
                        <div className="flex items-center justify-between gap-3 font-bold text-foreground">
                          <span className="flex items-center gap-1.5">
                            <TrainFront className="size-3.5 text-primary" />
                            {t.name} ({t.train_number})
                          </span>
                          <span
                            className={cn(
                              "font-mono text-[11px]",
                              isDelayed ? "text-warn font-semibold" : "text-ok",
                            )}
                          >
                            {isDelayed ? `+${t.delay_min}m` : "On-Time"}
                          </span>
                        </div>
                        <p className="text-[11px] text-muted-foreground">
                          {t.category} · {t.direction} ➔ {t.destination} · Near Km {t.km.toFixed(1)}
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
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 border-t border-border bg-surface-2/40 px-4 py-2 text-[11px] text-muted-foreground">
        <div className="flex flex-wrap items-center gap-4">
          <LegendItem swatch="#10b981" label="On-Time Train" />
          <LegendItem swatch="#f59e0b" label="Delayed Train (+5-25m)" />
          <LegendItem swatch="#ef4444" label="Severe Delay (>25m) / Defect" />
          <LegendItem swatch="#3b82f6" label="Engineering Block / Machine" />
          <LegendItem swatch="#8b5cf6" label="Integrated Mega-Block" />
          <LegendItem swatch="#1e3a8a" label="Major Station" />
        </div>

        <div className="flex items-center gap-3 font-medium text-foreground">
          <span className="inline-flex items-center gap-1.5">
            <TrainFront className="size-3.5 text-primary" />
            <strong className="font-mono">{trains.length}</strong> Trains ({delayedTrains.length}{" "}
            delayed)
          </span>
          <span className="inline-flex items-center gap-1.5">
            <Wrench className="size-3.5 text-info" />
            <strong className="font-mono">{blocks.length}</strong> Active Blocks
          </span>
          <span className="inline-flex items-center gap-1.5">
            <AlertTriangle className="size-3.5 text-crit" />
            <strong className="font-mono">{criticalTasks.length}</strong> Defects
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
    <label className="flex items-center gap-1.5 cursor-pointer text-muted-foreground hover:text-foreground font-medium">
      <Checkbox
        checked={checked}
        onCheckedChange={onChange}
        className="size-3.5 border-border data-[state=checked]:bg-primary data-[state=checked]:border-primary"
      />
      <span>{label}</span>
      {typeof count === "number" && (
        <span className="rounded bg-surface-2 px-1 py-0.2 text-[10px] font-mono text-slate-600 font-semibold">
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
        className="size-2.5 rounded-full border border-black/10 shadow-xs"
        style={{ backgroundColor: swatch }}
        aria-hidden
      />
      <span className="text-slate-700 font-medium">{label}</span>
    </span>
  );
}
