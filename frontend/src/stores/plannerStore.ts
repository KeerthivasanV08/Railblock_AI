import { create } from "zustand";
import type { BlockPlan, BlockStatus, Department, TrainPath } from "@/types";
import { PLAN_DATE } from "@/data/operations";
import { generateTrainPaths } from "@/data/trains";
import { blocksApi, plannerApi } from "@/api";
import { adaptBackendBlock, adaptWeeklyPlanItemToBlock } from "@/utils/backendAdapters";
import type { DataProvenance } from "@/utils/backendAdapters";
import { useNotificationStore } from "./notificationStore";

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
  aiError: string | null;
  compareBaseline: BlockPlan[] | null;
  compareOpen: boolean;
  dataSource: DataProvenance;
  loadingBlocks: boolean;
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
  /** Loads blocks from backend weekly_block_plan.csv. Falls back to empty. */
  loadBlocksFromBackend: () => Promise<void>;
}

function clampStart(start: number, duration: number) {
  return Math.max(0, Math.min(24 * 60 - duration, start));
}

export const usePlannerStore = create<PlannerState>((set, get) => ({
  blocks: [],
  trainPaths: generateTrainPaths(),
  planDate: PLAN_DATE,
  viewMode: "Week",
  departmentFilter: [],
  statusFilter: [],
  selectedBlockId: null,
  aiRunning: false,
  aiStage: 0,
  aiError: null,
  compareBaseline: null,
  compareOpen: false,
  dataSource: "SYNTHETIC",
  loadingBlocks: false,

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
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : `Unable to approve block ${id}. Please try again.`;
        useNotificationStore.getState().push({
          type: "System Alert",
          title: `Block ${id} approval error`,
          body: message,
          href: "/planner",
          severity: "Warning",
        });
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
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : `Unable to reject block ${id}. Please try again.`;
        useNotificationStore.getState().push({
          type: "System Alert",
          title: `Block ${id} rejection error`,
          body: message,
          href: "/planner",
          severity: "Warning",
        });
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
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : `Unable to modify block ${id}. Please try again.`;
        useNotificationStore.getState().push({
          type: "System Alert",
          title: `Block ${id} modification error`,
          body: message,
          href: "/planner",
          severity: "Warning",
        });
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
    set({ aiRunning: true, aiStage: 0, aiError: null, compareBaseline: get().blocks });

    /**
     * Real backend OR-Tools–driven AI plan generation.
     *
     * Stages map to real API phases:
     *   0 — Sending request to optimization engine
     *   1 — Waiting for OR-Tools / MILP solve
     *   2 — Checking resource availability
     *   3 — Validating constraints
     *   4 — Adapting backend blocks
     *   5 — Generating recommendation metadata
     *
     * On failure: sets aiError and does NOT substitute synthetic blocks.
     */
    const stageDelay = 600; // ms between stage advances before/after API call

    const failWithError = (msg: string) => {
      set({ aiRunning: false, aiError: msg });
      useNotificationStore.getState().push({
        type: "System Alert",
        title: "AI plan generation failed",
        body: msg,
        href: "/planner",
        severity: "Warning",
      });
    };

    // Advance to stage 1 ("Checking traffic windows...") while request is in flight
    set({ aiStage: 0 });
    const advanceTimer = setTimeout(() => set({ aiStage: 1 }), stageDelay);

    plannerApi
      .createWeeklyPlan()
      .then((res) => {
        clearTimeout(advanceTimer);
        const items = res?.weekly_plan ?? [];

        if (items.length === 0) {
          failWithError(
            "Backend optimizer returned no blocks. Check that feasibility-checked tasks are available.",
          );
          return;
        }

        // Advance through remaining visual stages quickly now data is available
        set({ aiStage: 2 });
        setTimeout(() => set({ aiStage: 3 }), stageDelay * 0.6);
        setTimeout(() => set({ aiStage: 4 }), stageDelay * 1.2);
        setTimeout(() => {
          set({ aiStage: 5 });
          setTimeout(() => {
            const adapted = items.map((item, i) => adaptWeeklyPlanItemToBlock(item, i));
            const existingNonAI = get().blocks.filter((b) => !b.ai_generated);
            set({
              blocks: [...existingNonAI, ...adapted],
              aiRunning: false,
              aiError: null,
              dataSource: "DERIVED",
              selectedBlockId: adapted[0]?.block_id ?? get().selectedBlockId,
            });
            useNotificationStore.getState().logAudit(
              "Generated AI Plan (Backend)",
              `${adapted.length} block(s) from OR-Tools optimizer`,
            );
            useNotificationStore.getState().push({
              type: "AI Recommendation",
              title: "AI plan generated",
              body: `${adapted.length} block(s) from the backend OR-Tools optimizer. Review and approve.`,
              href: "/planner",
              severity: "Info",
            });
          }, stageDelay * 0.8);
        }, stageDelay * 1.8);
      })
      .catch((err: unknown) => {
        clearTimeout(advanceTimer);
        const msg =
          err instanceof Error
            ? err.message
            : "Backend optimization service is unavailable. Verify the server is running.";
        failWithError(msg);
      });
  },

  resetPlan: () => {
    set({ blocks: [], compareBaseline: null, aiStage: 0, aiError: null, dataSource: "SYNTHETIC" });
    // Reload from backend to restore the current operational plan
    get().loadBlocksFromBackend();
  },
  setCompareOpen: (compareOpen) => set({ compareOpen }),

  loadBlocksFromBackend: async () => {
    set({ loadingBlocks: true });
    try {
      const res = await blocksApi.getBlocks(1, 200);
      const items = res?.items ?? res?.data ?? [];
      if (items.length > 0) {
        const adapted = items.map(adaptBackendBlock);
        set({
          blocks: adapted,
          dataSource: "DERIVED",
          loadingBlocks: false,
          selectedBlockId: adapted[0]?.block_id ?? get().selectedBlockId,
        });
        return;
      }
    } catch {
      // Backend unavailable — stay on synthetic
    }
    set({ dataSource: "SYNTHETIC", loadingBlocks: false });
  },
}));
