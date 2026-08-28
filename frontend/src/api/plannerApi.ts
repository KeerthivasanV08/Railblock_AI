import { apiClient } from "./client";

export interface OptimizationMetrics {
  status: string;
  solver_name?: string;
  candidate_count: number;
  selected_count: number;
  objective_value?: number;
  run_id?: string;
  runtime_ms?: number;
  configuration?: Record<string, unknown>;
}

export interface OptimizationResponse {
  status: string;
  metrics: OptimizationMetrics;
  selected_blocks: number;
}

export interface WeeklyPlanItem {
  block_id: string;
  section_id: string;
  from_km?: number;
  to_km?: number;
  date?: string;
  start_time?: string;
  end_time?: string;
  duration_minutes?: number;
  start_min?: number;
  duration_min?: number;
  departments?: string | string[];
  status?: string;
  optimization_score?: number;
  priority_score?: number;
  utilization?: number;
  required_resources?: string[];
  task_count?: number;
  tasks?: string[];
}

export interface WeeklyPlanResponse {
  status: string;
  weekly_plan: WeeklyPlanItem[];
}

export interface MonthlyPlanResponse {
  status: string;
  monthly_plan: WeeklyPlanItem[];
}

export const plannerApi = {
  runOptimization: async (): Promise<OptimizationResponse> => {
    return apiClient<OptimizationResponse>("/planner/optimize", {
      method: "POST",
    });
  },

  createWeeklyPlan: async (startDate?: string, sectionId?: string): Promise<WeeklyPlanResponse> => {
    const params = new URLSearchParams();
    if (startDate) params.set("start_date", startDate);
    if (sectionId) params.set("section_id", sectionId);
    const query = params.toString() ? `?${params.toString()}` : "";
    return apiClient<WeeklyPlanResponse>(`/planner/weekly${query}`, {
      method: "POST",
    });
  },

  createMonthlyPlan: async (startDate?: string): Promise<MonthlyPlanResponse> => {
    const params = new URLSearchParams();
    if (startDate) params.set("start_date", startDate);
    const query = params.toString() ? `?${params.toString()}` : "";
    return apiClient<MonthlyPlanResponse>(`/planner/monthly${query}`, {
      method: "POST",
    });
  },

  getRollingPlan: async (page = 1, pageSize = 50) => {
    return apiClient(`/planner/rolling?page=${page}&page_size=${pageSize}`);
  },
};
