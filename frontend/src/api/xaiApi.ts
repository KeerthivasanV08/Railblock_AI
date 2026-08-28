import { apiClient } from "./client";

export interface BlockExplanationResponse {
  block_id: string;
  priority_score: number;
  why_recommended: string[];
  risk_factors: string[];
  constraint_checks: {
    traffic: string;
    machine: string;
    crew: string;
    duration: string;
    spatial: string;
  };
  estimated_train_impact: string;
}

export const xaiApi = {
  explainBlock: async (blockId: string): Promise<BlockExplanationResponse> => {
    return apiClient<BlockExplanationResponse>(`/xai/explain/${blockId}`);
  },
};
