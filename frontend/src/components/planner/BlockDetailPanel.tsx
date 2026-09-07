import { useEffect, useState } from "react";
import { AlertTriangle, Brain, Check, CheckCircle2, Lock, Pencil, PlayCircle, Unlock, X, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { AIBadge, DepartmentBadge } from "@/components/common/DomainBadges";
import { BlockStatusBadge, ImpactBadge } from "@/components/common/StatusBadge";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { EmptyState } from "@/components/common/States";
import { toHHMM } from "@/utils/dateUtils";
import { km, pct } from "@/utils/formatters";
import type { BlockPlan, Conflict, MaintenanceTask } from "@/types";
import { ModifyBlockDialog } from "./ModifyBlockDialog";
import { xaiApi } from "@/api";
import type { BlockExplanationResponse } from "@/api";

interface BlockDetailPanelProps {
  block: BlockPlan | undefined;
  tasks: MaintenanceTask[];
  conflicts: Conflict[];
  onApprove: (id: string) => void;
  onReject: (id: string, reason: string) => void;
  onModify: (
    id: string,
    patch: { start_min: number; duration_min: number; reason: string },
  ) => void;
  onLock: (id: string) => void;
  onUnlock: (id: string) => void;
  onSimulate: () => void;
}

export function BlockDetailPanel({
  block,
  tasks,
  conflicts,
  onApprove,
  onReject,
  onModify,
  onLock,
  onUnlock,
  onSimulate,
}: BlockDetailPanelProps) {
  const [rejectOpen, setRejectOpen] = useState(false);
  const [modifyOpen, setModifyOpen] = useState(false);
  const [xai, setXai] = useState<BlockExplanationResponse | null>(null);

  // Fetch XAI explanation when selected block changes
  useEffect(() => {
    if (!block) { setXai(null); return; }
    xaiApi.explainBlock(block.block_id)
      .then((res) => setXai(res))
      .catch(() => setXai(null)); // silent fallback
  }, [block?.block_id]);

  if (!block) {
    return (
      <EmptyState
        title="No block selected"
        description="Select a block on the timeline to inspect it."
      />
    );
  }

  const blockTasks = tasks.filter((t) => block.task_ids.includes(t.task_id));

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-start justify-between gap-2 border-b border-border px-3 py-3">
        <div>
          <div className="flex items-center gap-1.5">
            <p className="font-mono text-sm font-semibold text-foreground">{block.block_id}</p>
            {block.ai_generated && <AIBadge />}
            {block.locked && <Lock className="size-3.5 text-muted-foreground" aria-hidden />}
          </div>
          <p className="mt-0.5 text-[11px] text-muted-foreground">
            {block.section_id} · {km(block.from_km)}–{km(block.to_km)}
          </p>
        </div>
        <BlockStatusBadge status={block.status} />
      </div>

      <div className="flex-1 overflow-auto px-3 py-3">
        <div className="grid grid-cols-2 gap-2 text-xs">
          <Field
            label="Window"
            value={`${toHHMM(block.start_min)}–${toHHMM(block.start_min + block.duration_min)}`}
          />
          <Field label="Duration" value={`${block.duration_min} min`} />
          <Field label="Utilization" value={pct(block.utilization)} />
          <Field label="Train Impact" value={<ImpactBadge impact={block.train_impact} />} />
        </div>

        <div className="mt-3 flex flex-wrap gap-1">
          {block.departments.map((d) => (
            <DepartmentBadge key={d} department={d} />
          ))}
        </div>

        {conflicts.length > 0 && (
          <div className="mt-3 space-y-2 rounded border border-crit/30 bg-crit/5 p-2.5">
            <p className="flex items-center gap-1.5 text-xs font-semibold text-crit">
              <AlertTriangle className="size-3.5" aria-hidden /> CONFLICT DETECTED
            </p>
            {conflicts.map((c) => (
              <div key={c.id} className="text-[11px] text-foreground">
                <p>{c.message}</p>
                {c.suggestions.length > 0 && (
                  <p className="mt-0.5 text-muted-foreground">
                    Suggested alternatives: {c.suggestions.map((s) => s.label).join(", ")}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}

        <Separator className="my-3" />

        <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
          Tasks in this block ({blockTasks.length})
        </p>
        <div className="space-y-1.5">
          {blockTasks.length === 0 ? (
            <p className="text-xs text-muted-foreground">No maintenance tasks attached.</p>
          ) : (
            blockTasks.map((t) => (
              <div key={t.task_id} className="rounded border border-border px-2 py-1.5 text-[11px]">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono font-medium">{t.task_id}</span>
                  <DepartmentBadge department={t.department} />
                </div>
                <p className="mt-0.5 text-muted-foreground">
                  {t.defect} · {t.location_label}
                </p>
              </div>
            ))
          )}
        </div>

        {block.resource_ids.length > 0 && (
          <>
            <Separator className="my-3" />
            <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              Resources
            </p>
            <div className="flex flex-wrap gap-1 text-[11px] text-foreground">
              {block.resource_ids.map((r) => (
                <span key={r} className="rounded border border-border px-1.5 py-0.5 font-mono">
                  {r}
                </span>
              ))}
            </div>
          </>
        )}

        {block.reason && (
          <>
            <Separator className="my-3" />
            <p className="text-[11px] text-muted-foreground">
              <span className="font-semibold text-foreground">Note: </span>
              {block.reason}
            </p>
          </>
        )}

        {/* ── XAI Explanation (live from backend) ───────────────── */}
        {xai && (
          <>
            <Separator className="my-3" />
            <div className="space-y-2">
              <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                <Brain className="size-3.5 text-primary" aria-hidden /> AI Explanation
                <span className="ml-auto rounded bg-primary/10 px-1.5 py-0.5 text-[10px] text-primary">LIVE</span>
              </p>
              {xai.why_recommended.slice(0, 3).map((r, i) => (
                <p key={i} className="text-[11px] text-foreground">
                  <span className="mr-1.5 text-primary">›</span>{r}
                </p>
              ))}
              {xai.risk_factors.length > 0 && (
                <div className="mt-1.5 rounded border border-warn/30 bg-warn/5 px-2 py-1.5">
                  <p className="text-[10px] font-semibold text-warn">Risk Factors</p>
                  {xai.risk_factors.slice(0, 2).map((r, i) => (
                    <p key={i} className="text-[11px] text-muted-foreground">{r}</p>
                  ))}
                </div>
              )}
              <div className="grid grid-cols-3 gap-1 pt-1">
                {(Object.entries(xai.constraint_checks) as [string, string][]).map(([k, v]) => {
                  const ok = v.toUpperCase().includes("PASS") || v.toUpperCase().includes("OK");
                  return (
                    <div key={k} className="flex items-center gap-1 rounded border border-border px-1.5 py-1">
                      {ok
                        ? <CheckCircle2 className="size-3 shrink-0 text-ok" aria-hidden />
                        : <XCircle className="size-3 shrink-0 text-crit" aria-hidden />}
                      <span className="text-[10px] capitalize text-foreground">{k}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        )}
      </div>

      <div className="grid grid-cols-2 gap-1.5 border-t border-border p-2.5">
        <Button size="sm" variant="outline" className="gap-1.5" onClick={onSimulate}>
          <PlayCircle className="size-3.5" aria-hidden /> Simulate
        </Button>
        <Button size="sm" variant="outline" className="gap-1.5" onClick={() => setModifyOpen(true)}>
          <Pencil className="size-3.5" aria-hidden /> Modify
        </Button>
        <Button
          size="sm"
          variant="outline"
          className="gap-1.5"
          onClick={() => (block.locked ? onUnlock(block.block_id) : onLock(block.block_id))}
        >
          {block.locked ? (
            <Unlock className="size-3.5" aria-hidden />
          ) : (
            <Lock className="size-3.5" aria-hidden />
          )}
          {block.locked ? "Unlock" : "Lock"}
        </Button>
        <Button
          size="sm"
          variant="outline"
          className="gap-1.5 border-crit/40 text-crit hover:bg-crit/10"
          onClick={() => setRejectOpen(true)}
        >
          <X className="size-3.5" aria-hidden /> Reject
        </Button>
        <Button
          size="sm"
          className="col-span-2 gap-1.5 bg-ok text-ok-foreground hover:bg-ok/90"
          onClick={() => onApprove(block.block_id)}
          disabled={block.status === "APPROVED" || block.status === "COMPLETED"}
        >
          <Check className="size-3.5" aria-hidden /> Approve Block
        </Button>
      </div>

      <ConfirmDialog
        open={rejectOpen}
        onOpenChange={setRejectOpen}
        title={`Reject block ${block.block_id}?`}
        description="This will mark the block as rejected and log the action to the audit trail."
        confirmLabel="Reject block"
        destructive
        onConfirm={() => onReject(block.block_id, "Rejected by controller during review")}
      />

      <ModifyBlockDialog
        open={modifyOpen}
        onOpenChange={setModifyOpen}
        block={block}
        onSubmit={(patch) => onModify(block.block_id, patch)}
      />
    </div>
  );
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded border border-border bg-surface-2 px-2 py-1.5">
      <p className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-0.5 font-mono text-xs font-medium text-foreground">{value}</p>
    </div>
  );
}
