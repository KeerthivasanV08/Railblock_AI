import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { BlockPlan } from "@/types";

interface ComparePlansDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  baseline: BlockPlan[];
  current: BlockPlan[];
}

function metrics(blocks: BlockPlan[]) {
  const utilization = blocks.length
    ? Math.round(blocks.reduce((s, b) => s + b.utilization, 0) / blocks.length)
    : 0;
  const integrated = blocks.filter((b) => b.lane === "Integrated").length;
  const conflicts = blocks.filter((b) => b.train_conflicts.length > 0).length;
  const trainsAffected = new Set(blocks.flatMap((b) => b.train_conflicts)).size;
  const tasksCovered = new Set(blocks.flatMap((b) => b.task_ids)).size;
  return { count: blocks.length, utilization, integrated, conflicts, trainsAffected, tasksCovered };
}

export function ComparePlansDialog({
  open,
  onOpenChange,
  baseline,
  current,
}: ComparePlansDialogProps) {
  const before = metrics(baseline);
  const after = metrics(current);
  const timeSaved = Math.max(0, (after.integrated - before.integrated) * 65);

  const rows: { label: string; before: string | number; after: string | number }[] = [
    { label: "Number of blocks", before: before.count, after: after.count },
    {
      label: "Average utilization",
      before: `${before.utilization}%`,
      after: `${after.utilization}%`,
    },
    { label: "Integrated blocks", before: before.integrated, after: after.integrated },
    { label: "Blocks with train conflicts", before: before.conflicts, after: after.conflicts },
    { label: "Trains impacted", before: before.trainsAffected, after: after.trainsAffected },
    { label: "Tasks covered", before: before.tasksCovered, after: after.tasksCovered },
    { label: "Estimated time saved", before: "—", after: `${timeSaved} min` },
  ];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Current Plan vs AI Plan</DialogTitle>
          <DialogDescription>Comparing current plan snapshot against the new AI-optimized plan from the backend OR-Tools solver.</DialogDescription>
        </DialogHeader>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-[11px] uppercase tracking-wide text-muted-foreground">
              <th className="py-1.5 font-medium">Metric</th>
              <th className="py-1.5 text-right font-medium">Current Plan</th>
              <th className="py-1.5 text-right font-medium text-ai">AI Plan</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.label} className="border-b border-border/60 last:border-0">
                <td className="py-1.5 text-foreground">{r.label}</td>
                <td className="py-1.5 text-right font-mono tabular-nums text-muted-foreground">
                  {r.before}
                </td>
                <td className="py-1.5 text-right font-mono tabular-nums font-semibold text-foreground">
                  {r.after}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </DialogContent>
    </Dialog>
  );
}
