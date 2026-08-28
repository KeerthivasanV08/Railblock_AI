import { PageHeader } from "@/components/common/PageHeader";
import { TaskFilters } from "./TaskFilters";
import { TaskTable } from "./TaskTable";

export function TasksPage() {
  return (
    <div className="flex h-full flex-col">
      <PageHeader
        title="Maintenance Task Matrix"
        description="Unified maintenance task management across TMS, SMMS and TDMS — 25,000 synthetic records"
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
