import { create } from "zustand";
import type { AIRecommendation } from "@/types";
import { generateRecommendations } from "@/data/operations";
import { useNotificationStore } from "./notificationStore";
import { usePlannerStore } from "./plannerStore";

interface RecommendationState {
  recommendations: AIRecommendation[];
  selectedId: string | null;
  select: (id: string | null) => void;
  approve: (id: string) => void;
  reject: (id: string, reason: string) => void;
  modify: (id: string, patch: { start_min: number; duration_min: number; reason: string }) => void;
  addGenerated: (recs: AIRecommendation[]) => void;
}

export const useRecommendationStore = create<RecommendationState>((set, get) => ({
  recommendations: generateRecommendations(),
  selectedId: null,
  select: (selectedId) => set({ selectedId }),

  approve: (id) => {
    set((s) => ({
      recommendations: s.recommendations.map((r) =>
        r.recommendation_id === id ? { ...r, status: "Approved" } : r,
      ),
    }));
    const rec = get().recommendations.find((r) => r.recommendation_id === id);
    if (rec) usePlannerStore.getState().approveBlock(rec.block_id);
    useNotificationStore.getState().logAudit("Approved Recommendation", id);
    useNotificationStore.getState().push({
      type: "AI Recommendation",
      title: `Recommendation ${id} approved`,
      body: rec
        ? `Block ${rec.block_id} has been approved for scheduling.`
        : "Recommendation approved.",
      href: `/recommendations/${id}`,
      severity: "Info",
    });
  },

  reject: (id, reason) => {
    set((s) => ({
      recommendations: s.recommendations.map((r) =>
        r.recommendation_id === id ? { ...r, status: "Rejected" } : r,
      ),
    }));
    const rec = get().recommendations.find((r) => r.recommendation_id === id);
    if (rec) usePlannerStore.getState().rejectBlock(rec.block_id, reason);
    useNotificationStore.getState().logAudit("Rejected Recommendation", id, "Success", reason);
    useNotificationStore.getState().push({
      type: "AI Recommendation",
      title: `Recommendation ${id} rejected`,
      body: reason,
      href: `/recommendations/${id}`,
      severity: "Warning",
    });
  },

  modify: (id, patch) => {
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
    if (rec) usePlannerStore.getState().modifyBlock(rec.block_id, patch);
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
