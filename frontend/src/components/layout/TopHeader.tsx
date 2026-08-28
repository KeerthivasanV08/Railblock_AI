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
import { NotificationCentre } from "./NotificationCentre";
import { Link } from "@tanstack/react-router";

export function TopHeader() {
  const role = useSettingsStore((s) => s.role);
  const setRole = useSettingsStore((s) => s.setRole);
  const setCommandOpen = useSettingsStore((s) => s.setCommandOpen);
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <header className="flex h-12 shrink-0 items-center gap-3 border-b border-border bg-surface px-3">
      <SidebarTrigger />
      <Link to="/dashboard" className="flex items-center gap-1.5 md:hidden">
        <TrainFront className="size-4 text-primary" aria-hidden />
        <span className="text-sm font-bold">RailBlock AI</span>
      </Link>

      <div className="hidden items-center gap-2 rounded border border-border bg-surface-2 px-2.5 py-1 md:flex">
        <span className="relative flex size-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-ok opacity-60" />
          <span className="relative inline-flex size-2 rounded-full bg-ok" />
        </span>
        <span className="text-[11px] font-semibold tracking-wide text-foreground">
          SYSTEM OPERATIONAL
        </span>
        <span className="text-border-strong">·</span>
        <span className="text-[11px] text-muted-foreground">Synthetic Demo Data</span>
        <span className="text-border-strong">·</span>
        <span className="text-[11px] text-muted-foreground">Corridor: New Delhi – Kanpur</span>
      </div>

      <div className="flex-1" />

      <button
        onClick={() => setCommandOpen(true)}
        className="hidden items-center gap-2 rounded border border-border bg-surface-2 px-2.5 py-1 text-[11px] text-muted-foreground transition-colors hover:border-border-strong hover:text-foreground lg:flex"
      >
        <Search className="size-3.5" aria-hidden />
        Search tasks, blocks, trains…
        <kbd className="ml-2 rounded border border-border bg-background px-1 font-mono text-[10px]">
          Ctrl K
        </kbd>
      </button>
      <Button
        variant="ghost"
        size="icon"
        className="lg:hidden"
        onClick={() => setCommandOpen(true)}
        aria-label="Search"
      >
        <Search className="size-4" aria-hidden />
      </Button>

      <span className="hidden font-mono text-xs tabular-nums text-muted-foreground sm:inline">
        {now.toLocaleDateString(undefined, { day: "2-digit", month: "short" })}{" "}
        {now.toLocaleTimeString(undefined, {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        })}
      </span>

      <Select value={role} onValueChange={(v) => setRole(v as typeof role)}>
        <SelectTrigger className="h-8 w-[168px] text-xs" aria-label="Demo role selector">
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

      <Link to="/admin">
        <Button variant="ghost" size="icon" aria-label="Administration">
          <Settings className="size-4" aria-hidden />
        </Button>
      </Link>
    </header>
  );
}
