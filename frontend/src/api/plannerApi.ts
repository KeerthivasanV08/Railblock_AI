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

export interface RollingPlanResponse {
  status: string;
  horizon_weeks: number;
  total_blocks: number;
  rolling_plan: RollingPlanBlock[];
}

export interface RollingPlanBlock {
  block_id: string;
  plan_run_id?: string;
  plan_version?: number;
  horizon?: string;
  week_number?: number;
  generated_at?: string;
  plan_date?: string;
  date?: string;
  section_id: string;
  start_time?: string;
  end_time?: string;
  duration_minutes?: number;
  task_ids?: string;
  departments?: string;
  priority?: number;
  priority_score?: number;
  overdue_days_projected?: number;
  deferred_count_projected?: number;
  seasonal_risk_score_projected?: number;
  maintenance_type?: string;
  resources?: string;
  crew?: string;
  train_impact?: string;
  utilization?: number;
  status: string;
  xai_reason?: string;
  source?: string;
}

export interface RollingPlanQueryParams {
  page?: number;
  page_size?: number;
  week_number?: number;
  department?: string;
  status?: string;
  section_id?: string;
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

  createRollingPlan: async (
    startDate?: string,
    horizonWeeks = 26,
  ): Promise<RollingPlanResponse> => {
    const params = new URLSearchParams();
    if (startDate) params.set("start_date", startDate);
    params.set("horizon_weeks", String(horizonWeeks));
    const query = params.toString() ? `?${params.toString()}` : "";
    return apiClient<RollingPlanResponse>(`/planner/rolling${query}`, {
      method: "POST",
    });
  },

  getRollingPlan: async (
    pageOrParams: number | RollingPlanQueryParams = 1,
    pageSize = 100,
  ) => {
    const params: RollingPlanQueryParams =
      typeof pageOrParams === "number"
        ? { page: pageOrParams, page_size: pageSize }
        : pageOrParams;

    const query = new URLSearchParams();
    if (params.page) query.set("page", String(params.page));
    if (params.page_size) query.set("page_size", String(params.page_size));
    if (params.week_number) query.set("week_number", String(params.week_number));
    if (params.department) query.set("department", params.department);
    if (params.status) query.set("status", params.status);
    if (params.section_id) query.set("section_id", params.section_id);

    return apiClient<{
      total?: number;
      page?: number;
      page_size?: number;
      items?: RollingPlanBlock[];
      records?: RollingPlanBlock[];
    }>(`/planner/rolling?${query.toString()}`);
  },
};

