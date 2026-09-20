import { create } from "zustand";
import type { Department, MaintenanceTask, Severity, TaskStatus } from "@/types";
import { getAllTasks } from "@/data/tasks";
import { tasksApi } from "@/api";
import { adaptBackendTask } from "@/utils/backendAdapters";
import type { DataProvenance } from "@/utils/backendAdapters";

export interface TaskFilters {
  search: string;
  departments: Department[];
  severities: Severity[];
  statuses: TaskStatus[];
  minPriority: number;
  overdueOnly: boolean;
  recommendedOnly: boolean;
  sectionId: string | null;
}

export const emptyFilters: TaskFilters = {
  search: "",
  departments: [],
  severities: [],
  statuses: [],
  minPriority: 0,
  overdueOnly: false,
  recommendedOnly: false,
  sectionId: null,
};

interface TaskState {
  tasks: MaintenanceTask[];
  dataSource: DataProvenance;
  totalBackendCount: number;
  loading: boolean;
  filters: TaskFilters;
  page: number;
  pageSize: number;
  selectedTaskId: string | null;
  setFilters: (patch: Partial<TaskFilters>) => void;
  resetFilters: () => void;
  setPage: (page: number) => void;
  select: (id: string | null) => void;
  setStatus: (taskId: string, status: TaskStatus) => void;
  setRecommendedBlock: (taskIds: string[], blockId: string | null) => void;
  /** Fetches tasks from backend and replaces store state. Supports server-side filtering. */
  loadFromBackend: (customFilters?: Partial<TaskFilters>) => Promise<void>;
}

export const useTaskStore = create<TaskState>((set, get) => ({
  tasks: getAllTasks(),
  dataSource: "SYNTHETIC",
  totalBackendCount: 0,
  loading: false,
  filters: emptyFilters,
  page: 1,
  pageSize: 25,
  selectedTaskId: null,

  setFilters: (patch) => set((s) => ({ filters: { ...s.filters, ...patch }, page: 1 })),
  resetFilters: () => set({ filters: emptyFilters, page: 1 }),
  setPage: (page) => set({ page }),
  select: (selectedTaskId) => set({ selectedTaskId }),

  setStatus: (taskId, status) =>
    set((s) => ({ tasks: s.tasks.map((t) => (t.task_id === taskId ? { ...t, status } : t)) })),

  setRecommendedBlock: (taskIds, blockId) =>
    set((s) => ({
      tasks: s.tasks.map((t) =>
        taskIds.includes(t.task_id) ? { ...t, recommended_block_id: blockId } : t,
      ),
    })),

  loadFromBackend: async (customFilters?: Partial<TaskFilters>) => {
    set({ loading: true });
    try {
      const f = { ...get().filters, ...(customFilters || {}) };
      const queryParams: import("@/api/tasksApi").TaskQueryParams = {
        page: 1,
        page_size: 500,
      };
      const dept = f.departments.length === 1 ? f.departments[0] : undefined;
      const sev = f.severities.length === 1 ? f.severities[0] : undefined;
      const stat = f.statuses.length === 1 ? f.statuses[0] : undefined;
      if (dept) queryParams.department = dept;
      if (sev) queryParams.severity = sev;
      if (stat) queryParams.status = stat;
      if (f.sectionId) queryParams.section_id = f.sectionId;
      if (f.minPriority > 0) queryParams.min_priority = f.minPriority;
      if (f.overdueOnly) queryParams.overdue_only = true;
      if (f.recommendedOnly) queryParams.recommended_only = true;
      if (f.search.trim()) queryParams.search = f.search.trim();

      const res = await tasksApi.getTasks(queryParams);
      const items = res?.items ?? res?.data ?? res?.records ?? [];
      if (items.length > 0) {
        const adapted = items.map(adaptBackendTask);
        set({
          tasks: adapted,
          dataSource: "DERIVED",
          totalBackendCount: res.total ?? adapted.length,
          loading: false,
        });
        return;
      }
    } catch {
      // Backend unreachable — stay on synthetic data
    }
    // Fallback: keep synthetic data, mark accordingly
    set({ dataSource: "SYNTHETIC", loading: false });
  },
}));

export function filterTasks(tasks: MaintenanceTask[], f: TaskFilters): MaintenanceTask[] {
  const q = f.search.trim().toLowerCase();
  return tasks.filter((t) => {
    if (f.departments.length && !f.departments.includes(t.department)) return false;
    if (f.severities.length && !f.severities.includes(t.severity)) return false;
    if (f.statuses.length && !f.statuses.includes(t.status)) return false;
    if (t.priority_score < f.minPriority) return false;
    if (f.overdueOnly && t.overdue_days <= 0) return false;
    if (f.recommendedOnly && !t.recommended_block_id) return false;
    if (f.sectionId && t.section_id !== f.sectionId) return false;
    if (q) {
      const hay =
        `${t.task_id} ${t.asset} ${t.section_id} ${t.defect} ${t.location_label}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });
}

