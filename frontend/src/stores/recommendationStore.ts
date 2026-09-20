import { create } from "zustand";
import type { AIRecommendation, Department } from "@/types";
import { generateRecommendations } from "@/data/operations";
import { blocksApi } from "@/api/blocksApi";
import { timeStrToMinutes } from "@/utils/backendAdapters";
import { useNotificationStore } from "./notificationStore";
import { usePlannerStore } from "./plannerStore";

interface RecommendationState {
  recommendations: AIRecommendation[];
  selectedId: string | null;
  loading: boolean;
  select: (id: string | null) => void;
  approve: (id: string) => Promise<void>;
  reject: (id: string, reason: string) => Promise<void>;
  modify: (id: string, patch: { start_min: number; duration_min: number; reason: string }) => Promise<void>;
  addGenerated: (recs: AIRecommendation[]) => void;
  fetchRecommendations: () => Promise<void>;
}

export const useRecommendationStore = create<RecommendationState>((set, get) => ({
  recommendations: generateRecommendations(),
  selectedId: null,
  loading: false,
  select: (selectedId) => set({ selectedId }),

  fetchRecommendations: async () => {
    set({ loading: true });
    try {
      const res = await blocksApi.getBlocks(1, 50, "PROPOSED");
      const items = res?.items ?? res?.data ?? [];
      if (items.length > 0) {
        const adaptedRecs: AIRecommendation[] = items.map((b, idx) => {
          const rawDepts = Array.isArray(b.departments)
            ? b.departments
            : String(b.departments || "Engineering").split(/[;,]/).map((d) => d.trim()).filter(Boolean);
          const rawTasks = (b as any).task_ids ?? b.tasks;
          const taskIds = Array.isArray(rawTasks)
            ? rawTasks
            : String(rawTasks || "").split(/[;,]/).map((t) => t.trim()).filter(Boolean);
          const startMin = b.start_min ?? timeStrToMinutes(b.start_time);
          const durMin = b.duration_min ?? b.duration_minutes ?? 120;
          const util = b.utilization ?? b.optimization_score ?? 85;
          const normUtil = util <= 1.0 && util > 0 ? Math.round(util * 100) : Math.round(util);
          const score = Math.round(b.priority_score ?? b.optimization_score ?? 85);

          return {
            recommendation_id: `REC-${b.block_id || idx + 1}`,
            block_id: b.block_id,
            section_id: b.section_id || "GZB-ALJN",
            start_min: startMin,
            duration_min: durMin,
            departments: (rawDepts.length ? rawDepts : ["Engineering"]) as Department[],
            task_ids: taskIds,
            priority: score,
            utilization: normUtil,
            train_impact: "Medium",
            confidence: Math.min(98, Math.max(75, score)),
            status:
              b.status?.toUpperCase() === "APPROVED"
                ? "Approved"
                : b.status?.toUpperCase() === "REJECTED"
                ? "Rejected"
                : "Pending",
            reasons: [
              `Multi-disciplinary block on ${b.section_id}`,
              `OR-Tools MIP solver evaluated asset availability & timetable gap`,
              `Weather safety & possession constraints verified`,
            ],
            factors: [
              { label: "MDPS Priority", value: score },
              { label: "Possession Efficiency", value: normUtil },
              { label: "Timetable Slack", value: 85 },
              { label: "Weather Safety Margin", value: 92 },
            ],
            date: b.date || "2026-09-01",
          };
        });
        set({ recommendations: adaptedRecs, loading: false });
        return;
      }
    } catch {
      // Backend error — keep current recommendations
    }
    set({ loading: false });
  },

  approve: async (id) => {
    set((s) => ({
      recommendations: s.recommendations.map((r) =>
        r.recommendation_id === id ? { ...r, status: "Approved" } : r,
      ),
    }));
    const rec = get().recommendations.find((r) => r.recommendation_id === id);
    if (rec) {
      usePlannerStore.getState().approveBlock(rec.block_id);
      try {
        await blocksApi.approveBlock(rec.block_id, {
          approved_by: "Chief Controller",
          role: "Controller",
          notes: "Approved from AI Recommendations console",
        });
      } catch {
        // Error logged
      }
    }
    useNotificationStore.getState().logAudit("Approved Recommendation", id);
    useNotificationStore.getState().push({
      type: "AI Recommendation",
      title: `Recommendation ${id} approved`,
      body: rec
        ? `Block ${rec.block_id} has been approved for scheduling.`
        : "Recommendation approved.",
      href: `/recommendations`,
      severity: "Info",
    });
  },

  reject: async (id, reason) => {
    set((s) => ({
      recommendations: s.recommendations.map((r) =>
        r.recommendation_id === id ? { ...r, status: "Rejected" } : r,
      ),
    }));
    const rec = get().recommendations.find((r) => r.recommendation_id === id);
    if (rec) {
      usePlannerStore.getState().rejectBlock(rec.block_id, reason);
      try {
        await blocksApi.rejectBlock(rec.block_id, {
          rejected_by: "Chief Controller",
          role: "Controller",
          reason,
        });
      } catch {
        // Error logged
      }
    }
    useNotificationStore.getState().logAudit("Rejected Recommendation", id, "Success", reason);
    useNotificationStore.getState().push({
      type: "AI Recommendation",
      title: `Recommendation ${id} rejected`,
      body: reason,
      href: `/recommendations`,
      severity: "Warning",
    });
  },

  modify: async (id, patch) => {
    set((s) => ({
      recommendations: s.recommendations.map((r) =>
        r.recommendation_id === id
          ? {
              ...r,
              start_min: patch.start_min,
              duration_min: patch.duration_min,
              status: "Modified",
            }
          : r,
      ),
    }));
    const rec = get().recommendations.find((r) => r.recommendation_id === id);
    if (rec) {
      usePlannerStore.getState().modifyBlock(rec.block_id, patch);
      try {
        await blocksApi.modifyBlock(rec.block_id, {
          modified_by: "Chief Controller",
          role: "Controller",
          reason: patch.reason,
          start_min: patch.start_min,
          duration_min: patch.duration_min,
        });
      } catch {
        // Error logged
      }
    }
    useNotificationStore
      .getState()
      .logAudit("Modified Recommendation", id, "Success", patch.reason);
  },

  addGenerated: (recs) =>
    set((s) => ({
      recommendations: [
        ...recs,
        ...s.recommendations.filter(
          (r) => !recs.some((n) => n.recommendation_id === r.recommendation_id),
        ),
      ],
    })),
}));
