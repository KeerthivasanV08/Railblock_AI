import { useEffect } from "react";
import type { ReactNode } from "react";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { Toaster } from "@/components/ui/sonner";
import { useSettingsStore } from "@/stores/settingsStore";
import { AppSidebar } from "./AppSidebar";
import { TopHeader } from "./TopHeader";
import { CommandPalette } from "./CommandPalette";

export function AppShell({ children }: { children: ReactNode }) {
  const sidebarCollapsed = useSettingsStore((s) => s.sidebarCollapsed);
  const toggleSidebar = useSettingsStore((s) => s.toggleSidebar);
  const setCommandOpen = useSettingsStore((s) => s.setCommandOpen);

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
