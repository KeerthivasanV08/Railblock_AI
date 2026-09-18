import { useEffect } from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { TaskFilters } from "./TaskFilters";
import { TaskTable } from "./TaskTable";
import { useTaskStore } from "@/stores/taskStore";

export function TasksPage() {
  const { loadFromBackend, dataSource, loading } = useTaskStore();

  // Load real backend data on mount; gracefully falls back to synthetic if unreachable
  useEffect(() => {
    loadFromBackend();
  }, [loadFromBackend]);

  const description =
    dataSource === "DERIVED"
      ? "Unified maintenance task management across TMS, SMMS and TDMS — live MDPS-scored data"
      : loading
        ? "Loading tasks from backend…"
        : "Unified maintenance task management across TMS, SMMS and TDMS — synthetic fallback data";

  return (
    <div className="flex h-full flex-col">
      <PageHeader
        title="Maintenance Task Matrix"
        description={description}
        crumbs={[{ label: "Planning" }, { label: "Maintenance Tasks" }]}
      />
      <div className="flex flex-1 overflow-hidden">
        <aside className="hidden w-[240px] shrink-0 overflow-hidden border-r border-border md:block">
          <TaskFilters />
        </aside>
        <div className="min-w-0 flex-1 overflow-hidden">
          <TaskTable />
        </div>
      </div>
    </div>
  );
}
