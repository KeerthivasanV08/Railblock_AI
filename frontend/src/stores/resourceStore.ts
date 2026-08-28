import { create } from "zustand";
import type { Crew, Machine, ResourceAvailability } from "@/types";
import { generateCrews, generateMachines } from "@/data/resources";
import { resourcesApi } from "@/api";

interface ResourceState {
  machines: Machine[];
  crews: Crew[];
  selectedResourceId: string | null;
  select: (id: string | null) => void;
  setMachineAvailability: (id: string, availability: ResourceAvailability) => void;
  assignMachine: (id: string, taskId: string | null) => void;
  assignCrew: (id: string, blockId: string | null) => void;
  fetchResources: () => void;
}

export const useResourceStore = create<ResourceState>((set) => ({
  machines: generateMachines(),
  crews: generateCrews(),
  selectedResourceId: null,
  select: (selectedResourceId) => set({ selectedResourceId }),

  setMachineAvailability: (id, availability) =>
    set((s) => ({
      machines: s.machines.map((m) => (m.resource_id === id ? { ...m, availability } : m)),
    })),

  assignMachine: (id, taskId) =>
    set((s) => ({
      machines: s.machines.map((m) =>
        m.resource_id === id
          ? { ...m, assigned_task_id: taskId, availability: taskId ? "Assigned" : "Available" }
          : m,
      ),
    })),

  assignCrew: (id, blockId) =>
    set((s) => ({
      crews: s.crews.map((c) =>
        c.crew_id === id
          ? { ...c, assigned_block_id: blockId, availability: blockId ? "Assigned" : "Available" }
          : c,
      ),
    })),

  fetchResources: () => {
    // Enrich machine availability from backend (non-blocking)
    resourcesApi
      .getMachines(1, 100)
      .then((res) => {
        if (res?.items?.length) {
          set((s) => ({
            machines: s.machines.map((m) => {
              const live = res.items.find((b) => b.resource_id === m.resource_id);
              if (!live) return m;
              return {
                ...m,
                availability: (live.availability as ResourceAvailability) ?? m.availability,
                utilization: live.utilization ?? m.utilization,
              };
            }),
          }));
        }
      })
      .catch(() => {});

    // Enrich crew availability from backend (non-blocking)
    resourcesApi
      .getCrews(1, 100)
      .then((res) => {
        if (res?.items?.length) {
          set((s) => ({
            crews: s.crews.map((c) => {
              const live = res.items.find((b) => b.crew_id === c.crew_id);
              if (!live) return c;
              return {
                ...c,
                availability: (live.availability as ResourceAvailability) ?? c.availability,
                utilization: live.utilization ?? c.utilization,
              };
            }),
          }));
        }
      })
      .catch(() => {});
  },
}));
