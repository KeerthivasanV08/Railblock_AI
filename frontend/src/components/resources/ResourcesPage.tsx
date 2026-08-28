import { PageHeader } from "@/components/common/PageHeader";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DepartmentBadge } from "@/components/common/DomainBadges";
import { AvailabilityBadge } from "@/components/common/StatusBadge";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import { CorridorMap } from "@/components/map/CorridorMap";
import { useResourceStore } from "@/stores/resourceStore";
import { downloadCSV } from "@/services/export/csvExportService";
import { ResourceCalendar } from "./ResourceCalendar";

export function ResourcesPage() {
  const { machines, crews } = useResourceStore();

  const exportCSV = () => {
    downloadCSV("railblock-resource-availability.csv", [
      ...machines.map((m) => ({
        id: m.resource_id,
        kind: "Machine",
        type: m.type,
        department: m.department,
        depot: m.home_depot,
        location: m.current_location,
        availability: m.availability,
        last_updated: m.last_updated,
      })),
      ...crews.map((c) => ({
        id: c.crew_id,
        kind: "Crew",
        type: c.shift,
        department: c.department,
        depot: c.depot,
        location: `Km ${c.km}`,
        availability: c.availability,
        last_updated: "—",
      })),
    ]);
  };

  return (
    <div className="flex h-full flex-col overflow-auto">
      <PageHeader
        title="Resource Availability"
        description="Machine and crew availability across the corridor — Synthetic Demo Data"
        crumbs={[{ label: "Planning" }, { label: "Resources" }]}
        actions={
          <Button variant="outline" size="sm" className="gap-1.5" onClick={exportCSV}>
            <Download className="size-3.5" aria-hidden /> Export CSV
          </Button>
        }
      />
      <div className="space-y-4 p-4">
        <CorridorMap machines={machines} heightClass="h-[220px]" />

        <Tabs defaultValue="machines">
          <TabsList>
            <TabsTrigger value="machines">Machines ({machines.length})</TabsTrigger>
            <TabsTrigger value="crews">Crew ({crews.length})</TabsTrigger>
            <TabsTrigger value="calendar">Resource Calendar</TabsTrigger>
          </TabsList>

          <TabsContent value="machines" className="rounded-md border border-border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Resource ID</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Home Depot</TableHead>
                  <TableHead>Current Location</TableHead>
                  <TableHead>Availability</TableHead>
                  <TableHead>Last Updated</TableHead>
                  <TableHead>Assigned Task</TableHead>
                  <TableHead className="text-right">Utilization</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {machines.map((m) => (
                  <TableRow key={m.resource_id}>
                    <TableCell className="font-mono text-xs">{m.resource_id}</TableCell>
                    <TableCell className="text-xs">{m.type}</TableCell>
                    <TableCell className="text-xs">{m.home_depot}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {m.current_location}
                    </TableCell>
                    <TableCell>
                      <AvailabilityBadge status={m.availability} />
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {m.last_updated}
                    </TableCell>
                    <TableCell className="font-mono text-xs">{m.assigned_task_id ?? "—"}</TableCell>
                    <TableCell className="text-right font-mono text-xs">{m.utilization}%</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TabsContent>

          <TabsContent value="crews" className="rounded-md border border-border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Crew ID</TableHead>
                  <TableHead>Department</TableHead>
                  <TableHead>Depot</TableHead>
                  <TableHead>Shift</TableHead>
                  <TableHead className="text-right">Headcount</TableHead>
                  <TableHead>Availability</TableHead>
                  <TableHead>Assigned Block</TableHead>
                  <TableHead className="text-right">Utilization</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {crews.map((c) => (
                  <TableRow key={c.crew_id}>
                    <TableCell className="font-mono text-xs">{c.crew_id}</TableCell>
                    <TableCell>
                      <DepartmentBadge department={c.department} />
                    </TableCell>
                    <TableCell className="text-xs">{c.depot}</TableCell>
                    <TableCell className="text-xs">{c.shift}</TableCell>
                    <TableCell className="text-right font-mono text-xs">{c.headcount}</TableCell>
                    <TableCell>
                      <AvailabilityBadge status={c.availability} />
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {c.assigned_block_id ?? "—"}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs">{c.utilization}%</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TabsContent>

          <TabsContent value="calendar">
            <ResourceCalendar machines={machines} crews={crews} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
