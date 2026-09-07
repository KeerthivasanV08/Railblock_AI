import { useEffect } from "react";
import type { ReactNode } from "react";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { Toaster } from "@/components/ui/sonner";
import { useSettingsStore } from "@/stores/settingsStore";
import { useTaskStore } from "@/stores/taskStore";
import { usePlannerStore } from "@/stores/plannerStore";
import { useDisruptionStore } from "@/stores/disruptionStore";
import { useResourceStore } from "@/stores/resourceStore";
import { useOperationsStore } from "@/stores/operationsStore";
import { AppSidebar } from "./AppSidebar";
import { TopHeader } from "./TopHeader";
import { CommandPalette } from "./CommandPalette";

export function AppShell({ children }: { children: ReactNode }) {
  const sidebarCollapsed = useSettingsStore((s) => s.sidebarCollapsed);
  const toggleSidebar = useSettingsStore((s) => s.toggleSidebar);
  const setCommandOpen = useSettingsStore((s) => s.setCommandOpen);

  const loadTasks = useTaskStore((s) => s.loadFromBackend);
  const loadBlocks = usePlannerStore((s) => s.loadBlocksFromBackend);
  const loadDisruptions = useDisruptionStore((s) => s.loadFromBackend);
  const fetchResources = useResourceStore((s) => s.fetchResources);
  const initLiveStream = useOperationsStore((s) => s.initLiveStream);

  // ── Global data bootstrap ───────────────────────────────────────────────
  // On mount: fire all backend loads in parallel (fire-and-forget, silent fallback).
  // Each store handles its own error → falls back to synthetic data.
  useEffect(() => {
    void loadTasks();
    void loadBlocks();
    void loadDisruptions();
    fetchResources();
    initLiveStream();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCommandOpen(true);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [setCommandOpen]);

  return (
    <div className="dark h-svh w-full overflow-hidden bg-background text-foreground">
      <SidebarProvider
        open={!sidebarCollapsed}
        onOpenChange={(open) => toggleSidebar()}
        className="h-full"
      >
        <AppSidebar />
        <SidebarInset className="flex h-svh min-w-0 flex-col overflow-hidden">
          <TopHeader />
          <main className="flex-1 overflow-auto">{children}</main>
        </SidebarInset>
      </SidebarProvider>
      <CommandPalette />
      <Toaster position="top-right" richColors />
    </div>
  );
}

