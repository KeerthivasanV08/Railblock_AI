import { create } from "zustand";
import type { Department, MaintenanceTask, Severity, TaskStatus } from "@/types";
import { getAllTasks } from "@/data/tasks";

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
}

export const useTaskStore = create<TaskState>((set) => ({
  tasks: getAllTasks(),
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
