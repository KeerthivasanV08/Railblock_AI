import { apiClient } from "./client";

export const scoringApi = {
  calculatePriority: async (task?: Record<string, unknown>) => {
    return apiClient("/scoring/priority", {
      method: "POST",
      body: task ? JSON.stringify(task) : undefined,
    });
  },

  trainModel: async () => {
    return apiClient("/scoring/train", {
      method: "POST",
    });
  },
};
