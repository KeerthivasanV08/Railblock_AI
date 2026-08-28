import { apiClient } from "./client";
import type { PaginatedResponse } from "./tasksApi";

export interface BackendBlockItem {
  block_id: string;
  section_id: string;
  from_km?: number;
  to_km?: number;
  date?: string;
  start_time?: string;
  end_time?: string;
  duration_minutes?: number;
  status: string;
  optimization_score?: number;
  priority_score?: number;
  utilization?: number;
  departments?: string | string[];
  tasks?: string | string[];
  reason?: string;
}

export interface FeasibleCandidateItem {
  block_id: string;
  primary_task: string;
  shadow_tasks: string[];
  departments: string[];
  corridor: string;
  start_time: string | null;
  end_time: string | null;
  duration: number;
  utilization: number;
  priority: number;
  required_resources: string[];
  train_impact: string;
  feasibility: {
    feasible: boolean;
    failed_constraints: string;
    satisfied_constraints: string;
    explanation: string;
  };
  constraint_summary: {
    traffic: boolean;
    machine: boolean;
    crew: boolean;
    duration: boolean;
    spatial: boolean;
  };
  xai_reasons: string[];
}

export interface CandidateGenerationResponse {
  candidate_count: number;
  candidates: FeasibleCandidateItem[];
}

export interface BlockApprovalPayload {
  approved_by: string;
  role?: string;
  notes?: string;
}

export interface BlockModificationPayload {
  modified_by: string;
  role?: string;
  start_time?: string;
  end_time?: string;
  duration_minutes?: number;
  start_min?: number;
  duration_min?: number;
  reason: string;
}

export interface BlockRejectionPayload {
  rejected_by: string;
  role?: string;
  reason: string;
}

export const blocksApi = {
  getBlocks: async (
    page = 1,
    pageSize = 50,
    status?: string,
  ): Promise<PaginatedResponse<BackendBlockItem>> => {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (status) params.set("status", status);
    return apiClient<PaginatedResponse<BackendBlockItem>>(`/blocks?${params.toString()}`);
  },

  getBlockById: async (blockId: string): Promise<BackendBlockItem> => {
    return apiClient<BackendBlockItem>(`/blocks/${blockId}`);
  },

  generateCandidates: async (): Promise<CandidateGenerationResponse> => {
    return apiClient<CandidateGenerationResponse>("/blocks/candidates", {
      method: "POST",
    });
  },

  generateBlockPlan: async (startDate?: string) => {
    const params = startDate ? `?start_date=${startDate}` : "";
    return apiClient(`/blocks/generate${params}`, {
      method: "POST",
    });
  },

  checkFeasibility: async (): Promise<{ status: string; feasible_tasks: number }> => {
    return apiClient<{ status: string; feasible_tasks: number }>("/blocks/check-feasibility", {
      method: "POST",
    });
  },

  runClustering: async (): Promise<{ status: string; clusters_generated: number }> => {
    return apiClient<{ status: string; clusters_generated: number }>("/blocks/cluster", {
      method: "POST",
    });
  },

  approveBlock: async (blockId: string, payload: BlockApprovalPayload) => {
    return apiClient(`/blocks/${blockId}/approve`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  modifyBlock: async (blockId: string, payload: BlockModificationPayload) => {
    return apiClient(`/blocks/${blockId}/modify`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  rejectBlock: async (blockId: string, payload: BlockRejectionPayload) => {
    return apiClient(`/blocks/${blockId}/reject`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};
