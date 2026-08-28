import { create } from "zustand";
import type { BlockPlan, BlockStatus, Department, TrainPath } from "@/types";
import { generateBlocks, PLAN_DATE } from "@/data/operations";
import { generateTrainPaths } from "@/data/trains";
import { AI_STAGES, generateAIPlan } from "@/services/mock/aiService";
import { blocksApi, plannerApi } from "@/api";
import { useTaskStore } from "./taskStore";
import { useResourceStore } from "./resourceStore";
import { useNotificationStore } from "./notificationStore";
import { useRecommendationStore } from "./recommendationStore";

export type PlannerViewMode = "Week" | "Month" | "26 Week";

interface PlannerState {
  blocks: BlockPlan[];
  trainPaths: TrainPath[];
  planDate: string;
  viewMode: PlannerViewMode;
  departmentFilter: Department[];
  statusFilter: BlockStatus[];
  selectedBlockId: string | null;
  aiRunning: boolean;
  aiStage: number;
  compareBaseline: BlockPlan[] | null;
  compareOpen: boolean;
  setViewMode: (m: PlannerViewMode) => void;
  setDepartmentFilter: (d: Department[]) => void;
  setStatusFilter: (s: BlockStatus[]) => void;
  select: (id: string | null) => void;
  moveBlock: (id: string, start_min: number) => void;
  resizeBlock: (id: string, duration_min: number) => void;
  lockBlock: (id: string) => void;
  unlockBlock: (id: string) => void;
  approveBlock: (id: string) => void;
  rejectBlock: (id: string, reason: string) => void;
  modifyBlock: (
    id: string,
    patch: { start_min: number; duration_min: number; reason: string },
  ) => void;
  applyExternalReschedule: (id: string, start_min: number, duration_min?: number) => void;
  startAIGeneration: () => void;
  resetPlan: () => void;
  setCompareOpen: (open: boolean) => void;
}

function clampStart(start: number, duration: number) {
  return Math.max(0, Math.min(24 * 60 - duration, start));
}

