import { useEffect, useState } from "react";
import { Search, Settings, TrainFront } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SidebarTrigger } from "@/components/ui/sidebar";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { DEMO_ROLES, useSettingsStore } from "@/stores/settingsStore";
import { useTaskStore } from "@/stores/taskStore";
import { usePlannerStore } from "@/stores/plannerStore";
import { NotificationCentre } from "./NotificationCentre";
import { Link } from "@tanstack/react-router";
import { CORRIDOR } from "@/data/corridor";

export function TopHeader() {
  const role = useSettingsStore((s) => s.role);
  const setRole = useSettingsStore((s) => s.setRole);
  const setCommandOpen = useSettingsStore((s) => s.setCommandOpen);
  const [now, setNow] = useState(() => new Date());
  const taskSource = useTaskStore((s) => s.dataSource);
  const plannerSource = usePlannerStore((s) => s.dataSource);
  const isLiveBackend = taskSource !== "SYNTHETIC" || plannerSource !== "SYNTHETIC";

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <header className="flex h-12 shrink-0 items-center justify-between gap-2 border-b border-border bg-surface px-3">
      <div className="flex items-center gap-2.5 min-w-0">
        <SidebarTrigger className="shrink-0" />
        <Link to="/dashboard" className="flex items-center gap-1.5 md:hidden shrink-0">
          <TrainFront className="size-4 text-primary" aria-hidden />
          <span className="text-sm font-bold">RailBlock AI</span>
        </Link>

        <div className="hidden items-center gap-2 rounded border border-border bg-surface-2 px-2.5 py-1 md:flex shrink-0">
          <span className="relative flex size-2">
            <span className={`absolute inline-flex h-full w-full animate-ping rounded-full ${isLiveBackend ? "bg-ok" : "bg-warn"} opacity-60`} />
            <span className={`relative inline-flex size-2 rounded-full ${isLiveBackend ? "bg-ok" : "bg-warn"}`} />
          </span>
          <span className="text-[11px] font-semibold tracking-wide text-foreground whitespace-nowrap">
            {isLiveBackend ? "BACKEND CONNECTED" : "OFFLINE / SIMULATION"}
          </span>
          <span className="text-border-strong hidden xl:inline">·</span>
          <span className={`text-[11px] font-medium hidden xl:inline whitespace-nowrap ${isLiveBackend ? "text-ok" : "text-warn"}`}>
            {isLiveBackend ? "Live Railway Data" : "Synthetic Fallback"}
          </span>
          <span className="text-border-strong hidden 2xl:inline">·</span>
          <span className="text-[11px] text-muted-foreground hidden 2xl:inline whitespace-nowrap">{CORRIDOR.displayName}</span>
        </div>
      </div>

      <div className="flex items-center gap-2 shrink-0">
        <button
          onClick={() => setCommandOpen(true)}
          className="hidden items-center gap-2 rounded border border-border bg-surface-2 px-2.5 py-1 text-[11px] text-muted-foreground transition-colors hover:border-border-strong hover:text-foreground lg:flex"
        >
          <Search className="size-3.5" aria-hidden />
          <span className="hidden xl:inline">Search tasks, blocks, trains…</span>
          <span className="xl:hidden">Search…</span>
          <kbd className="ml-1.5 rounded border border-border bg-background px-1 font-mono text-[10px]">
            Ctrl K
          </kbd>
        </button>
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden shrink-0"
          onClick={() => setCommandOpen(true)}
          aria-label="Search"
        >
          <Search className="size-4" aria-hidden />
        </Button>

        <span className="hidden font-mono text-xs tabular-nums text-muted-foreground 2xl:inline-block shrink-0 px-1">
          {now.toLocaleDateString(undefined, { day: "2-digit", month: "short" })}{" "}
          {now.toLocaleTimeString(undefined, {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
          })}
        </span>

        <Select value={role} onValueChange={(v) => setRole(v as typeof role)}>
          <SelectTrigger className="h-8 w-[150px] sm:w-[170px] text-xs shrink-0" aria-label="Demo role selector">
            <SelectValue />
          </SelectTrigger>
          <SelectContent align="end">
            {DEMO_ROLES.map((r) => (
              <SelectItem key={r} value={r} className="text-xs">
                Demo Role: {r}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <NotificationCentre />

        <Link to="/admin" className="shrink-0">
          <Button variant="ghost" size="icon" aria-label="Administration">
            <Settings className="size-4" aria-hidden />
          </Button>
        </Link>
      </div>
    </header>
  );
}
