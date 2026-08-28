import { create } from "zustand";
import type { DisruptionEvent, RescheduleOption } from "@/types";
import { generateDisruptions } from "@/data/operations";
import { generateRescheduleOptions } from "@/services/mock/aiService";
import { disruptionsApi } from "@/api";
import { usePlannerStore } from "./plannerStore";
import { useNotificationStore } from "./notificationStore";

interface SimulationResult {
  before: { start_min: number; duration_min: number };
  after: { start_min: number; duration_min: number };
  option: RescheduleOption;
}

interface DisruptionState {
  disruptions: DisruptionEvent[];
  selectedEventId: string | null;
  optionsByEvent: Record<string, RescheduleOption[]>;
  selectedOptionByEvent: Record<string, string>;
  simulationByEvent: Record<string, SimulationResult | null>;
  select: (id: string | null) => void;
  ensureOptions: (eventId: string) => void;
  selectOption: (eventId: string, optionId: string) => void;
  simulate: (eventId: string) => void;
  applyReschedule: (eventId: string) => void;
  dismiss: (eventId: string) => void;
  injectDisruption: (event: DisruptionEvent) => void;
}

function parseTimeToMin(timeStr?: string): number {
  if (!timeStr) return 120;
  try {
    const parts = timeStr.includes(" ") ? timeStr.split(" ")[1] : timeStr;
    const [h, m] = parts.split(":").map(Number);
    return (h || 0) * 60 + (m || 0);
  } catch {
    return 120;
  }
}

export const useDisruptionStore = create<DisruptionState>((set, get) => ({
  disruptions: generateDisruptions(),
  selectedEventId: "EVT-9001",
  optionsByEvent: {},
  selectedOptionByEvent: {},
  simulationByEvent: {},

  select: (selectedEventId) => set({ selectedEventId }),

  ensureOptions: (eventId) => {
    if (get().optionsByEvent[eventId]) return;
    const event = get().disruptions.find((e) => e.event_id === eventId);
    if (!event) return;
    const { blocks, trainPaths } = usePlannerStore.getState();
    const block = event.affected_block_id
      ? blocks.find((b) => b.block_id === event.affected_block_id)
      : undefined;

    // Generate immediate options from local logic
    const localOptions = generateRescheduleOptions(event, block, { trainPaths, blocks });
    set((s) => ({ optionsByEvent: { ...s.optionsByEvent, [eventId]: localOptions } }));

    // Request backend constraint-validated rescheduling in background
    disruptionsApi
      .rescheduleBlock(event.event_id, event.affected_block_id || "RB-402", {
        section_id: event.section_id,
        criticality_score: 85.0,
        duration_minutes: block?.duration_min ?? 180,
      })
      .then((res) => {
        if (res?.options?.length) {
          const backendMapped: RescheduleOption[] = res.options.map((opt) => ({
            id: opt.option_id,
            label: `${opt.action_type.toUpperCase()} · ${opt.proposed_start_time.split(" ")[1]?.slice(0, 5) || "02:00"} (${opt.feasible ? "Feasible" : "Infeasible"})`,
            start_min: parseTimeToMin(opt.proposed_start_time),
            duration_min: Math.round(opt.duration_minutes),
            train_impact:
              opt.traffic_density < 0.3 ? "Low" : opt.traffic_density < 0.7 ? "Medium" : "High",
            maintenance_impact: opt.reason,
            resource_impact:
              opt.machine_available && opt.crew_available
                ? "Machinery & Crew confirmed"
                : "Resource constraint flagged",
            utilization: Math.round(opt.optimization_score),
            confidence: opt.feasible ? 94 : 0,
            added_train_delay_min: Math.round(opt.shift_from_original_hours * 6),
          }));
          set((s) => ({ optionsByEvent: { ...s.optionsByEvent, [eventId]: backendMapped } }));
        }
      })
      .catch(() => {
        // Safe fallback preserved
      });
  },

  selectOption: (eventId, optionId) =>
    set((s) => ({ selectedOptionByEvent: { ...s.selectedOptionByEvent, [eventId]: optionId } })),

  simulate: (eventId) => {
    const event = get().disruptions.find((e) => e.event_id === eventId);
    const options = get().optionsByEvent[eventId];
    const chosenId = get().selectedOptionByEvent[eventId];
    const option = options?.find((o) => o.id === chosenId) ?? options?.[0];
    if (!event || !option) return;
    const { blocks } = usePlannerStore.getState();
    const block = event.affected_block_id
      ? blocks.find((b) => b.block_id === event.affected_block_id)
      : undefined;
    set((s) => ({
      simulationByEvent: {
        ...s.simulationByEvent,
        [eventId]: {
          before: { start_min: block?.start_min ?? 0, duration_min: block?.duration_min ?? 0 },
          after: { start_min: option.start_min, duration_min: option.duration_min },
          option,
        },
      },
    }));
    useNotificationStore.getState().logAudit("Simulated Reschedule", eventId);
    useNotificationStore.getState().push({
      type: "Disruption",
      title: `Simulation complete for ${eventId}`,
      body: `Option ${option.id.replace("OPT-", "")} evaluated — ${option.train_impact} train impact.`,
      href: `/disruptions/${eventId}`,
      severity: "Info",
    });
  },

  applyReschedule: (eventId) => {
    const event = get().disruptions.find((e) => e.event_id === eventId);
    const options = get().optionsByEvent[eventId];
    const chosenId = get().selectedOptionByEvent[eventId];
    const option = options?.find((o) => o.id === chosenId) ?? options?.[0];
    if (!event || !option) return;
    if (event.affected_block_id) {
      usePlannerStore
        .getState()
        .applyExternalReschedule(event.affected_block_id, option.start_min, option.duration_min);
    }
    set((s) => ({
      disruptions: s.disruptions.map((e) =>
        e.event_id === eventId ? { ...e, status: "Rescheduled" as const } : e,
      ),
    }));
    useNotificationStore
      .getState()
      .logAudit(
        "Applied Reschedule",
        event.affected_block_id ?? eventId,
        "Success",
        `Moved to ${option.label}`,
      );
    useNotificationStore.getState().push({
      type: "Disruption",
      title: `Reschedule applied for ${eventId}`,
      body: `${event.affected_block_id ?? "Event"} rescheduled to ${option.label}. Added train delay: ${option.added_train_delay_min} min.`,
      href: "/planner",
      severity: "Info",
    });

    // Notify backend approval
    disruptionsApi.approveReschedule(option.id, "Section Controller", true).catch(() => {});
  },

  dismiss: (eventId) => {
    set((s) => ({
      disruptions: s.disruptions.map((e) =>
        e.event_id === eventId ? { ...e, status: "Dismissed" as const } : e,
      ),
    }));
    useNotificationStore.getState().logAudit("Dismissed Disruption", eventId);
  },

  injectDisruption: (event) =>
    set((s) => ({ disruptions: [event, ...s.disruptions], selectedEventId: event.event_id })),
}));
