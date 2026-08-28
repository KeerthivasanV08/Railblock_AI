import { useNavigate } from "@tanstack/react-router";
import { Check, ChevronRight, PlayCircle, Sparkles, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AIBadge, DepartmentBadge } from "@/components/common/DomainBadges";
import { ImpactBadge, StatusBadge } from "@/components/common/StatusBadge";
import { toHHMM } from "@/utils/dateUtils";
import { pct } from "@/utils/formatters";
import type { AIRecommendation } from "@/types";

const STATUS_TONE = {
  Pending: "warn",
  Approved: "ok",
  Rejected: "crit",
  Modified: "info",
} as const;

export function RecommendationCard({
  rec,
  onApprove,
  onReject,
  onModify,
  onSimulate,
  compact,
}: {
  rec: AIRecommendation;
  onApprove: () => void;
  onReject: () => void;
  onModify: () => void;
  onSimulate: () => void;
  compact?: boolean;
}) {
  const navigate = useNavigate();
  return (
    <div className="rounded-md border border-border bg-surface p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-1.5">
            <AIBadge label="AI Recommendation" />
            <StatusBadge label={rec.status} tone={STATUS_TONE[rec.status]} />
          </div>
          <button
            className="mt-1.5 flex items-center gap-1 font-mono text-sm font-semibold text-foreground hover:underline"
            onClick={() =>
              navigate({
                to: "/recommendations/$recommendationId",
                params: { recommendationId: rec.recommendation_id },
              })
            }
          >
            Block {rec.block_id}
            <ChevronRight className="size-3.5" aria-hidden />
          </button>
          <p className="text-xs text-muted-foreground">
            {toHHMM(rec.start_min)} – {toHHMM(rec.start_min + rec.duration_min)} · {rec.section_id}
          </p>
        </div>
        <div className="text-right">
          <p className="font-mono text-2xl font-bold tabular-nums text-foreground">
            {rec.priority}
          </p>
          <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Priority</p>
        </div>
      </div>

      <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
        {rec.departments.map((d) => (
          <DepartmentBadge key={d} department={d} />
        ))}
        <span className="text-[11px] text-muted-foreground">
          {rec.task_ids.length || "—"} tasks
        </span>
        <span className="text-[11px] text-muted-foreground">
          · {pct(rec.utilization)} utilization
        </span>
        <ImpactBadge impact={rec.train_impact} />
        <span className="text-[11px] text-muted-foreground">· {rec.confidence}% confidence</span>
      </div>

      {!compact && (
        <div className="mt-3 space-y-1">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            Why recommended?
          </p>
          {rec.reasons.map((r) => (
            <p key={r} className="flex items-start gap-1.5 text-xs text-foreground">
              <Check className="mt-0.5 size-3 shrink-0 text-ok" aria-hidden />
              {r}
            </p>
          ))}
        </div>
      )}

      <div className="mt-3 grid grid-cols-4 gap-1.5">
        <Button
          size="sm"
          className="col-span-1 gap-1 bg-ok text-ok-foreground hover:bg-ok/90"
          onClick={onApprove}
          disabled={rec.status === "Approved"}
        >
          <Check className="size-3.5" aria-hidden /> Approve
        </Button>
        <Button size="sm" variant="outline" className="gap-1" onClick={onModify}>
          <Sparkles className="size-3.5" aria-hidden /> Modify
        </Button>
        <Button
          size="sm"
          variant="outline"
          className="gap-1 border-crit/40 text-crit hover:bg-crit/10"
          onClick={onReject}
        >
          <X className="size-3.5" aria-hidden /> Reject
        </Button>
        <Button size="sm" variant="outline" className="gap-1" onClick={onSimulate}>
          <PlayCircle className="size-3.5" aria-hidden /> Simulate
        </Button>
      </div>
    </div>
  );
}
