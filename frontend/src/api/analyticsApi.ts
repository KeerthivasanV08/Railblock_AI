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

export interface OverviewKPIs extends Record<string, unknown> {
  asset_availability?: string;
  maintenance_completion?: string;
  active_blocks?: number;
  critical_defects?: number;
  overdue_tasks?: number;
  block_utilization?: string;
  integrated_block_percentage?: string;
  unused_block_time_minutes?: number;
  deferred_tasks?: number;
  total_unified_tasks?: number;
  pending_approvals?: number;
  approved_blocks?: number;
  total_blocks?: number;
}

export const analyticsApi = {
  getOverviewKPIs: async () => {
    return apiClient<OverviewKPIs>("/analytics/overview");
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
