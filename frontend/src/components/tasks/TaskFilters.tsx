import { Search, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import type { Department, Severity, TaskStatus } from "@/types";
import { emptyFilters, useTaskStore } from "@/stores/taskStore";

const DEPARTMENTS: Department[] = ["Engineering", "TRD", "S&T"];
const SEVERITIES: Severity[] = ["A", "B", "C"];
const STATUSES: TaskStatus[] = ["Pending", "Scheduled", "In Progress", "Completed", "Deferred"];

export function TaskFilters() {
  const { filters, setFilters, resetFilters } = useTaskStore();

  const toggle = <T,>(arr: T[], value: T): T[] =>
    arr.includes(value) ? arr.filter((v) => v !== value) : [...arr, value];

  const dirty = JSON.stringify(filters) !== JSON.stringify(emptyFilters);

  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto p-3 text-xs">
      <div>
        <label className="mb-1 block text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
          Search
        </label>
        <div className="relative">
          <Search
            className="absolute left-2 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground"
            aria-hidden
          />
          <Input
            value={filters.search}
            onChange={(e) => setFilters({ search: e.target.value })}
            placeholder="Task ID, asset, section, defect…"
            className="h-8 pl-7 text-xs"
          />
        </div>
      </div>

      <FilterGroup label="Department">
        {DEPARTMENTS.map((d) => (
          <CheckRow
            key={d}
            label={d}
            checked={filters.departments.includes(d)}
            onChange={() => setFilters({ departments: toggle(filters.departments, d) })}
          />
        ))}
      </FilterGroup>

      <FilterGroup label="Severity">
        {SEVERITIES.map((s) => (
          <CheckRow
            key={s}
            label={`Severity ${s}`}
            checked={filters.severities.includes(s)}
            onChange={() => setFilters({ severities: toggle(filters.severities, s) })}
          />
        ))}
      </FilterGroup>

      <FilterGroup label="Status">
        {STATUSES.map((s) => (
          <CheckRow
            key={s}
            label={s}
            checked={filters.statuses.includes(s)}
            onChange={() => setFilters({ statuses: toggle(filters.statuses, s) })}
          />
        ))}
      </FilterGroup>

      <div>
        <div className="mb-1.5 flex items-center justify-between">
          <span className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            Min priority
          </span>
          <span className="font-mono text-[11px] text-foreground">{filters.minPriority}</span>
        </div>
        <Slider
          value={[filters.minPriority]}
          max={100}
          step={5}
          onValueChange={([v]) => setFilters({ minPriority: v })}
        />
      </div>

      <div className="flex items-center justify-between">
        <span className="text-[11px] font-medium text-foreground">Overdue only</span>
        <Switch
          checked={filters.overdueOnly}
          onCheckedChange={(v) => setFilters({ overdueOnly: v })}
        />
      </div>
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-medium text-foreground">Recommended only</span>
        <Switch
          checked={filters.recommendedOnly}
          onCheckedChange={(v) => setFilters({ recommendedOnly: v })}
        />
      </div>

      {dirty && (
        <Button variant="outline" size="sm" className="mt-auto gap-1.5" onClick={resetFilters}>
          <X className="size-3.5" aria-hidden /> Clear filters
        </Button>
      )}
    </div>
  );
}

function FilterGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <div className="space-y-1">{children}</div>
    </div>
  );
}

function CheckRow({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: () => void;
}) {
  return (
    <label className="flex items-center gap-2 text-[11px] text-foreground">
      <Checkbox checked={checked} onCheckedChange={onChange} />
      {label}
    </label>
  );
}
