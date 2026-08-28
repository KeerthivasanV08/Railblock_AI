import { useMemo } from "react";
import { useNavigate } from "@tanstack/react-router";
import { ClipboardList, MapPin, Sparkles, TrainFront, Wrench, Waypoints } from "lucide-react";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { useSettingsStore } from "@/stores/settingsStore";
import { useTaskStore } from "@/stores/taskStore";
import { usePlannerStore } from "@/stores/plannerStore";
import { useRecommendationStore } from "@/stores/recommendationStore";
import { useResourceStore } from "@/stores/resourceStore";
import { STATIONS } from "@/data/stations";

export function CommandPalette() {
  const open = useSettingsStore((s) => s.commandOpen);
  const setOpen = useSettingsStore((s) => s.setCommandOpen);
  const navigate = useNavigate();

  const tasks = useTaskStore((s) => s.tasks);
  const blocks = usePlannerStore((s) => s.blocks);
  const recommendations = useRecommendationStore((s) => s.recommendations);
  const machines = useResourceStore((s) => s.machines);

  const topTasks = useMemo(
    () => [...tasks].sort((a, b) => b.priority_score - a.priority_score).slice(0, 8),
    [tasks],
  );

  const go = (to: string) => {
    setOpen(false);
    navigate({ to });
  };

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Search task ID, block ID, train number, station, machine, recommendation…" />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>
        <CommandGroup heading="Blocks">
          {blocks.slice(0, 8).map((b) => (
            <CommandItem key={b.block_id} onSelect={() => go("/planner")}>
              <Waypoints className="mr-2 size-4" aria-hidden />
              Block {b.block_id} — {b.section_id}
            </CommandItem>
          ))}
        </CommandGroup>
        <CommandGroup heading="Maintenance Tasks (top priority)">
          {topTasks.map((t) => (
            <CommandItem key={t.task_id} onSelect={() => go(`/tasks/${t.task_id}`)}>
              <ClipboardList className="mr-2 size-4" aria-hidden />
              {t.task_id} — {t.defect}
            </CommandItem>
          ))}
        </CommandGroup>
        <CommandGroup heading="AI Recommendations">
          {recommendations.map((r) => (
            <CommandItem
              key={r.recommendation_id}
              onSelect={() => go(`/recommendations/${r.recommendation_id}`)}
            >
              <Sparkles className="mr-2 size-4" aria-hidden />
              {r.recommendation_id} — Block {r.block_id}
            </CommandItem>
          ))}
        </CommandGroup>
        <CommandGroup heading="Stations">
          {STATIONS.map((s) => (
            <CommandItem key={s.station_code} onSelect={() => go("/live")}>
              <MapPin className="mr-2 size-4" aria-hidden />
              {s.name} ({s.station_code}) — Km {s.km}
            </CommandItem>
          ))}
        </CommandGroup>
        <CommandGroup heading="Machines">
          {machines.slice(0, 8).map((m) => (
            <CommandItem key={m.resource_id} onSelect={() => go("/resources")}>
              <Wrench className="mr-2 size-4" aria-hidden />
              {m.resource_id} — {m.type}
            </CommandItem>
          ))}
        </CommandGroup>
        <CommandGroup heading="Live">
          <CommandItem onSelect={() => go("/live")}>
            <TrainFront className="mr-2 size-4" aria-hidden />
            Open Live Corridor Monitor
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
