import { Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Department, Severity } from "@/types";

const SEVERITY_STYLE: Record<Severity, string> = {
  A: "bg-crit/15 text-crit border-crit/30",
  B: "bg-warn/15 text-warn border-warn/30",
  C: "bg-muted text-muted-foreground border-border",
};

const SEVERITY_LABEL: Record<Severity, string> = {
  A: "Sev A · Critical",
  B: "Sev B · High",
  C: "Sev C · Routine",
};

export function SeverityBadge({ severity, className }: { severity: Severity; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded border px-1.5 py-0.5 text-[11px] font-semibold leading-none",
        SEVERITY_STYLE[severity],
        className,
      )}
      title={SEVERITY_LABEL[severity]}
    >
      {severity}
    </span>
  );
}

const DEPT_STYLE: Record<Department, string> = {
  Engineering: "bg-info/15 text-info border-info/30",
  TRD: "bg-ai/15 text-ai border-ai/30",
  "S&T": "bg-ok/15 text-ok border-ok/30",
};

export function DepartmentBadge({
  department,
  className,
}: {
  department: Department;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded border px-1.5 py-0.5 text-[11px] font-medium leading-none",
        DEPT_STYLE[department],
        className,
      )}
    >
      {department}
    </span>
  );
}

export function PriorityBadge({ score, className }: { score: number; className?: string }) {
  const tone =
    score >= 85
      ? "bg-crit/15 text-crit border-crit/30"
      : score >= 60
        ? "bg-warn/15 text-warn border-warn/30"
        : "bg-ok/15 text-ok border-ok/30";
  return (
    <span
      className={cn(
        "inline-flex items-center rounded border px-1.5 py-0.5 text-[11px] font-mono font-semibold leading-none tabular-nums",
        tone,
        className,
      )}
    >
      {score}
    </span>
  );
}

export function AIBadge({
  className,
  label = "AI Recommended",
}: {
  className?: string;
  label?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded border border-ai/30 bg-ai/15 px-1.5 py-0.5 text-[11px] font-medium leading-none text-ai",
        className,
      )}
    >
      <Sparkles className="size-3" aria-hidden />
      {label}
    </span>
  );
}
