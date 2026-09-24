/**
 * Execution Monitoring & Closed-Loop Feedback API Client.
 */

import { apiClient } from "./client";

export interface ExecutionRecord {
  execution_id: string;
  block_id: string;
  section_id: string;
  department: string;
  planned_start: string;
  planned_end: string;
  actual_start?: string | null;
  actual_end?: string | null;
  planned_duration: number;
  actual_duration?: number | null;
  variance_minutes?: number | null;
  completed_tasks: number;
  total_tasks: number;
  completion_percentage: number;
  machine_id?: string | null;
  crew_id?: string | null;
  status: "SCHEDULED" | "ACTIVE" | "COMPLETED" | "PARTIAL" | "ABANDONED";
  deviation_reason?: string | null;
  notes?: string | null;
  created_at: string;
  recorded_by?: string;
}

export interface ActiveExecution {
  block_id: string;
  execution_id?: string;
  section_id: string;
  department?: string;
  started_at?: string;
  actual_start?: string;
  actual_end?: string;
  planned_start?: string;
  planned_end?: string;
  planned_duration_min?: number;
  planned_duration?: number;
  elapsed_min?: number;
  status?: string;
  machine_id?: string;
  crew_id?: string;
  completed_tasks?: number;
  total_tasks?: number;
  deviation_reason?: string;
  notes?: string;
}

export interface ExecutionKPIs {
  total_executions: number;
  avg_variance: number;
  overrun_rate: number;
  block_wastage: number | null;
  block_wastage_formatted?: string;
  note?: string;
}

export interface DurationSeriesPoint {
  block_id: string;
  section_id: string;
  planned_duration: number;
  actual_duration: number;
  variance: number;
}

export interface StatusDistribution {
  status: string;
  count: number;
  percentage: number;
}

export interface VarianceTrendPoint {
  date: string;
  avg_variance: number;
  overrun_count: number;
}

export interface DeviationReasonCount {
  reason: string;
  count: number;
  percentage: number;
}

export interface ExecutionAnalyticsData {
  planned_vs_actual: DurationSeriesPoint[];
  status_distribution: StatusDistribution[];
  variance_trend: VarianceTrendPoint[];
  top_deviation_reasons: DeviationReasonCount[];
}

export interface RecordOutcomePayload {
  block_id: string;
  section_id?: string | undefined;
  department?: string | undefined;
  planned_start?: string | undefined;
  planned_end?: string | undefined;
  actual_start?: string | undefined;
  actual_end?: string | undefined;
  planned_duration?: number | undefined;
  actual_duration?: number | undefined;
  completed_tasks?: number | undefined;
  total_tasks?: number | undefined;
  machine_id?: string | undefined;
  crew_id?: string | undefined;
  status: "SCHEDULED" | "ACTIVE" | "COMPLETED" | "PARTIAL" | "ABANDONED";
  deviation_reason?: string | undefined;
  notes?: string | undefined;
  recorded_by?: string | undefined;
}

export const executionApi = {
  getExecutionRecords: async (status?: string): Promise<{ records: ExecutionRecord[]; count: number }> => {
    const query = status ? `?status=${encodeURIComponent(status)}` : "";
    return apiClient<{ records: ExecutionRecord[]; count: number }>(`/execution${query}`);
  },

  getActiveExecutions: async (): Promise<{ active_executions: ActiveExecution[] }> => {
    return apiClient<{ active_executions: ActiveExecution[] }>("/execution/active");
  },

  getExecutionKPIs: async (): Promise<ExecutionKPIs> => {
    return apiClient<ExecutionKPIs>("/execution/kpis");
  },

  getExecutionMetrics: async () => {
    return apiClient<{ status: string; metrics: Record<string, unknown> }>("/execution/metrics");
  },

  getExecutionAnalytics: async (): Promise<ExecutionAnalyticsData> => {
    return apiClient<ExecutionAnalyticsData>("/execution/analytics");
  },

  getExecutionById: async (id: string): Promise<ExecutionRecord> => {
    return apiClient<ExecutionRecord>(`/execution/${encodeURIComponent(id)}`);
  },

  createExecutionRecord: async (payload: RecordOutcomePayload): Promise<{ status: string; record: ExecutionRecord }> => {
    return apiClient<{ status: string; record: ExecutionRecord }>("/execution", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  updateExecutionRecord: async (
    id: string,
    payload: Partial<RecordOutcomePayload>,
  ): Promise<{ status: string; record: ExecutionRecord }> => {
    return apiClient<{ status: string; record: ExecutionRecord }>(`/execution/${encodeURIComponent(id)}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  recordOutcome: async (
    blockId: string,
    payload: RecordOutcomePayload,
  ): Promise<{ status: string; record: ExecutionRecord }> => {
    return apiClient<{ status: string; record: ExecutionRecord }>("/execution", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};
