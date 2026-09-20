import { apiClient } from "./client";

export interface TaskQueryParams {
  page?: number;
  page_size?: number;
  department?: string;
  severity?: string;
  status?: string;
  section_id?: string;
  min_priority?: number;
  overdue_only?: boolean;
  recommended_only?: boolean;
  search?: string;
}

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  page_size: number;
  items: T[];
  data?: T[];
  records?: T[];
}

export interface BackendTask {
  task_id: string;
  source_system?: string;
  department: string;
  section_id: string;
  location_reference_type?: string;
  location_reference_id?: string;
  mapped_chainage_km?: number;
  latitude?: number;
  longitude?: number;
  defect_type?: string;
  defect?: string;
  severity_class?: string;
  severity?: string;
  overdue_days?: number;
  deferred_count?: number;
  previous_deferrals?: number;
  traffic_density?: number;
  traffic_density_class?: string;
  estimated_duration_minutes?: number;
  required_resource_type?: string;
  priority_score?: number;
  criticality_score?: number;
  priority_band?: string;
  status?: string;
  is_primary_task?: boolean;
  cluster_id?: string;
  mast_number?: string;
  signal_id?: string;
}

export interface TaskPriorityResponse {
  task_id: string;
  priority_score: number;
  criticality_score?: number;
  priority_band: string;
  risk_level?: string;
  components?: {
    severity: number;
    overdue_days: number;
    traffic_density: number;
    deferrals: number;
  };
  explanation?: {
    summary: string;
    risk_drivers: string[];
    safety_justification: string;
  };
  model_version?: string;
}

export const tasksApi = {
  getTasks: async (params: TaskQueryParams = {}): Promise<PaginatedResponse<BackendTask>> => {
    const query = new URLSearchParams();
    if (params.page) query.set("page", String(params.page));
    if (params.page_size) query.set("page_size", String(params.page_size));
    if (params.department) query.set("department", params.department);
    if (params.severity) query.set("severity", params.severity);
    if (params.status) query.set("status", params.status);
    if (params.section_id) query.set("section_id", params.section_id);
    if (params.min_priority !== undefined && params.min_priority > 0) query.set("min_priority", String(params.min_priority));
    if (params.overdue_only) query.set("overdue_only", "true");
    if (params.recommended_only) query.set("recommended_only", "true");
    if (params.search) query.set("search", params.search);

    return apiClient<PaginatedResponse<BackendTask>>(`/tasks?${query.toString()}`);
  },

  getTaskById: async (taskId: string): Promise<BackendTask> => {
    return apiClient<BackendTask>(`/tasks/${taskId}`);
  },

  getTaskPriority: async (taskId: string): Promise<TaskPriorityResponse> => {
    return apiClient<TaskPriorityResponse>(`/tasks/${taskId}/priority`);
  },

  unifyTasks: async (planningDate?: string): Promise<{ status: string; task_count: number }> => {
    return apiClient<{ status: string; task_count: number }>("/tasks/unify", {
      method: "POST",
      body: JSON.stringify({ planning_date: planningDate }),
    });
  },
};
