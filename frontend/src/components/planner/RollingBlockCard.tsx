import React from "react";
import {
  Calendar,
  Clock,
  MapPin,
  Layers,
  Wrench,
  Users,
  AlertTriangle,
  TrendingUp,
  CloudSun,
  CheckCircle2,
  ChevronRight,
  ShieldAlert,
} from "lucide-react";
import type { RollingPlanBlock } from "@/api/plannerApi";
import { sectionById } from "@/data/sections";
import { STATIONS } from "@/data/stations";
import { minutesToDuration } from "@/utils/formatters";
import { BlockStatusBadge } from "@/components/common/StatusBadge";
import { cn } from "@/lib/utils";

// Map station codes to friendly names
const STATION_NAMES: Record<string, string> = Object.fromEntries(
  STATIONS.map((s) => [s.station_code, s.name]),
);

interface RollingBlockCardProps {
  block: RollingPlanBlock;
  onSelect: (block: RollingPlanBlock) => void;
  isSelected?: boolean;
}

export function RollingBlockCard({ block, onSelect, isSelected }: RollingBlockCardProps) {
  const section = sectionById(block.section_id);
  const fromStation = section?.from_station ?? "";
  const toStation = section?.to_station ?? "";
  const fromName = STATION_NAMES[fromStation] || fromStation;
  const toName = STATION_NAMES[toStation] || toStation;
  const fromKm = section?.from_km ?? 0;
  const toKm = section?.to_km ?? 0;
  const lengthKm = (toKm - fromKm).toFixed(1);

  // Parse departments into array
  const depts = block.departments
    ? block.departments.split(/[;,]/).map((d) => d.trim()).filter(Boolean)
    : [];

  const isMultiDept = depts.length > 1;
  const isCyclic = block.maintenance_type?.toUpperCase().includes("CYCLIC") ?? false;
  const isMega = isMultiDept || (block.maintenance_type?.toUpperCase().includes("MEGA") ?? false);

  // Format date
  const dateStr = block.plan_date || block.date;
  let formattedDate = dateStr ?? "—";
  if (dateStr) {
    try {
      const d = new Date(dateStr);
      if (!isNaN(d.getTime())) {
        formattedDate = d.toLocaleDateString("en-IN", {
          day: "2-digit",
          month: "short",
          year: "numeric",
        });
      }
    } catch {
      // keep original
    }
  }

  // Format time window
  const startTime = block.start_time ? block.start_time.split(" ")[1]?.slice(0, 5) || block.start_time.slice(0, 5) : "";
  const endTime = block.end_time ? block.end_time.split(" ")[1]?.slice(0, 5) || block.end_time.slice(0, 5) : "";
  const timeWindow = startTime && endTime ? `${startTime} – ${endTime}` : "Window flexible";

  const durationMin = block.duration_minutes ?? 180;
  const priority = Number(block.priority ?? block.priority_score ?? 80);
  const overdueDays = block.overdue_days_projected ?? 0;
  const srs = Number(block.seasonal_risk_score_projected ?? 20);

  // Priority styling
  const priorityTone =
    priority >= 90
      ? "text-crit bg-crit/10 border-crit/30"
      : priority >= 70
        ? "text-warn bg-warn/10 border-warn/30"
        : "text-ok bg-ok/10 border-ok/30";

  return (
    <div
      onClick={() => onSelect(block)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect(block);
        }
      }}
      className={cn(
        "group relative flex flex-col justify-between rounded-lg border bg-surface p-3.5 text-xs transition-all duration-200 hover:border-primary/50 hover:shadow-md hover:shadow-primary/5 cursor-pointer",
        isSelected
          ? "border-primary ring-1 ring-primary bg-primary/5"
          : "border-border hover:bg-surface-2/40",
      )}
    >
      {/* Top Bar: Block ID, Week & Status Badges */}
      <div>
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="font-mono text-xs font-bold tracking-tight text-foreground group-hover:text-primary transition-colors">
              {block.block_id}
            </span>
            <span className="rounded bg-surface-2 px-1.5 py-0.5 text-[10px] font-semibold text-muted-foreground border border-border">
              Wk {block.week_number ?? "—"}
            </span>
            {isMega && (
              <span className="rounded bg-purple-500/15 text-purple-400 border border-purple-500/30 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider">
                Mega Block
              </span>
            )}
            {isCyclic && (
              <span className="rounded bg-info/15 text-info border border-info/30 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider">
                Cyclic
              </span>
            )}
          </div>
          <BlockStatusBadge status={block.status ?? "PROPOSED"} />
        </div>

        {/* Section & Stations */}
        <div className="mt-2.5 flex items-start gap-1.5 text-foreground">
          <MapPin className="size-3.5 shrink-0 text-primary mt-0.5" aria-hidden />
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-1.5 font-semibold text-xs truncate">
              <span className="text-primary font-mono">{block.section_id}</span>
              {fromStation && toStation ? (
                <>
                  <span className="text-muted-foreground">·</span>
                  <span className="truncate">
                    {fromStation} → {toStation}
                  </span>
                </>
              ) : null}
            </div>
            {fromName && toName && (
              <p className="text-[11px] text-muted-foreground truncate">
                {fromName} → {toName}
              </p>
            )}
            <div className="mt-0.5 flex items-center gap-2 text-[10px] text-muted-foreground font-mono">
              <span>
                Km {fromKm.toFixed(1)} – {toKm.toFixed(1)} ({lengthKm} km)
              </span>
              {section?.double_line && (
                <span className="rounded bg-surface-2 px-1 text-[9px] text-foreground font-sans">
                  Double Line
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Timing and Duration Row */}
        <div className="mt-2.5 grid grid-cols-2 gap-2 rounded bg-surface-2/60 p-2 text-[11px] border border-border/40">
          <div className="flex items-center gap-1.5">
            <Calendar className="size-3 shrink-0 text-muted-foreground" aria-hidden />
            <span className="truncate text-foreground font-medium">{formattedDate}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Clock className="size-3 shrink-0 text-muted-foreground" aria-hidden />
            <span className="truncate text-foreground font-medium">{timeWindow}</span>
          </div>
          <div className="col-span-2 flex items-center justify-between text-[10px] text-muted-foreground pt-1 border-t border-border/30">
            <span>Duration: <strong className="text-foreground">{minutesToDuration(durationMin)}</strong></span>
            <span className="font-mono">{durationMin} min</span>
          </div>
        </div>

        {/* Departments & Tasks */}
        <div className="mt-2.5 flex items-center justify-between gap-1 flex-wrap text-[11px]">
          <div className="flex items-center gap-1 flex-wrap">
            <Layers className="size-3 text-muted-foreground shrink-0" aria-hidden />
            {depts.map((dept) => (
              <span
                key={dept}
                className={cn(
                  "rounded px-1.5 py-0.2 text-[10px] font-medium border",
                  dept === "Engineering"
                    ? "bg-info/10 text-info border-info/30"
                    : dept === "TRD"
                      ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                      : "bg-ok/10 text-ok border-ok/30",
                )}
              >
                {dept}
              </span>
            ))}
          </div>
          {block.task_ids && (
            <span className="text-[10px] font-mono text-muted-foreground truncate max-w-[120px]" title={block.task_ids}>
              {block.task_ids.split(";").length} task{block.task_ids.split(";").length > 1 ? "s" : ""}
            </span>
          )}
        </div>
      </div>

      {/* Bottom Operational Footer */}
      <div className="mt-3 pt-2.5 border-t border-border/50">
        <div className="flex items-center justify-between gap-2">
          {/* MDPS Priority Score */}
          <div className="flex items-center gap-1.5">
            <span
              className={cn(
                "inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-[10px] font-mono font-bold",
                priorityTone,
              )}
            >
              <TrendingUp className="size-2.5" aria-hidden />
              MDPS {priority.toFixed(1)}
            </span>
            {overdueDays > 0 && (
              <span
                className="inline-flex items-center gap-0.5 text-[10px] font-mono text-crit"
                title={`Projected ${overdueDays} days overdue if deferred`}
              >
                <AlertTriangle className="size-2.5" aria-hidden />
                +{overdueDays}d
              </span>
            )}
          </div>

          {/* Seasonal / Train Impact */}
          <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
            {srs > 0 && (
              <span className="flex items-center gap-0.5" title={`Seasonal Risk Score: ${srs}`}>
                <CloudSun className="size-3 text-amber-400" aria-hidden />
                SRS {srs.toFixed(0)}
              </span>
            )}
            <ChevronRight className="size-3.5 text-muted-foreground group-hover:text-primary group-hover:translate-x-0.5 transition-all" aria-hidden />
          </div>
        </div>

        {/* Resources line */}
        {(block.crew || block.resources) && (
          <div className="mt-1.5 flex items-center gap-1 text-[10px] text-muted-foreground truncate">
            <Users className="size-2.5 shrink-0" aria-hidden />
            <span className="truncate">{block.crew || block.resources}</span>
          </div>
        )}
      </div>
    </div>
  );
}
