import { useState } from "react";
import { Download, Printer } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { generateReports } from "@/data/analytics";
import { downloadCSV } from "@/services/export/csvExportService";
import { useNotificationStore } from "@/stores/notificationStore";

const CATEGORIES = [
  "All",
  "Weekly Block Plan",
  "Monthly Rolling Plan",
  "Maintenance Summary",
  "Resource Utilization",
  "Disruption Summary",
  "AI Recommendation Summary",
  "Audit Report",
] as const;

export function ReportsPage() {
  const [category, setCategory] = useState<(typeof CATEGORIES)[number]>("All");
  const reports = generateReports().filter((r) => category === "All" || r.category === category);
  const audit = useNotificationStore((s) => s.audit);

  const exportReport = (id: string, title: string) => {
    if (id === "RPT-AUDIT") {
      downloadCSV(
        `${id}.csv`,
        audit.map((a) => ({
          at: a.at,
          role: a.role,
          action: a.action,
          entity: a.entity,
          result: a.result,
          detail: a.detail ?? "",
        })),
      );
      return;
    }
    downloadCSV(`${id}.csv`, [
      { report: title, note: "Synthetic demo export — full dataset generated client-side." },
    ]);
  };

  return (
    <div className="h-full overflow-auto">
      <PageHeader
        title="Reports"
        description="Operational reports for governance and audit — Synthetic Demo Data"
        crumbs={[{ label: "Governance" }, { label: "Reports" }]}
        actions={
          <Select value={category} onValueChange={(v) => setCategory(v as typeof category)}>
            <SelectTrigger className="h-8 w-[220px] text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {CATEGORIES.map((c) => (
                <SelectItem key={c} value={c} className="text-xs">
                  {c}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        }
      />
      <div className="grid grid-cols-1 gap-3 p-4 md:grid-cols-2">
        {reports.map((r) => (
          <div key={r.id} className="rounded-md border border-border bg-surface p-4">
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="text-[10px] uppercase tracking-wide text-muted-foreground">
                  {r.category}
                </p>
                <p className="mt-0.5 text-sm font-semibold text-foreground">{r.title}</p>
              </div>
              <span className="shrink-0 font-mono text-[11px] text-muted-foreground">{r.id}</span>
            </div>
            <p className="mt-1.5 text-xs text-muted-foreground">{r.description}</p>
            <div className="mt-2 flex items-center justify-between text-[11px] text-muted-foreground">
              <span>Generated {r.generated_at}</span>
              <span>{r.rows.toLocaleString()} rows</span>
            </div>
            <div className="mt-3 flex gap-1.5">
              <Button
                size="sm"
                variant="outline"
                className="gap-1.5"
                onClick={() => exportReport(r.id, r.title)}
              >
                <Download className="size-3.5" aria-hidden /> Export CSV
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="gap-1.5"
                onClick={() => window.print()}
              >
                <Printer className="size-3.5" aria-hidden /> Print View
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