export const usePlannerStore = create<PlannerState>((set, get) => ({
  blocks: generateBlocks(),
  trainPaths: generateTrainPaths(),
  planDate: PLAN_DATE,
  viewMode: "Week",
  departmentFilter: [],
  statusFilter: [],
  selectedBlockId: "RB-402",
  aiRunning: false,
  aiStage: 0,
  compareBaseline: null,
  compareOpen: false,

  setViewMode: (viewMode) => set({ viewMode }),
  setDepartmentFilter: (departmentFilter) => set({ departmentFilter }),
  setStatusFilter: (statusFilter) => set({ statusFilter }),
  select: (selectedBlockId) => set({ selectedBlockId }),

  moveBlock: (id, start_min) =>
    set((s) => ({
      blocks: s.blocks.map((b) =>
        b.block_id === id && !b.locked
          ? { ...b, start_min: clampStart(start_min, b.duration_min) }
          : b,
      ),
    })),

  resizeBlock: (id, duration_min) =>
    set((s) => ({
      blocks: s.blocks.map((b) =>
        b.block_id === id && !b.locked
          ? {
              ...b,
              duration_min: Math.max(30, Math.min(600, duration_min)),
              start_min: clampStart(b.start_min, Math.max(30, Math.min(600, duration_min))),
            }
          : b,
      ),
    })),

  lockBlock: (id) => {
    set((s) => ({ blocks: s.blocks.map((b) => (b.block_id === id ? { ...b, locked: true } : b)) }));
    useNotificationStore.getState().logAudit("Locked Block", id);
  },
  unlockBlock: (id) => {
    set((s) => ({
      blocks: s.blocks.map((b) => (b.block_id === id ? { ...b, locked: false } : b)),
    }));
    useNotificationStore.getState().logAudit("Unlocked Block", id);
  },

  approveBlock: (id) => {
    set((s) => ({
      blocks: s.blocks.map((b) =>
        b.block_id === id ? { ...b, status: "APPROVED" as BlockStatus } : b,
      ),
    }));
    useNotificationStore.getState().logAudit("Approved Block", id);
    useNotificationStore.getState().push({
      type: "System Alert",
      title: `Block ${id} approved`,
      body: `Block ${id} moved to APPROVED status.`,
      href: "/planner",
      severity: "Info",
    });

    // Fire backend approval async
    blocksApi
      .approveBlock(id, { approved_by: "Section Controller", role: "Controller" })
      .catch(() => {
        // Fallback handled gracefully in store
      });
  },

  rejectBlock: (id, reason) => {
    set((s) => ({
      blocks: s.blocks.map((b) =>
        b.block_id === id ? { ...b, status: "REJECTED" as BlockStatus, reason } : b,
      ),
    }));
    useNotificationStore.getState().logAudit("Rejected Block", id, "Success", reason);

    // Fire backend rejection async
    blocksApi
      .rejectBlock(id, { rejected_by: "Section Controller", role: "Controller", reason })
      .catch(() => {
        // Fallback handled gracefully
      });
  },

  modifyBlock: (id, patch) => {
    set((s) => ({
      blocks: s.blocks.map((b) =>
        b.block_id === id
          ? {
              ...b,
              start_min: clampStart(patch.start_min, patch.duration_min),
              duration_min: patch.duration_min,
              reason: patch.reason,
              status: b.status === "APPROVED" ? ("PENDING APPROVAL" as BlockStatus) : b.status,
            }
          : b,
      ),
    }));
    useNotificationStore.getState().logAudit("Modified Block", id, "Success", patch.reason);

    // Fire backend modification async
    blocksApi
      .modifyBlock(id, {
        modified_by: "Section Controller",
        role: "Controller",
        reason: patch.reason,
        start_min: patch.start_min,
        duration_min: patch.duration_min,
      })
      .catch(() => {
        // Fallback handled gracefully
      });
  },

  applyExternalReschedule: (id, start_min, duration_min) =>
    set((s) => ({
      blocks: s.blocks.map((b) =>
        b.block_id === id
          ? {
              ...b,
              start_min: clampStart(start_min, duration_min ?? b.duration_min),
              duration_min: duration_min ?? b.duration_min,
              status: "SCHEDULED" as BlockStatus,
            }
          : b,
      ),
    })),

  startAIGeneration: () => {
    if (get().aiRunning) return;
    set({ aiRunning: true, aiStage: 0, compareBaseline: get().blocks });

    // Trigger backend optimization in parallel
    plannerApi.runOptimization().catch(() => {});

    const advance = (stage: number) => {
      if (stage >= AI_STAGES.length) {
        const tasks = useTaskStore.getState().tasks;
        const { machines, crews } = useResourceStore.getState();
        const { blocks: existingBlocks, trainPaths } = get();
        const result = generateAIPlan({ tasks, trainPaths, machines, crews, existingBlocks });
        set((s) => ({
          blocks: [
            ...s.blocks.filter((b) => !b.ai_generated || b.block_id === "RB-402"),
            ...result.blocks,
          ],
          aiRunning: false,
          selectedBlockId: result.blocks[0]?.block_id ?? s.selectedBlockId,
        }));
        useRecommendationStore.getState().addGenerated(result.recommendations);
        useNotificationStore
          .getState()
          .logAudit("Generated AI Plan", `${result.blocks.length} block(s)`);
        useNotificationStore.getState().push({
          type: "AI Recommendation",
          title: "AI plan generated",
          body: `${result.blocks.length} integrated block(s) recommended across the corridor.`,
          href: "/planner",
          severity: "Info",
        });
        return;
      }
      set({ aiStage: stage });
      setTimeout(() => advance(stage + 1), 550);
    };
    advance(0);
  },

  resetPlan: () => set({ blocks: generateBlocks(), compareBaseline: null, aiStage: 0 }),
  setCompareOpen: (compareOpen) => set({ compareOpen }),
}));
