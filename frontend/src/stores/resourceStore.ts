import { create } from "zustand";
import type { Crew, Machine, ResourceAvailability } from "@/types";
import { generateCrews, generateMachines } from "@/data/resources";
import { resourcesApi } from "@/api";
import { adaptBackendCrew, adaptBackendMachine } from "@/utils/backendAdapters";
import type { DataProvenance } from "@/utils/backendAdapters";

interface ResourceState {
  machines: Machine[];
  crews: Crew[];
  selectedResourceId: string | null;
  dataSource: DataProvenance;
  loading: boolean;
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
  dataSource: "SYNTHETIC",
  loading: false,
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
    set({ loading: true });

    // Primary source: backend machinery
    resourcesApi
      .getMachines(1, 100)
      .then((res) => {
        const items = res?.items ?? [];
        if (items.length > 0) {
          set((s) => ({
            machines: items.map(adaptBackendMachine),
            dataSource: "DERIVED",
            loading: false,
          }));
        } else {
          // Backend returned nothing — keep synthetic
          set({ dataSource: "SYNTHETIC", loading: false });
        }
      })
      .catch(() => {
        set({ dataSource: "SYNTHETIC", loading: false });
      });

    // Primary source: backend crews
    resourcesApi
      .getCrews(1, 100)
      .then((res) => {
        const items = res?.items ?? [];
        if (items.length > 0) {
          set({ crews: items.map(adaptBackendCrew) });
        }
      })
      .catch(() => {});
  },
}));
