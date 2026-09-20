import React, { useMemo, useState } from "react";
import type { Crew, Machine } from "@/types";
import type { CalendarRecord } from "@/api/resourcesApi";
import { Badge } from "@/components/ui/badge";
import { AvailabilityBadge } from "@/components/common/StatusBadge";
import { DepartmentBadge } from "@/components/common/DomainBadges";
import { Wrench, Users, Calendar, Clock, Search, Filter } from "lucide-react";

interface ResourceCalendarProps {
  machines: Machine[];
  crews: Crew[];
  calendarItems?: CalendarRecord[];
}

export function ResourceCalendar({ machines, crews, calendarItems = [] }: ResourceCalendarProps) {
  const [filterType, setFilterType] = useState<"ALL" | "Machine" | "Crew">("ALL");
  const [search, setSearch] = useState("");

  // Build unified calendar entries from backend endpoint records or live store
  const entries = useMemo(() => {
    if (calendarItems && calendarItems.length > 0) {
      return calendarItems.map((c) => ({
        id: c.resource_id,
        name: c.resource,
        type: c.resource_type as "Machine" | "Crew",
        typeName: c.type_name,
        department: c.department,
        date: c.date,
        timeWindow: `${c.start_time} – ${c.end_time}`,
        availability: c.availability,
        assignment: c.assignment,
        blockId: c.block_id,
        utilization: c.utilization,
        status: c.status,
      }));
    }

    // Fallback: build from active machine & crew allocations if backend calendar returned empty
    const machineEntries = machines.map((m) => ({
      id: m.resource_id,
      name: `${m.resource_id} · ${m.type}`,
      type: "Machine" as const,
      typeName: m.type,
      department: m.department,
      date: "2026-09-01",
      timeWindow: "02:00 – 06:00",
      availability: m.availability,
      assignment: m.assigned_task_id ? `Assigned Task ${m.assigned_task_id}` : "Unassigned / Standby",
      blockId: m.assigned_task_id ?? "—",
      utilization: m.utilization,
      status: m.availability === "Assigned" ? "ALLOCATED" : "AVAILABLE",
    }));

    const crewEntries = crews.map((c) => ({
      id: c.crew_id,
      name: `${c.crew_id} · ${c.department}`,
      type: "Crew" as const,
      typeName: `${c.shift} (${c.headcount} staff)`,
      department: c.department,
      date: "2026-09-01",
      timeWindow: c.shift.includes("Night") ? "20:00 – 08:00" : "08:00 – 20:00",
      availability: c.availability,
      assignment: c.assigned_block_id ? `Block ${c.assigned_block_id}` : "Unassigned / Depot Standby",
      blockId: c.assigned_block_id ?? "—",
      utilization: c.utilization,
      status: c.availability === "Assigned" ? "ALLOCATED" : "AVAILABLE",
    }));

    return [...machineEntries, ...crewEntries];
  }, [calendarItems, machines, crews]);

  const filtered = useMemo(() => {
    return entries.filter((e) => {
      if (filterType !== "ALL" && e.type !== filterType) return false;
      if (search.trim()) {
        const q = search.toLowerCase();
        return (
          e.id.toLowerCase().includes(q) ||
          e.name.toLowerCase().includes(q) ||
          e.department.toLowerCase().includes(q) ||
          e.assignment.toLowerCase().includes(q) ||
          e.blockId.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [entries, filterType, search]);

  return (
    <div className="space-y-3">
      {/* Filter and Search Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-border bg-surface-2/40 p-2.5 text-xs">
        <div className="flex items-center gap-2">
          <div className="flex items-center rounded-md border border-border bg-background p-0.5">
            <button
              onClick={() => setFilterType("ALL")}
              className={`rounded px-2.5 py-1 text-xs font-medium transition-colors ${
                filterType === "ALL"
                  ? "bg-primary text-primary-foreground font-semibold"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              All Resources ({entries.length})
            </button>
            <button
              onClick={() => setFilterType("Machine")}
              className={`flex items-center gap-1 rounded px-2.5 py-1 text-xs font-medium transition-colors ${
                filterType === "Machine"
                  ? "bg-primary text-primary-foreground font-semibold"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Wrench className="size-3" aria-hidden /> Machines
            </button>
            <button
              onClick={() => setFilterType("Crew")}
              className={`flex items-center gap-1 rounded px-2.5 py-1 text-xs font-medium transition-colors ${
                filterType === "Crew"
                  ? "bg-primary text-primary-foreground font-semibold"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Users className="size-3" aria-hidden /> Crews
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" aria-hidden />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search resource, block, task..."
              className="h-7 w-56 rounded-md border border-border bg-background pl-8 pr-2.5 text-xs text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none"
            />
          </div>
          <span className="font-mono text-[11px] text-muted-foreground">
            {filtered.length} scheduled
          </span>
        </div>
      </div>

      {/* Unified Resource Calendar Table */}
      <div className="overflow-x-auto rounded-md border border-border bg-surface">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-border bg-surface-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              <th className="px-3 py-2.5">Resource ID & Name</th>
              <th className="px-3 py-2.5">Type</th>
              <th className="px-3 py-2.5">Department</th>
              <th className="px-3 py-2.5">Operational Assignment</th>
              <th className="px-3 py-2.5">Date & Window</th>
              <th className="px-3 py-2.5">Availability</th>
              <th className="px-3 py-2.5 text-right">Utilization</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/60">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-muted-foreground">
                  No resource calendar entries found matching the filter.
                </td>
              </tr>
            ) : (
              filtered.map((item, idx) => (
                <tr key={`${item.id}-${idx}`} className="hover:bg-surface-2/30 transition-colors">
                  <td className="px-3 py-2.5 font-medium text-foreground">
                    <div className="flex items-center gap-2">
                      {item.type === "Machine" ? (
                        <Wrench className="size-3.5 text-primary shrink-0" aria-hidden />
                      ) : (
                        <Users className="size-3.5 text-info shrink-0" aria-hidden />
                      )}
                      <div>
                        <div className="font-mono font-semibold text-xs text-foreground">{item.id}</div>
                        <div className="text-[11px] text-muted-foreground">{item.typeName}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-3 py-2.5">
                    <Badge variant="outline" className="text-[10px] font-mono uppercase">
                      {item.type}
                    </Badge>
                  </td>
                  <td className="px-3 py-2.5">
                    <DepartmentBadge department={item.department as any} />
                  </td>
                  <td className="px-3 py-2.5 font-mono text-xs">
                    <div className="font-medium text-foreground">{item.assignment}</div>
                    {item.blockId && item.blockId !== "—" && (
                      <div className="text-[10px] text-primary">Block Ref: {item.blockId}</div>
                    )}
                  </td>
                  <td className="px-3 py-2.5 text-[11px] text-muted-foreground">
                    <div className="flex items-center gap-1 font-mono text-foreground">
                      <Calendar className="size-3 text-muted-foreground" aria-hidden />
                      {item.date}
                    </div>
                    <div className="flex items-center gap-1 font-mono text-[10px] text-muted-foreground mt-0.5">
                      <Clock className="size-3 text-muted-foreground" aria-hidden />
                      {item.timeWindow}
                    </div>
                  </td>
                  <td className="px-3 py-2.5">
                    <AvailabilityBadge status={item.availability as any} />
                  </td>
                  <td className="px-3 py-2.5 text-right font-mono">
                    <div className="flex items-center justify-end gap-2">
                      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-surface-2">
                        <div
                          className="h-full bg-primary rounded-full"
                          style={{ width: `${Math.min(100, Math.max(0, item.utilization))}%` }}
                        />
                      </div>
                      <span className="text-xs font-semibold">{item.utilization}%</span>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between border-t border-border px-1 py-1.5 text-[11px] text-muted-foreground">
        <span>Backend-synchronized resource allocation timetable · Data provenance: DERIVED</span>
        <span className="font-mono">Live operational sync</span>
      </div>
    </div>
  );
}
