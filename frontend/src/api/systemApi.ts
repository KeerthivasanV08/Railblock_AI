import { apiClient } from "./client";

export interface SystemHealthData {
  status: string;
  timestamp: string;
  data_sources?: Record<string, { status: string; row_count: number }>;
  ai_engines?: Record<string, { available: boolean; model_type?: string; version?: string }>;
}

export const systemApi = {
  getHealth: async (): Promise<SystemHealthData> => {
    return apiClient<SystemHealthData>("/system/health");
  },

  getDataStatus: async () => {
    return apiClient("/system/data-status");
  },

  validateData: async () => {
    return apiClient("/system/validate-data", {
      method: "POST",
    });
  },

  preprocessData: async () => {
    return apiClient("/system/preprocess", {
      method: "POST",
    });
  },

  getAuthStatus: async () => {
    return apiClient<{ status: string; message: string }>("/auth/status");
  },
};
