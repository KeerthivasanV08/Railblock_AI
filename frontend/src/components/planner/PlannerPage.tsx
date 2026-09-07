import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { GitCompare, Loader2, RotateCcw, Sparkles } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { usePlannerStore, type PlannerViewMode } from "@/stores/plannerStore";
import { useTaskStore } from "@/stores/taskStore";
import { useResourceStore } from "@/stores/resourceStore";
import { detectAllConflicts } from "@/utils/conflictDetection";
import { clockNow } from "@/utils/dateUtils";
import { PlannerTimeline } from "./PlannerTimeline";
import { BlockDetailPanel } from "./BlockDetailPanel";
import { AIGenerationOverlay } from "./AIGenerationOverlay";
import { ComparePlansDialog } from "./ComparePlansDialog";
import { CORRIDOR } from "@/data/corridor";

export function PlannerPage() {
  const {
    blocks,
    trainPaths,
    selectedBlockId,
    aiRunning,
    aiStage,
    aiError,
    compareBaseline,
    select,
    moveBlock,
    resizeBlock,
    approveBlock,
    rejectBlock,
    modifyBlock,
    lockBlock,
    unlockBlock,
    startAIGeneration,
    resetPlan,
    viewMode,
    setViewMode,
    loadBlocksFromBackend,
  } = usePlannerStore();
  const tasks = useTaskStore((s) => s.tasks);
  const { machines, crews } = useResourceStore();
  const [compareOpen, setCompareOpen] = useState(false);

  // Load operational blocks from backend on first mount
  useEffect(() => {
    if (blocks.length === 0) loadBlocksFromBackend();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Surface backend AI generation errors as destructive toasts
  useEffect(() => {
    if (aiError) {
      toast.error("AI plan generation failed", { description: aiError });
    }
  }, [aiError]);

  const conflictsByBlock = useMemo(() => {
    const all = detectAllConflicts({ blocks, trainPaths, machines, crews });
    const map: Record<string, ReturnType<typeof detectAllConflicts>> = {};
    for (const c of all) (map[c.block_id] ??= []).push(c);
    return map;
  }, [blocks, trainPaths, machines, crews]);

  const selectedBlock = blocks.find((b) => b.block_id === selectedBlockId);
  const nowMin = (() => {
    const parts = clockNow().split(":").map(Number);
    const h = parts[0] ?? 0;
    const m = parts[1] ?? 0;
    return h * 60 + m;
  })();

  const handleSimulate = () => {
    const conflicts = selectedBlockId ? (conflictsByBlock[selectedBlockId] ?? []) : [];
    if (conflicts.length > 0) {
      toast.warning(`Conflict detected with ${conflicts[0]?.entity ?? "unknown entity"}.`, {
        description: conflicts[0]?.suggestions?.[0]
          ? `Try ${conflicts[0].suggestions[0]?.label}`
          : undefined,
      });
    } else {
      toast.success("AI rescheduling simulation completed.", {
        description: "No conflicts found for the current window.",
      });
    }
  };

  return (
    <div className="relative flex h-full flex-col">
      <PageHeader
        title="AI Block Planner"
        description={`Integrated maintenance block planning — ${CORRIDOR.displayName}`}
        crumbs={[{ label: "Planning" }, { label: "AI Block Planner" }]}
        actions={
          <>
            <Select defaultValue={CORRIDOR.routeId}>
              <SelectTrigger className="h-8 w-[190px] text-xs">
                <SelectValue placeholder="Corridor" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={CORRIDOR.routeId}>{CORRIDOR.displayName}</SelectItem>
              </SelectContent>
            </Select>
            <Select defaultValue={CORRIDOR.divisions[0]}>
              <SelectTrigger className="h-8 w-[180px] text-xs">
                <SelectValue placeholder="Division" />
              </SelectTrigger>
              <SelectContent>
                {CORRIDOR.divisions.map((div) => (
                  <SelectItem key={div} value={div}>{div}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as PlannerViewMode)}>
              <TabsList className="h-8">
                <TabsTrigger value="Week" className="text-xs">
                  Week
                </TabsTrigger>
                <TabsTrigger value="Month" className="text-xs">
                  Month
                </TabsTrigger>
                <TabsTrigger value="26 Week" className="text-xs">
                  26 Week
                </TabsTrigger>
              </TabsList>
            </Tabs>
            <Button variant="outline" size="sm" className="gap-1.5" onClick={resetPlan}>
              <RotateCcw className="size-3.5" aria-hidden /> Reset
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5"
              disabled={!compareBaseline}
              onClick={() => setCompareOpen(true)}
            >
              <GitCompare className="size-3.5" aria-hidden /> Compare Plans
            </Button>
            <Button
              size="sm"
              className="gap-1.5 bg-ai text-ai-foreground hover:bg-ai/90"
              onClick={startAIGeneration}
              disabled={aiRunning}
            >
              {aiRunning ? (
                <Loader2 className="size-3.5 animate-spin" aria-hidden />
              ) : (
                <Sparkles className="size-3.5" aria-hidden />
              )}
              {aiRunning ? "Optimizing…" : "Generate AI Plan"}
            </Button>
          </>
        }
      />

      <div className="relative flex flex-1 gap-3 overflow-hidden p-3">
        <div className="min-w-0 flex-1 overflow-auto">
          <PlannerTimeline
            blocks={blocks}
            trainPaths={trainPaths}
            conflictsByBlock={conflictsByBlock}
            selectedBlockId={selectedBlockId}
            onSelect={select}
            onMove={moveBlock}
            onResize={resizeBlock}
            nowMin={viewMode === "Week" ? nowMin : undefined}
          />
          <p className="mt-2 px-1 text-[11px] text-muted-foreground">
            Drag a block to move it, drag the right edge to resize. Locked blocks cannot be edited.
            Thin grey bars show reference train paths for the selected date.
          </p>
        </div>
        <aside className="hidden w-[320px] shrink-0 overflow-hidden rounded-md border border-border bg-surface xl:block">
          <BlockDetailPanel
            block={selectedBlock}
            tasks={tasks}
            conflicts={selectedBlockId ? (conflictsByBlock[selectedBlockId] ?? []) : []}
            onApprove={approveBlock}
            onReject={rejectBlock}
            onModify={modifyBlock}
            onLock={lockBlock}
            onUnlock={unlockBlock}
            onSimulate={handleSimulate}
          />
        </aside>
        {aiRunning && <AIGenerationOverlay stage={aiStage} />}
      </div>

      <ComparePlansDialog
        open={compareOpen}
        onOpenChange={setCompareOpen}
        baseline={compareBaseline ?? []}
        current={blocks}
      />
    </div>
  );
}
