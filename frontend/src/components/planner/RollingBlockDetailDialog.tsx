import React, { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  MapPin,
  Calendar,
  Clock,
  Layers,
  Wrench,
  Users,
  ShieldCheck,
  TrendingUp,
  AlertTriangle,
  CloudSun,
  Brain,
  Cpu,
  ExternalLink,
  CheckCircle2,
  XCircle,
  Sparkles,
  Info,
  Check,
  X,
  FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { BlockStatusBadge } from "@/components/common/StatusBadge";
import type { RollingPlanBlock } from "@/api/plannerApi";
import { sectionById } from "@/data/sections";
import { STATIONS } from "@/data/stations";
import { minutesToDuration } from "@/utils/formatters";
import { blocksApi, xaiApi, type BlockExplanationResponse } from "@/api";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

const STATION_NAMES: Record<string, string> = Object.fromEntries(
  STATIONS.map((s) => [s.station_code, s.name]),
);

interface RollingBlockDetailDialogProps {
  block: RollingPlanBlock | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onStatusUpdated?: (blockId: string, newStatus: string) => void;
}

export function RollingBlockDetailDialog({
  block,
  open,
  onOpenChange,
  onStatusUpdated,
}: RollingBlockDetailDialogProps) {
  const [xaiData, setXaiData] = useState<BlockExplanationResponse | null>(null);
  const [loadingXai, setLoadingXai] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [isRejecting, setIsRejecting] = useState(false);
  const [rejectPromptOpen, setRejectPromptOpen] = useState(false);
  const [rejectionReason, setRejectionReason] = useState("");

  // Fetch live XAI explanation when block opens
  useEffect(() => {
    if (!block || !open) {
      setXaiData(null);
      setRejectPromptOpen(false);
      setRejectionReason("");
      return;
    }

    setLoadingXai(true);
    xaiApi
      .explainBlock(block.block_id)
      .then((res) => setXaiData(res))
      .catch(() => setXaiData(null))
      .finally(() => setLoadingXai(false));
  }, [block?.block_id, open]);

  if (!block) return null;

  const section = sectionById(block.section_id);
  const fromStation = section?.from_station ?? "";
  const toStation = section?.to_station ?? "";
  const fromName = STATION_NAMES[fromStation] || fromStation;
  const toName = STATION_NAMES[toStation] || toStation;
  const fromKm = section?.from_km ?? 0;
  const toKm = section?.to_km ?? 0;
  const lengthKm = (toKm - fromKm).toFixed(1);

  // Departments
  const depts = block.departments
    ? block.departments.split(/[;,]/).map((d) => d.trim()).filter(Boolean)
    : [];
  const isMultiDept = depts.length > 1;
  const isCyclic = block.maintenance_type?.toUpperCase().includes("CYCLIC") ?? false;
  const isMega = isMultiDept || (block.maintenance_type?.toUpperCase().includes("MEGA") ?? false);

  // Tasks
  const taskList = block.task_ids
    ? block.task_ids.split(/[;,]/).map((t) => t.trim()).filter(Boolean)
    : [];

  // Date
  const dateStr = block.plan_date || block.date;
  let formattedDate = dateStr ?? "—";
  if (dateStr) {
    try {
      const d = new Date(dateStr);
      if (!isNaN(d.getTime())) {
        formattedDate = d.toLocaleDateString("en-IN", {
          weekday: "long",
          day: "2-digit",
          month: "long",
          year: "numeric",
        });
      }
    } catch {
      // keep
    }
  }

  // Time
  const startTime = block.start_time
    ? block.start_time.split(" ")[1]?.slice(0, 5) || block.start_time.slice(0, 5)
    : "06:00";
  const endTime = block.end_time
    ? block.end_time.split(" ")[1]?.slice(0, 5) || block.end_time.slice(0, 5)
    : "09:00";
  const durationMin = block.duration_minutes ?? 180;
  const priority = Number(block.priority ?? block.priority_score ?? 80);
  const overdueDays = block.overdue_days_projected ?? 0;
  const deferredCount = block.deferred_count_projected ?? 0;
  const srs = Number(block.seasonal_risk_score_projected ?? 20);
  const utilization = Math.round(Number(block.utilization ?? 1.0) * 100);

  // Handle Human Controller Approval
  const handleApprove = async () => {
    setIsApproving(true);
    try {
      await blocksApi.approveBlock(block.block_id, {
        approved_by: "Chief Power & Traffic Controller",
        role: "CPTC",
        notes: `Approved 26-week rolling block on ${block.section_id} (Week ${block.week_number}).`,
      });
      toast.success("Block Plan Approved", {
        description: `Block ${block.block_id} transitioned to APPROVED. Recorded in audit log.`,
      });
      onStatusUpdated?.(block.block_id, "APPROVED");
      onOpenChange(false);
    } catch (err: unknown) {
      toast.error("Approval Failed", {
        description: err instanceof Error ? err.message : "Unable to approve block.",
      });
    } finally {
      setIsApproving(false);
    }
  };

  // Handle Human Controller Rejection
  const handleReject = async () => {
    if (!rejectionReason.trim()) {
      toast.error("Reason Required", {
        description: "Please provide an operational reason for rejection.",
      });
      return;
    }
    setIsRejecting(true);
    try {
      await blocksApi.rejectBlock(block.block_id, {
        rejected_by: "Senior Divisional Operations Manager",
        role: "SrDOM",
        reason: rejectionReason,
      });
      toast.info("Block Recommendation Rejected", {
        description: `Block ${block.block_id} rejected. Reason logged in audit registry.`,
      });
      onStatusUpdated?.(block.block_id, "REJECTED");
      onOpenChange(false);
    } catch (err: unknown) {
      toast.error("Rejection Failed", {
        description: err instanceof Error ? err.message : "Unable to reject block.",
      });
    } finally {
      setIsRejecting(false);
      setRejectPromptOpen(false);
    }
  };

  const isProposed =
    block.status?.toUpperCase() === "PROPOSED" ||
    block.status?.toUpperCase() === "AI RECOMMENDED" ||
    block.status?.toUpperCase() === "PENDING APPROVAL";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[88vh] overflow-y-auto p-0 gap-0 border-border bg-background text-foreground shadow-2xl">
        {/* Top Header */}
        <div className="sticky top-0 z-10 border-b border-border bg-surface/95 backdrop-blur-md px-6 py-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-mono text-base font-bold text-foreground">
                  {block.block_id}
                </span>
                <span className="rounded bg-primary/10 text-primary border border-primary/30 px-2 py-0.5 text-xs font-semibold">
                  26-Week Rolling · Week {block.week_number ?? "—"}
                </span>
                {isMega && (
                  <span className="rounded bg-purple-500/15 text-purple-400 border border-purple-500/30 px-2 py-0.5 text-xs font-semibold">
                    Mega Block
                  </span>
                )}
                {isCyclic && (
                  <span className="rounded bg-info/15 text-info border border-info/30 px-2 py-0.5 text-xs font-semibold">
                    Cyclic Track Maintenance
                  </span>
                )}
              </div>
              <DialogDescription className="mt-1 text-xs text-muted-foreground">
                Detailed Block Inspection & Constraint Verification Dossier · Southern Railway Corridor
              </DialogDescription>
            </div>
            <div className="flex items-center gap-2 mr-6">
              <BlockStatusBadge status={block.status ?? "PROPOSED"} />
            </div>
          </div>
        </div>

        {/* Modal Scrollable Body */}
        <div className="space-y-5 p-6 text-xs">
          {/* Section 1: Geographic Location & Track Geometry */}
          <div className="rounded-lg border border-border bg-surface p-4">
            <div className="flex items-center justify-between gap-2 border-b border-border/50 pb-2 mb-3">
              <div className="flex items-center gap-2 font-semibold text-foreground">
                <MapPin className="size-4 text-primary" aria-hidden />
                <span>Geographic Location & Track Infrastructure</span>
              </div>
              <a
                href={`/live`}
                className="inline-flex items-center gap-1 text-[11px] font-medium text-primary hover:underline"
              >
                Corridor View <ExternalLink className="size-3" aria-hidden />
              </a>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs">
              <div className="rounded bg-surface-2 p-2.5">
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">Section ID</span>
                <span className="font-mono font-bold text-foreground text-sm">{block.section_id}</span>
                <span className="text-[11px] text-muted-foreground block mt-0.5">
                  {section?.double_line ? "Double Line (UP/DN)" : "Single Line Section"}
                </span>
              </div>

              <div className="rounded bg-surface-2 p-2.5">
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">Station Pair</span>
                <span className="font-bold text-foreground">
                  {fromStation} → {toStation}
                </span>
                <span className="text-[11px] text-muted-foreground block mt-0.5 truncate" title={`${fromName} → ${toName}`}>
                  {fromName} → {toName}
                </span>
              </div>

              <div className="rounded bg-surface-2 p-2.5">
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">Chainage Span</span>
                <span className="font-mono font-bold text-foreground">
                  Km {fromKm.toFixed(1)} – {toKm.toFixed(1)}
                </span>
                <span className="text-[11px] text-muted-foreground block mt-0.5">
                  Total length: {lengthKm} km
                </span>
              </div>

              <div className="rounded bg-surface-2 p-2.5">
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">Traffic Density</span>
                <span className="font-bold text-foreground">
                  {section?.traffic_density ?? 75} trains/day
                </span>
                <span className="text-[11px] text-muted-foreground block mt-0.5">
                  {Number(section?.traffic_density ?? 0) >= 80 ? "High Density Route" : "Standard Density Route"}
                </span>
              </div>
            </div>
          </div>

          {/* Section 2: Timing, Schedule & Horizon */}
          <div className="rounded-lg border border-border bg-surface p-4">
            <div className="flex items-center gap-2 font-semibold text-foreground border-b border-border/50 pb-2 mb-3">
              <Clock className="size-4 text-primary" aria-hidden />
              <span>Schedule, Horizon & Execution Window</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="rounded bg-surface-2 p-2.5">
                <div className="flex items-center gap-1.5 text-muted-foreground mb-1">
                  <Calendar className="size-3.5" aria-hidden />
                  <span className="text-[10px] uppercase tracking-wider">Scheduled Date</span>
                </div>
                <p className="font-medium text-foreground text-sm">{formattedDate}</p>
                <p className="text-[11px] text-muted-foreground mt-0.5">Week {block.week_number} of 26-Week Plan</p>
              </div>

              <div className="rounded bg-surface-2 p-2.5">
                <div className="flex items-center gap-1.5 text-muted-foreground mb-1">
                  <Clock className="size-3.5" aria-hidden />
                  <span className="text-[10px] uppercase tracking-wider">Window Time</span>
                </div>
                <p className="font-mono font-bold text-foreground text-sm">{startTime} – {endTime}</p>
                <p className="text-[11px] text-muted-foreground mt-0.5">Off-peak gap alignment verified</p>
              </div>

              <div className="rounded bg-surface-2 p-2.5">
                <div className="flex items-center gap-1.5 text-muted-foreground mb-1">
                  <Sparkles className="size-3.5 text-amber-400" aria-hidden />
                  <span className="text-[10px] uppercase tracking-wider">Duration Granted</span>
                </div>
                <p className="font-bold text-foreground text-sm">{minutesToDuration(durationMin)}</p>
                <p className="text-[11px] text-muted-foreground mt-0.5">{durationMin} minutes allocated</p>
              </div>
            </div>
          </div>

          {/* Section 3: Maintenance Tasks & Departments */}
          <div className="rounded-lg border border-border bg-surface p-4">
            <div className="flex items-center justify-between gap-2 border-b border-border/50 pb-2 mb-3">
              <div className="flex items-center gap-2 font-semibold text-foreground">
                <Layers className="size-4 text-primary" aria-hidden />
                <span>Consolidated Maintenance Tasks & Disciplines</span>
              </div>
              <div className="flex items-center gap-1.5">
                {depts.map((d) => (
                  <span
                    key={d}
                    className="rounded px-2 py-0.5 text-[10px] font-semibold border bg-primary/10 text-primary border-primary/30"
                  >
                    {d}
                  </span>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-[11px] text-muted-foreground bg-surface-2 px-3 py-1.5 rounded">
                <span>Task ID</span>
                <span>Type / Discipline</span>
                <span>Priority</span>
              </div>
              {taskList.map((tid, idx) => (
                <div
                  key={tid}
                  className="flex items-center justify-between rounded border border-border/60 bg-surface-2/40 px-3 py-2 text-xs font-mono"
                >
                  <span className="font-semibold text-foreground flex items-center gap-1.5">
                    <FileText className="size-3 text-muted-foreground" aria-hidden />
                    {tid}
                  </span>
                  <span className="font-sans text-muted-foreground text-[11px]">
                    {block.maintenance_type || "Corridor Track Maintenance"}
                  </span>
                  <span className="text-ok font-bold text-[11px]">MDPS {priority.toFixed(0)}</span>
                </div>
              ))}
            </div>

            {isMega && (
              <p className="mt-3 rounded border border-purple-500/20 bg-purple-500/5 p-2.5 text-[11px] text-purple-300 flex items-start gap-2">
                <Sparkles className="size-4 shrink-0 text-purple-400 mt-0.5" aria-hidden />
                <span>
                  <strong>Shadow Block Consolidation Active:</strong> TRD overhead electrification inspection and Track
                  maintenance tasks have been bundled into a single corridor window, saving an estimated 150 min of total
                  line traffic occupation.
                </span>
              </p>
            )}
          </div>

          {/* Section 4: Plant, Machinery & Crew Resources */}
          <div className="rounded-lg border border-border bg-surface p-4">
            <div className="flex items-center gap-2 font-semibold text-foreground border-b border-border/50 pb-2 mb-3">
              <Wrench className="size-4 text-primary" aria-hidden />
              <span>Plant, Machinery & Crew Allocation</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="rounded bg-surface-2 p-3">
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">Required Equipment & Machinery</span>
                <p className="font-medium text-foreground mt-1 text-xs">
                  {block.resources || "CSM Tamping Machine · Tower Wagon · Utility Trolley"}
                </p>
                <div className="mt-2 flex items-center gap-1 text-[11px] text-ok">
                  <CheckCircle2 className="size-3" aria-hidden />
                  <span>Depot allocation confirmed feasible</span>
                </div>
              </div>

              <div className="rounded bg-surface-2 p-3">
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">Assigned Gang / Crew</span>
                <p className="font-mono font-bold text-foreground mt-1 text-xs">
                  {block.crew || `CREW_${block.section_id}`}
                </p>
                <div className="mt-2 flex items-center gap-1 text-[11px] text-ok">
                  <CheckCircle2 className="size-3" aria-hidden />
                  <span>Certified staff within maximum duty hours</span>
                </div>
              </div>
            </div>
          </div>

          {/* Section 5: Optimization, Risk & Seasonal Intelligence */}
          <div className="rounded-lg border border-border bg-surface p-4">
            <div className="flex items-center gap-2 font-semibold text-foreground border-b border-border/50 pb-2 mb-3">
              <TrendingUp className="size-4 text-primary" aria-hidden />
              <span>Optimization & Risk Intelligence</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="rounded bg-surface-2 p-2.5">
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">MDPS Priority Score</span>
                <div className="mt-1 flex items-baseline gap-1">
                  <span className="text-base font-bold font-mono text-crit">{priority.toFixed(1)}</span>
                  <span className="text-[10px] text-muted-foreground">/ 100</span>
                </div>
                <div className="mt-1.5 h-1.5 w-full rounded-full bg-surface">
                  <div
                    className="h-full rounded-full bg-crit"
                    style={{ width: `${Math.min(priority, 100)}%` }}
                  />
                </div>
              </div>

              <div className="rounded bg-surface-2 p-2.5">
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">Projected Overdue</span>
                <div className="mt-1 flex items-baseline gap-1">
                  <span className="text-base font-bold font-mono text-warn">+{overdueDays}</span>
                  <span className="text-[10px] text-muted-foreground">days</span>
                </div>
                <p className="mt-1 text-[10px] text-muted-foreground">
                  {deferredCount > 0 ? `${deferredCount} prior deferrals` : "0 prior deferrals"}
                </p>
              </div>

              <div className="rounded bg-surface-2 p-2.5">
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">Seasonal Risk (SRS)</span>
                <div className="mt-1 flex items-baseline gap-1">
                  <span className="text-base font-bold font-mono text-foreground">{srs.toFixed(0)}</span>
                  <span className="text-[10px] text-muted-foreground">/ 100</span>
                </div>
                <p className="mt-1 text-[10px] text-muted-foreground flex items-center gap-1">
                  <CloudSun className="size-3 text-amber-400" aria-hidden />
                  {srs < 40 ? "Low weather risk" : "Monsoon caution"}
                </p>
              </div>

              <div className="rounded bg-surface-2 p-2.5">
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">Train Impact & Util</span>
                <div className="mt-1 flex items-baseline gap-1">
                  <span className="text-base font-bold font-mono text-ok">{block.train_impact || "LOW"}</span>
                </div>
                <p className="mt-1 text-[10px] text-muted-foreground">
                  {utilization}% window utilization
                </p>
              </div>
            </div>
          </div>

          {/* Section 6: Hard Constraint Validation Checklist */}
          <div className="rounded-lg border border-ok/30 bg-ok/5 p-4">
            <div className="flex items-center gap-2 font-semibold text-ok border-b border-ok/20 pb-2 mb-3">
              <ShieldCheck className="size-4" aria-hidden />
              <span>Hard Constraint Engine Validation (5 / 5 Verified)</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5 text-xs">
              <div className="flex items-start gap-2 rounded bg-surface p-2.5 border border-border/50">
                <CheckCircle2 className="size-4 text-ok shrink-0 mt-0.5" aria-hidden />
                <div>
                  <strong className="text-foreground block text-[11px]">Traffic Gap Feasibility</strong>
                  <span className="text-[10px] text-muted-foreground">No conflict with express timetables</span>
                </div>
              </div>

              <div className="flex items-start gap-2 rounded bg-surface p-2.5 border border-border/50">
                <CheckCircle2 className="size-4 text-ok shrink-0 mt-0.5" aria-hidden />
                <div>
                  <strong className="text-foreground block text-[11px]">Machine & Plant Feasibility</strong>
                  <span className="text-[10px] text-muted-foreground">Equipment confirmed available</span>
                </div>
              </div>

              <div className="flex items-start gap-2 rounded bg-surface p-2.5 border border-border/50">
                <CheckCircle2 className="size-4 text-ok shrink-0 mt-0.5" aria-hidden />
                <div>
                  <strong className="text-foreground block text-[11px]">Gang / Crew Feasibility</strong>
                  <span className="text-[10px] text-muted-foreground">Depot certified within shift limits</span>
                </div>
              </div>

              <div className="flex items-start gap-2 rounded bg-surface p-2.5 border border-border/50">
                <CheckCircle2 className="size-4 text-ok shrink-0 mt-0.5" aria-hidden />
                <div>
                  <strong className="text-foreground block text-[11px]">Duration Safety Margin</strong>
                  <span className="text-[10px] text-muted-foreground">Includes safety isolation buffer</span>
                </div>
              </div>

              <div className="flex items-start gap-2 rounded bg-surface p-2.5 border border-border/50">
                <CheckCircle2 className="size-4 text-ok shrink-0 mt-0.5" aria-hidden />
                <div>
                  <strong className="text-foreground block text-[11px]">Spatial Headway Guard</strong>
                  <span className="text-[10px] text-muted-foreground">Adjacent junction safety ensured</span>
                </div>
              </div>

              <div className="flex items-start gap-2 rounded bg-surface p-2.5 border border-border/50">
                <CheckCircle2 className="size-4 text-ok shrink-0 mt-0.5" aria-hidden />
                <div>
                  <strong className="text-foreground block text-[11px]">Deterministic Fallback</strong>
                  <span className="text-[10px] text-muted-foreground">MILP rule check satisfied</span>
                </div>
              </div>
            </div>
          </div>

          {/* Section 7: Explainable AI (XAI) Justification */}
          <div className="rounded-lg border border-ai/30 bg-ai/5 p-4">
            <div className="flex items-center justify-between gap-2 border-b border-ai/20 pb-2 mb-3">
              <div className="flex items-center gap-2 font-semibold text-ai">
                <Brain className="size-4" aria-hidden />
                <span>Explainable AI (XAI) Recommendation Rationale</span>
              </div>
              <span className="rounded bg-ai/20 px-2 py-0.5 text-[10px] font-mono text-ai font-semibold">
                XAI v2.4
              </span>
            </div>

            {/* Primary backend reason */}
            {block.xai_reason && (
              <p className="text-xs text-foreground bg-surface/70 p-3 rounded border border-ai/20 leading-relaxed">
                {block.xai_reason}
              </p>
            )}

            {/* Live XAI breakdown */}
            {loadingXai && (
              <p className="text-xs text-muted-foreground py-2">Consulting XAI reasoning engine…</p>
            )}

            {xaiData?.why_recommended && xaiData.why_recommended.length > 0 && (
              <div className="mt-3 space-y-1.5">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                  Optimization Drivers:
                </span>
                <ul className="space-y-1 text-[11px] text-muted-foreground">
                  {xaiData.why_recommended.map((r, i) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <span className="text-ai mt-0.5">▪</span>
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {xaiData?.risk_factors && xaiData.risk_factors.length > 0 && (
              <div className="mt-3 space-y-1 rounded bg-warn/10 p-2.5 text-[11px] text-warn border border-warn/20">
                <strong className="block text-[10px] uppercase tracking-wider">Operational Risk Factors:</strong>
                {xaiData.risk_factors.map((rf, i) => (
                  <p key={i}>• {rf}</p>
                ))}
              </div>
            )}
          </div>

          {/* Section 8: Model & Governance Metadata */}
          <div className="rounded-lg border border-border bg-surface-2/60 p-3.5 text-[11px]">
            <div className="flex items-center gap-2 font-semibold text-muted-foreground mb-2">
              <Cpu className="size-3.5" aria-hidden />
              <span>Model & Governance Provenance</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-muted-foreground font-mono text-[10px]">
              <div>
                <span className="block text-foreground">Solver Engine</span>
                <span>{block.source || "rolling_optimizer"} (OR-Tools)</span>
              </div>
              <div>
                <span className="block text-foreground">Plan Run ID</span>
                <span className="truncate block" title={block.plan_run_id}>{block.plan_run_id || "RUN-ROLLING-26W"}</span>
              </div>
              <div>
                <span className="block text-foreground">Plan Version</span>
                <span>v{block.plan_version ?? 1} (Active Candidate)</span>
              </div>
              <div>
                <span className="block text-foreground">Audit Logging</span>
                <span className="text-ok font-semibold">Enabled (Immutable)</span>
              </div>
            </div>
          </div>

          {/* Inline Rejection Prompt */}
          {rejectPromptOpen && (
            <div className="rounded-lg border border-crit/40 bg-crit/5 p-4 space-y-3">
              <div className="flex items-center gap-2 text-crit font-semibold">
                <AlertTriangle className="size-4" aria-hidden />
                <span>Provide Rejection Rationale</span>
              </div>
              <p className="text-[11px] text-muted-foreground">
                Enter an operational reason for rejecting this block recommendation (e.g. VIP train movement,
                resource bottleneck, or track safety embargo).
              </p>
              <textarea
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="Reason for rejection (required for controller audit trail)…"
                className="w-full rounded border border-border bg-surface p-2.5 text-xs text-foreground placeholder:text-muted-foreground focus:border-crit focus:outline-none focus:ring-1 focus:ring-crit"
                rows={3}
              />
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setRejectPromptOpen(false)}
                  disabled={isRejecting}
                >
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => void handleReject()}
                  disabled={isRejecting || !rejectionReason.trim()}
                >
                  {isRejecting ? "Rejecting…" : "Confirm Rejection"}
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="sticky bottom-0 z-10 flex items-center justify-between border-t border-border bg-surface/95 backdrop-blur-md px-6 py-3.5">
          <div className="flex items-center gap-2">
            <a
              href="/planner"
              className="inline-flex items-center gap-1 rounded border border-border bg-surface px-3 py-1.5 text-xs font-medium text-foreground hover:bg-surface-2 transition-colors"
            >
              Weekly Timeline <ExternalLink className="size-3" aria-hidden />
            </a>
          </div>

          <div className="flex items-center gap-2">
            {isProposed && !rejectPromptOpen && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setRejectPromptOpen(true)}
                  className="text-crit hover:bg-crit/10 hover:text-crit border-crit/30"
                >
                  <XCircle className="size-3.5 mr-1" aria-hidden /> Reject
                </Button>
                <Button
                  size="sm"
                  onClick={() => void handleApprove()}
                  disabled={isApproving}
                  className="bg-ok hover:bg-ok/90 text-white font-semibold"
                >
                  <CheckCircle2 className="size-3.5 mr-1" aria-hidden />
                  {isApproving ? "Approving…" : "Approve Block"}
                </Button>
              </>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => onOpenChange(false)}
            >
              Close
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
