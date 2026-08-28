import { useState } from "react";
import { toast } from "sonner";
import { Check, X } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/States";
import { Button } from "@/components/ui/button";
import { AIBadge, DepartmentBadge } from "@/components/common/DomainBadges";
import { ImpactBadge, StatusBadge } from "@/components/common/StatusBadge";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { toHHMM } from "@/utils/dateUtils";
import { pct } from "@/utils/formatters";
import { useRecommendationStore } from "@/stores/recommendationStore";
import { useTaskStore } from "@/stores/taskStore";
import { ModifyRecommendationDialog } from "./ModifyRecommendationDialog";

const STATUS_TONE = {
  Pending: "warn",
  Approved: "ok",
  Rejected: "crit",
  Modified: "info",
} as const;

export function RecommendationDetailPage({ recommendationId }: { recommendationId: string }) {
  const rec = useRecommendationStore((s) =>
    s.recommendations.find((r) => r.recommendation_id === recommendationId),
  );
  const { approve, reject, modify } = useRecommendationStore();
  const tasks = useTaskStore((s) => s.tasks);
  const [rejectOpen, setRejectOpen] = useState(false);
  const [modifyOpen, setModifyOpen] = useState(false);

  if (!rec) {
    return (
      <div className="flex h-full flex-col">
        <PageHeader
          title="Recommendation not found"
          crumbs={[
            { label: "AI Recommendations", to: "/recommendations" },
            { label: recommendationId },
          ]}
        />
        <EmptyState className="m-6" title={`No recommendation ${recommendationId}`} />
      </div>
    );
  }

  const relatedTasks = tasks.filter((t) => rec.task_ids.includes(t.task_id));

  return (
    <div className="flex h-full flex-col overflow-auto">
      <PageHeader
        title={`Recommendation ${rec.recommendation_id}`}
        description={`Block ${rec.block_id} · ${rec.section_id}`}
        crumbs={[
          { label: "AI Recommendations", to: "/recommendations" },
          { label: rec.recommendation_id },
        ]}
        badge={<StatusBadge label={rec.status} tone={STATUS_TONE[rec.status]} />}
        actions={
          <>
            <Button
              size="sm"
              className="gap-1.5 bg-ok text-ok-foreground hover:bg-ok/90"
              onClick={() => {
                approve(rec.recommendation_id);
                toast.success("Block approved successfully.");
              }}
              disabled={rec.status === "Approved"}
            >
              <Check className="size-3.5" aria-hidden /> Approve
            </Button>
            <Button size="sm" variant="outline" onClick={() => setModifyOpen(true)}>
              Modify
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="gap-1.5 border-crit/40 text-crit hover:bg-crit/10"
              onClick={() => setRejectOpen(true)}
            >
              <X className="size-3.5" aria-hidden /> Reject
            </Button>
          </>
        }
      />

      <div className="grid flex-1 grid-cols-1 gap-4 p-4 lg:grid-cols-[1.1fr_1fr]">
        <div className="space-y-4">
          <div className="rounded-md border border-border bg-surface p-4">
            <div className="flex items-center gap-1.5">
              <AIBadge label="AI Recommendation" />
            </div>
            <p className="mt-2 font-mono text-lg font-semibold">
              {toHHMM(rec.start_min)} – {toHHMM(rec.start_min + rec.duration_min)}
            </p>
            <div className="mt-2 flex flex-wrap items-center gap-1.5">
              {rec.departments.map((d) => (
                <DepartmentBadge key={d} department={d} />
              ))}
              <ImpactBadge impact={rec.train_impact} />
            </div>
            <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
              <Metric label="Tasks" value={String(rec.task_ids.length)} />
              <Metric label="Utilization" value={pct(rec.utilization)} />
              <Metric label="Confidence" value={`${rec.confidence}%`} />
            </div>
          </div>

          <div className="rounded-md border border-ai/30 bg-ai/5 p-4">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-ai">
              Why recommended?
            </p>
            <div className="mt-2 space-y-1.5">
              {rec.reasons.map((r) => (
                <p key={r} className="flex items-start gap-1.5 text-sm text-foreground">
                  <Check className="mt-0.5 size-3.5 shrink-0 text-ok" aria-hidden /> {r}
                </p>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-md border border-border bg-surface p-4">
            <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              Recommendation Factors
            </p>
            <div className="space-y-2.5">
              {rec.factors.map((f) => (
                <div key={f.label}>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-foreground">{f.label}</span>
                    <span className="font-mono text-muted-foreground">{f.value}</span>
                  </div>
                  <div className="mt-1 h-1.5 rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-ai"
                      style={{ width: `${Math.min(100, f.value)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-md border border-border bg-surface p-4">
            <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              Related tasks ({relatedTasks.length})
            </p>
            <div className="space-y-1.5">
              {relatedTasks.length === 0 ? (
                <p className="text-xs text-muted-foreground">No individual tasks linked.</p>
              ) : (
                relatedTasks.map((t) => (
                  <div
                    key={t.task_id}
                    className="rounded border border-border px-2 py-1.5 text-[11px]"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-medium">{t.task_id}</span>
                      <DepartmentBadge department={t.department} />
                    </div>
                    <p className="mt-0.5 text-muted-foreground">{t.defect}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      <ConfirmDialog
        open={rejectOpen}
        onOpenChange={setRejectOpen}
        title={`Reject ${rec.recommendation_id}?`}
        description="This marks the recommendation and its block as rejected."
        confirmLabel="Reject"
        destructive
        onConfirm={() => {
          reject(rec.recommendation_id, "Rejected from XAI console detail view");
          toast.error("Recommendation rejected.");
        }}
      />
      <ModifyRecommendationDialog
        open={modifyOpen}
        onOpenChange={setModifyOpen}
        rec={rec}
        onSubmit={(patch) => modify(rec.recommendation_id, patch)}
      />
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border border-border bg-surface-2 px-2 py-1.5 text-center">
      <p className="font-mono text-sm font-semibold text-foreground">{value}</p>
      <p className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</p>
    </div>
  );
}
