import { apiClient } from "./client";

export const scoringApi = {
  calculatePriority: async (task?: Record<string, unknown>) => {
    return apiClient("/scoring/priority", {
      method: "POST",
      ...(task ? { body: JSON.stringify(task) } : {}),
    });
  },

  trainModel: async () => {
    return apiClient("/scoring/train", {
      method: "POST",
    });
  },
};
