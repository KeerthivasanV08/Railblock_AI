import { apiClient } from "./client";

export interface LiveTrainPosition {
  train_id: string;
  name?: string;
  train_number?: string;
  category?: string;
  direction?: string;
  section_id: string;
  current_km: number;
  speed_kmph: number;
  delay_minutes: number;
  origin?: string;
  destination?: string;
}

export const liveApi = {
  getTrainPositions: async (): Promise<{
    provider_status: Record<string, unknown>;
    source: string;
    items: LiveTrainPosition[];
  }> => {
    return apiClient("/live/trains");
  },

  getProviderStatus: async () => {
    return apiClient("/live/status");
  },

  syncMovements: async () => {
    return apiClient("/live/sync", {
      method: "POST",
    });
  },
};
