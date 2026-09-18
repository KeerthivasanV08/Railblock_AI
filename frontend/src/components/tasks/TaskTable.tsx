import { useMemo, useState, useCallback } from "react";
import { useNavigate } from "@tanstack/react-router";
import { ChevronLeft, ChevronRight, Download, ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { SeverityBadge, DepartmentBadge, PriorityBadge } from "@/components/common/DomainBadges";
import { TaskStatusBadge } from "@/components/common/StatusBadge";
import { EmptyState } from "@/components/common/States";
import { downloadCSV } from "@/services/export/csvExportService";
import { filterTasks, useTaskStore } from "@/stores/taskStore";
import type { MaintenanceTask } from "@/types";

type SortField = "priority_score" | "overdue_days" | "previous_deferrals";
type SortDir = "desc" | "asc";

function SortIcon({ field, active, dir }: { field: string; active: string; dir: SortDir }) {
  if (active !== field) return <ArrowUpDown className="ml-1 inline size-3 opacity-40" aria-hidden />;
  return dir === "desc"
    ? <ArrowDown className="ml-1 inline size-3 text-primary" aria-hidden />
    : <ArrowUp className="ml-1 inline size-3 text-primary" aria-hidden />;
}

export function TaskTable() {
  const { tasks, filters, page, pageSize, setPage } = useTaskStore();
  const navigate = useNavigate();

  // Numeric sort state — default: highest priority first
  const [sortField, setSortField] = useState<SortField>("priority_score");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const toggleSort = useCallback(
    (field: SortField) => {
      if (sortField === field) {
        setSortDir((d) => (d === "desc" ? "asc" : "desc"));
      } else {
        setSortField(field);
        setSortDir("desc");
      }
      setPage(1);
    },
    [sortField, setPage],
  );

  const filtered = useMemo(() => {
    const base = filterTasks(tasks, filters);
    // Always sort numerically — never lexicographically
    return base.sort((a: MaintenanceTask, b: MaintenanceTask) => {
      const va = Number(a[sortField] ?? 0);
      const vb = Number(b[sortField] ?? 0);
      return sortDir === "desc" ? vb - va : va - vb;
    });
  }, [tasks, filters, sortField, sortDir]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const clampedPage = Math.min(page, totalPages);
  const pageRows = filtered.slice((clampedPage - 1) * pageSize, clampedPage * pageSize);

  const exportCSV = () => {
    downloadCSV(
      "railblock-maintenance-tasks.csv",
      filtered.map((t) => ({
        task_id: t.task_id,
        department: t.department,
        asset: t.asset,
        location: t.location_label,
        defect: t.defect,
        severity: t.severity,
        overdue_days: t.overdue_days,
        priority_score: t.priority_score,
        previous_deferrals: t.previous_deferrals,
        required_duration_min: t.required_duration_min,
        required_resource: t.required_resource,
        status: t.status,
        recommended_block: t.recommended_block_id ?? "",
      })),
    );
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-border px-3 py-2">
        <p className="text-xs text-muted-foreground">
          {filtered.length.toLocaleString()} of {tasks.length.toLocaleString()} tasks match current
          filters
        </p>
        <Button variant="outline" size="sm" className="gap-1.5" onClick={exportCSV}>
          <Download className="size-3.5" aria-hidden /> Export CSV
        </Button>
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          title="No maintenance tasks match your filters"
          description="Adjust or clear filters to see more results."
          className="m-4"
        />
      ) : (
        <div className="flex-1 overflow-auto">
          <Table>
            <TableHeader className="sticky top-0 z-10 bg-surface">
              <TableRow>
                <TableHead>Task ID</TableHead>
                <TableHead>Dept</TableHead>
                <TableHead>Asset</TableHead>
                <TableHead>Location</TableHead>
                <TableHead>Defect</TableHead>
                <TableHead>Sev</TableHead>
                <TableHead
                  className="cursor-pointer text-right select-none"
                  onClick={() => toggleSort("overdue_days")}
                  title="Sort by overdue days"
                >
                  Overdue
                  <SortIcon field="overdue_days" active={sortField} dir={sortDir} />
                </TableHead>
                {/* Priority column — numeric sort (never lexicographic) */}
                <TableHead
                  className="cursor-pointer text-right select-none"
                  onClick={() => toggleSort("priority_score")}
                  title="Sort by MDPS priority score (numeric)"
                >
                  Priority
                  <SortIcon field="priority_score" active={sortField} dir={sortDir} />
                </TableHead>
                <TableHead
                  className="cursor-pointer text-right select-none"
                  onClick={() => toggleSort("previous_deferrals")}
                  title="Sort by deferrals"
                >
                  Deferrals
                  <SortIcon field="previous_deferrals" active={sortField} dir={sortDir} />
                </TableHead>
                <TableHead className="text-right">Duration</TableHead>
                <TableHead>Resource</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Rec. Block</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {pageRows.map((t) => (
                <TableRow
                  key={t.task_id}
                  className="cursor-pointer"
                  onClick={() => navigate({ to: "/tasks/$taskId", params: { taskId: t.task_id } })}
                >
                  <TableCell className="font-mono text-xs">{t.task_id}</TableCell>
                  <TableCell>
                    <DepartmentBadge department={t.department} />
                  </TableCell>
                  <TableCell className="text-xs">{t.asset}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {t.location_label}
                  </TableCell>
                  <TableCell className="text-xs">{t.defect}</TableCell>
                  <TableCell>
                    <SeverityBadge severity={t.severity} />
                  </TableCell>
                  <TableCell className="text-right font-mono text-xs">
                    {t.overdue_days > 0 ? `${t.overdue_days}d` : "—"}
                  </TableCell>
                  <TableCell className="text-right">
                    {/* priority_score is always a number from adaptBackendTask — no fallback to 99 */}
                    <PriorityBadge score={t.priority_score} />
                  </TableCell>
                  <TableCell className="text-right font-mono text-xs">
                    {t.previous_deferrals}
                  </TableCell>
                  <TableCell className="text-right font-mono text-xs">
                    {t.required_duration_min}m
                  </TableCell>
                  <TableCell className="text-xs">{t.required_resource}</TableCell>
                  <TableCell>
                    <TaskStatusBadge status={t.status} />
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    {t.recommended_block_id ?? "—"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <div className="flex items-center justify-between border-t border-border px-3 py-2 text-xs text-muted-foreground">
        <span>
          Page {clampedPage} of {totalPages}
        </span>
        <div className="flex items-center gap-1">
          <Button
            variant="outline"
            size="icon"
            className="size-7"
            disabled={clampedPage <= 1}
            onClick={() => setPage(clampedPage - 1)}
          >
            <ChevronLeft className="size-3.5" aria-hidden />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="size-7"
            disabled={clampedPage >= totalPages}
            onClick={() => setPage(clampedPage + 1)}
          >
            <ChevronRight className="size-3.5" aria-hidden />
          </Button>
        </div>
      </div>
    </div>
  );
}
