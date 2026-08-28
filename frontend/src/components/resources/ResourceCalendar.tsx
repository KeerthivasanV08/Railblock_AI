import { useMemo } from "react";
import type { Crew, Machine } from "@/types";
import { mulberry32, seedFromString } from "@/lib/random";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"];

function bars(id: string) {
  const rand = mulberry32(seedFromString(id));
  return DAYS.map(() => rand() > 0.45);
}

export function ResourceCalendar({ machines, crews }: { machines: Machine[]; crews: Crew[] }) {
  const rows = useMemo(
    () => [
      ...machines.map((m) => ({
        id: m.resource_id,
        label: `${m.resource_id} · ${m.type}`,
        bars: bars(m.resource_id),
      })),
      ...crews.map((c) => ({
        id: c.crew_id,
        label: `${c.crew_id} · ${c.department}`,
        bars: bars(c.crew_id),
      })),
    ],
    [machines, crews],
  );

  return (
    <div className="overflow-x-auto rounded-md border border-border">
      <div className="min-w-[560px]">
        <div className="flex border-b border-border bg-surface-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
          <div className="w-[220px] shrink-0 px-2 py-1.5">Resource</div>
          {DAYS.map((d) => (
            <div key={d} className="flex-1 px-2 py-1.5 text-center">
              {d}
            </div>
          ))}
        </div>
        {rows.map((r) => (
          <div key={r.id} className="flex items-center border-b border-border/70 last:border-0">
            <div className="w-[220px] shrink-0 px-2 py-2 font-mono text-[11px] text-foreground">
              {r.label}
            </div>
            {r.bars.map((assigned, i) => (
              <div key={i} className="flex-1 px-2 py-2">
                <div
                  className={`h-2.5 rounded-full ${assigned ? "bg-info" : "bg-muted"}`}
                  title={assigned ? "Assigned" : "Available"}
                />
              </div>
            ))}
          </div>
        ))}
      </div>
      <div className="flex items-center gap-3 border-t border-border px-3 py-1.5 text-[10px] text-muted-foreground">
        <span className="inline-flex items-center gap-1">
          <span className="size-2 rounded-full bg-info" /> Assigned
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="size-2 rounded-full bg-muted" /> Available
        </span>
      </div>
    </div>
  );
}
