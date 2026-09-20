import { apiClient } from "./client";
import type { PaginatedResponse } from "./tasksApi";

export interface BackendMachine {
  resource_id: string;
  type: string;
  department: string;
  home_depot: string;
  current_location: string;
  km?: number;
  availability: string;
  last_updated?: string;
  assigned_task_id?: string | null;
  utilization?: number;
}

export interface BackendCrew {
  crew_id: string;
  department: string;
  depot: string;
  shift: string;
  headcount: number;
  availability: string;
  assigned_block_id?: string | null;
  km?: number;
  utilization?: number;
}

export const resourcesApi = {
  getMachines: async (
    page = 1,
    pageSize = 50,
    resourceType?: string,
  ): Promise<PaginatedResponse<BackendMachine>> => {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (resourceType) params.set("resource_type", resourceType);
    return apiClient<PaginatedResponse<BackendMachine>>(`/resources?${params.toString()}`);
  },

  getCrews: async (
    page = 1,
    pageSize = 50,
    department?: string,
  ): Promise<PaginatedResponse<BackendCrew>> => {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (department) params.set("department", department);
    return apiClient<PaginatedResponse<BackendCrew>>(`/resources/crew?${params.toString()}`);
  },

  getLiveResources: async () => {
    return apiClient<{ status: string; machinery: BackendMachine[]; crews: BackendCrew[] }>(
      "/resources/live",
    );
  },

  getCalendar: async (
    page = 1,
    pageSize = 50,
  ): Promise<PaginatedResponse<CalendarRecord>> => {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    return apiClient<PaginatedResponse<CalendarRecord>>(`/resources/calendar?${params.toString()}`);
  },
};

export interface CalendarRecord {
  resource: string;
  resource_id: string;
  resource_type: string;
  type_name: string;
  department: string;
  date: string;
  start_time: string;
  end_time: string;
  availability: string;
  assignment: string;
  block_id: string;
  status: string;
  utilization: number;
}
