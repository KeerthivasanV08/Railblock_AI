/**
 * Execution Monitoring & Closed-Loop Feedback API Client.
 *
 * Covers:
 *   GET  /execution/active              — Active block executions in the field
 *   GET  /execution/metrics             — Closed-loop feedback metrics
 *   GET  /execution/section-modifier/:id — Learned section buffer modifier
 *   POST /blocks/:id/execute            — Record block execution outcome
 */

import { apiClient } from "./client";

export interface ActiveExecution {
  block_id: string;
  section_id: string;
  department?: string;
  started_at?: string;
  planned_duration_min?: number;
  elapsed_min?: number;
  status?: string;
}

export interface ExecutionMetrics {
  total_executions: number;
  avg_duration_variance_min: number;
  overrun_rate_pct: number;
  block_wastage_pct: number;
  avg_buffer_applied_min: number;
  sections_with_learned_buffers?: number;
  [key: string]: unknown;
}

export interface ExecutionMetricsResponse {
  status: string;
  metrics: ExecutionMetrics;
}

export interface SectionBufferModifier {
  section_id: string;
  recommended_buffer_minutes: number;
}

export interface BlockExecutionOutcomePayload {
  actual_start_time?: string;
  actual_end_time?: string;
  actual_duration_minutes?: number;
  completion_status: "COMPLETED" | "PARTIAL" | "ABANDONED";
  work_done_pct?: number;
  notes?: string;
  recorded_by?: string;
  role?: string;
}

export const executionApi = {
  getActiveExecutions: async (): Promise<{ active_executions: ActiveExecution[] }> => {
    return apiClient<{ active_executions: ActiveExecution[] }>("/execution/active");
  },

  getExecutionMetrics: async (): Promise<ExecutionMetricsResponse> => {
    return apiClient<ExecutionMetricsResponse>("/execution/metrics");
  },

  getSectionBufferModifier: async (sectionId: string): Promise<SectionBufferModifier> => {
    return apiClient<SectionBufferModifier>(
      `/execution/section-modifier/${encodeURIComponent(sectionId)}`,
    );
  },

  recordOutcome: async (
    blockId: string,
    payload: BlockExecutionOutcomePayload,
  ): Promise<{ status: string; block_id: string }> => {
    return apiClient<{ status: string; block_id: string }>(`/blocks/${blockId}/execute`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};
