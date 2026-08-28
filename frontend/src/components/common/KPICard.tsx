import type { LucideIcon } from "lucide-react";
import { TrendingDown, TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";
import type { StatusTone } from "./StatusBadge";

interface KPICardProps {
  label: string;
  value: string;
  icon: LucideIcon;
  trendLabel?: string;
  trendDirection?: "up" | "down" | "flat";
  statusLabel?: string;
  tone?: StatusTone;
  onClick?: () => void;
  className?: string;
}

const TONE_STYLES: Record<StatusTone, { iconBg: string; iconColor: string; borderAccent: string }> =
  {
    ok: { iconBg: "bg-ok/10", iconColor: "text-ok", borderAccent: "border-t-ok" },
    warn: {
      iconBg: "bg-warn/15",
      iconColor: "text-warn-foreground",
      borderAccent: "border-t-warn",
    },
    crit: { iconBg: "bg-crit/10", iconColor: "text-crit", borderAccent: "border-t-crit" },
    info: { iconBg: "bg-info/10", iconColor: "text-info", borderAccent: "border-t-info" },
    ai: { iconBg: "bg-ai/10", iconColor: "text-ai", borderAccent: "border-t-ai" },
    neutral: {
      iconBg: "bg-muted",
      iconColor: "text-muted-foreground",
      borderAccent: "border-t-border-strong",
    },
  };

export function KPICard({
  label,
  value,
  icon: Icon,
  trendLabel,
  trendDirection = "flat",
  statusLabel,
  tone = "neutral",
  onClick,
  className,
}: KPICardProps) {
  const Tag = onClick ? "button" : "div";
  const styles = TONE_STYLES[tone] || TONE_STYLES.neutral;

  return (
    <Tag
      onClick={onClick}
      className={cn(
        "flex flex-col justify-between gap-2.5 rounded-lg border border-border bg-surface p-3 text-left shadow-xs transition-all min-w-0 overflow-hidden",
        "border-t-2",
        styles.borderAccent,
        onClick &&
          "cursor-pointer hover:border-border-strong hover:shadow-sm hover:translate-y-[-1px]",
        className,
      )}
    >
      <div className="flex items-center justify-between gap-1.5 min-w-0">
        <span className="text-[10px] sm:text-[11px] font-semibold tracking-wider text-muted-foreground uppercase truncate">
          {label}
        </span>
        <span className={cn("flex size-6 sm:size-7 shrink-0 items-center justify-center rounded-md", styles.iconBg)}>
          <Icon className={cn("size-3.5 sm:size-4", styles.iconColor)} aria-hidden />
        </span>
      </div>

      <div className="font-mono text-xl sm:text-2xl font-bold tracking-tight text-foreground tabular-nums truncate">
        {value}
      </div>

      <div className="flex items-center justify-between gap-1.5 border-t border-border/60 pt-2 text-[10px] sm:text-[11px] min-w-0">
        {trendLabel ? (
          <span
            className={cn(
              "inline-flex items-center gap-1 font-medium truncate shrink-0",
              trendDirection === "up"
                ? "text-ok"
                : trendDirection === "down"
                  ? "text-crit"
                  : "text-muted-foreground",
            )}
          >
            {trendDirection === "up" && <TrendingUp className="size-3 shrink-0" aria-hidden />}
            {trendDirection === "down" && <TrendingDown className="size-3 shrink-0" aria-hidden />}
            <span className="truncate">{trendLabel}</span>
          </span>
        ) : (
          <span />
        )}
        {statusLabel && (
          <span className="inline-flex items-center gap-1.5 font-medium text-muted-foreground truncate ml-auto">
            <span
              className={cn(
                "size-1.5 rounded-full shrink-0",
                styles.iconColor === "text-ok"
                  ? "bg-ok"
                  : styles.iconColor === "text-crit"
                    ? "bg-crit"
                    : styles.iconColor === "text-warn-foreground"
                      ? "bg-warn"
                      : "bg-muted-foreground",
              )}
              aria-hidden
            />
            <span className="truncate">{statusLabel}</span>
          </span>
        )}
      </div>
    </Tag>
  );
}
