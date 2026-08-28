import { AlertTriangle, CheckCircle2, CircleDot, Clock, Sparkles, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";

export type StatusTone = "ok" | "warn" | "crit" | "info" | "ai" | "neutral";

const TONE_CLASSES: Record<StatusTone, string> = {
  ok: "bg-ok/15 text-ok border-ok/30",
  warn: "bg-warn/15 text-warn border-warn/30",
  crit: "bg-crit/15 text-crit border-crit/30",
  info: "bg-info/15 text-info border-info/30",
  ai: "bg-ai/15 text-ai border-ai/30",
  neutral: "bg-muted text-muted-foreground border-border",
};

const TONE_ICON: Record<StatusTone, React.ComponentType<{ className?: string }>> = {
  ok: CheckCircle2,
  warn: AlertTriangle,
  crit: XCircle,
  info: CircleDot,
  ai: Sparkles,
  neutral: Clock,
};

interface StatusBadgeProps {
  label: string;
  tone: StatusTone;
  className?: string;
  dense?: boolean;
}

export function StatusBadge({ label, tone, className, dense }: StatusBadgeProps) {
  const Icon = TONE_ICON[tone];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded border px-1.5 py-0.5 text-[11px] font-medium leading-none tracking-wide",
        TONE_CLASSES[tone],
        dense && "px-1 py-0.5",
        className,
      )}
    >
      <Icon className="size-3" aria-hidden />
      {label}
    </span>
  );
}

const BLOCK_STATUS_TONE: Record<string, StatusTone> = {
  DRAFT: "neutral",
  "AI RECOMMENDED": "ai",
  "PENDING APPROVAL": "warn",
  APPROVED: "ok",
  SCHEDULED: "info",
  ACTIVE: "info",
  COMPLETED: "ok",
  REJECTED: "crit",
};

export function BlockStatusBadge({ status, className }: { status: string; className?: string }) {
  return (
    <StatusBadge
      label={status}
      tone={BLOCK_STATUS_TONE[status] ?? "neutral"}
      className={className}
    />
  );
}

const TASK_STATUS_TONE: Record<string, StatusTone> = {
  Pending: "warn",
  Scheduled: "info",
  "In Progress": "info",
  Completed: "ok",
  Deferred: "crit",
};

export function TaskStatusBadge({ status, className }: { status: string; className?: string }) {
  return (
    <StatusBadge
      label={status}
      tone={TASK_STATUS_TONE[status] ?? "neutral"}
      className={className}
    />
  );
}

const AVAILABILITY_TONE: Record<string, StatusTone> = {
  Available: "ok",
  Assigned: "info",
  "Under Maintenance": "warn",
  Unavailable: "crit",
};

export function AvailabilityBadge({ status, className }: { status: string; className?: string }) {
  return (
    <StatusBadge
      label={status}
      tone={AVAILABILITY_TONE[status] ?? "neutral"}
      className={className}
    />
  );
}

const IMPACT_TONE: Record<string, StatusTone> = { Low: "ok", Medium: "warn", High: "crit" };

export function ImpactBadge({ impact, className }: { impact: string; className?: string }) {
  return (
    <StatusBadge
      label={`${impact} Impact`}
      tone={IMPACT_TONE[impact] ?? "neutral"}
      className={className}
    />
  );
}
