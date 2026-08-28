import { apiClient } from "./client";
import type { PaginatedResponse } from "./tasksApi";

export interface BackendAuditRecord {
  audit_id: string;
  timestamp_utc: string;
  user_role: string;
  action: string;
  entity_id: string;
  status: string;
  old_value?: string;
  new_value?: string;
  rationale?: string;
}

export const analyticsApi = {
  getOverviewKPIs: async () => {
    return apiClient<Record<string, unknown>>("/analytics/overview");
  },

  getImpactAnalysis: async () => {
    return apiClient<Record<string, unknown>>("/analytics/impact");
  },

  getDepartmentWorkload: async () => {
    return apiClient<Record<string, unknown>>("/analytics/department-workload");
  },

  getAuditLogs: async (page = 1, pageSize = 50): Promise<PaginatedResponse<BackendAuditRecord>> => {
    return apiClient<PaginatedResponse<BackendAuditRecord>>(
      `/audit?page=${page}&page_size=${pageSize}`,
    );
  },
};
