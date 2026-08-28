import { create } from "zustand";
import type { DemoRole } from "@/types";

export const DEMO_ROLES: DemoRole[] = [
  "Control Office Operator",
  "Section Controller",
  "DRM / Divisional Officer",
  "Engineering Planner",
  "TRD Planner",
  "S&T Planner",
  "Field Maintenance Team",
  "System Administrator",
];

interface SettingsState {
  role: DemoRole;
  sidebarCollapsed: boolean;
  intelPanelOpen: boolean;
  commandOpen: boolean;
  setRole: (role: DemoRole) => void;
  toggleSidebar: () => void;
  setIntelPanel: (open: boolean) => void;
  setCommandOpen: (open: boolean) => void;
}

export const useSettingsStore = create<SettingsState>((set) => ({
  role: "Section Controller",
  sidebarCollapsed: false,
  intelPanelOpen: true,
  commandOpen: false,
  setRole: (role) => set({ role }),
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setIntelPanel: (intelPanelOpen) => set({ intelPanelOpen }),
  setCommandOpen: (commandOpen) => set({ commandOpen }),
}));
