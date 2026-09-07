import { apiClient } from "./client";
import type { PaginatedResponse } from "./tasksApi";

export interface BackendDisruptionEvent {
  event_id: string;
  event_type: string;
  section_id: string;
  location?: string;
  severity: string;
  delay_minutes?: number;
  train_number?: string;
  affected_block_id?: string | null;
  detected_at?: string;
  status?: string;
}

export interface RescheduleOptionItem {
  option_id: string;
  action_type: "delay" | "shift" | "reallocate";
  original_block_id: string;
  section_id: string;
  proposed_start_time: string;
  proposed_end_time: string;
  duration_minutes: number;
  shift_from_original_hours: number;
  traffic_density: number;
  machine_available: boolean;
  crew_available: boolean;
  optimization_score: number;
  feasible: boolean;
  failed_constraints: string[];
  rejection_reason: string;
  feasibility_explanation: string;
  reason: string;
  scoring_mode?: string;
}

export interface RescheduleResponse {
  status: string;
  request_id: string;
  engine_version: string;
  scoring_mode: string;
  timing_ms: number;
  event_id: string;
  affected_block_id: string;
  constraint_validation_summary: {
    total_candidates: number;
    feasible_count: number;
    infeasible_count: number;
    scoring_mode: string;
  };
  approval_required: boolean;
  approval_note: string;
  options: RescheduleOptionItem[];
}

export const disruptionsApi = {
  getDisruptions: async (
    page = 1,
    pageSize = 50,
    eventType?: string,
  ): Promise<PaginatedResponse<BackendDisruptionEvent>> => {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (eventType) params.set("event_type", eventType);
    return apiClient<PaginatedResponse<BackendDisruptionEvent>>(
      `/disruptions?${params.toString()}`,
    );
  },

  detectDisruptions: async (): Promise<{
    status: string;
    disruptions_detected_count: number;
    disruptions: BackendDisruptionEvent[];
  }> => {
    return apiClient<{
      status: string;
      disruptions_detected_count: number;
      disruptions: BackendDisruptionEvent[];
    }>("/disruptions/detect", {
      method: "POST",
    });
  },

  rescheduleBlock: async (
    eventId: string,
    affectedBlockId: string,
    blockMetadata?: Record<string, unknown>,
  ): Promise<RescheduleResponse> => {
    const params = new URLSearchParams({
      event_id: eventId,
      affected_block_id: affectedBlockId,
    });
    return apiClient<RescheduleResponse>(`/disruptions/reschedule?${params.toString()}`, {
      method: "POST",
      ...(blockMetadata ? { body: JSON.stringify(blockMetadata) } : {}),
    });
  },

  approveReschedule: async (
    optionId: string,
    actor = "Controller",
    confirmedFeasible = true,
  ): Promise<{
    status: string;
    reschedule_record: Record<string, unknown>;
    plan_update_note: string;
  }> => {
    const params = new URLSearchParams({
      option_id: optionId,
      actor,
      confirmed_feasible: String(confirmedFeasible),
    });
    return apiClient<{
      status: string;
      reschedule_record: Record<string, unknown>;
      plan_update_note: string;
    }>(`/disruptions/approve?${params.toString()}`, { method: "POST" });
  },
};
