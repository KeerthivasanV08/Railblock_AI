import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { PageHeader } from "@/components/common/PageHeader";
import { useTaskStore } from "@/stores/taskStore";
import {
  aiAcceptanceTrend,
  analyticsKPIs,
  beforeAfterComparison,
  blockUtilizationTrend,
  deferredTasksTrend,
  departmentWorkload,
  integratedBlockPctTrend,
  maintenanceCompletionTrend,
  trainDelayImpactTrend,
} from "@/data/analytics";
import { analyticsApi } from "@/api";

const CHART_HEIGHT = 200;

interface LiveKPI {
  label: string;
  value: string | number;
  unit?: string;
  trend: number;
}

export function AnalyticsPage() {
  const tasks = useTaskStore((s) => s.tasks);
  const kpis = analyticsKPIs(tasks);
  const workload = departmentWorkload(tasks);
  const beforeAfter = beforeAfterComparison();
  const [liveKPIs, setLiveKPIs] = useState<LiveKPI[]>([]);

  useEffect(() => {
    analyticsApi
      .getOverviewKPIs()
      .then((res: Record<string, unknown>) => {
        if (res && typeof res === "object") {
          const mapped: LiveKPI[] = [];
          if (typeof res.total_tasks === "number")
            mapped.push({ label: "Total Tasks", value: res.total_tasks, trend: 0 });
          if (typeof res.pending_tasks === "number")
            mapped.push({ label: "Pending Tasks", value: res.pending_tasks, trend: -2 });
          if (typeof res.total_blocks === "number")
            mapped.push({ label: "Total Blocks", value: res.total_blocks, trend: 5 });
          if (typeof res.disruptions_open === "number")
            mapped.push({ label: "Open Disruptions", value: res.disruptions_open, trend: -10 });
          if (mapped.length > 0) setLiveKPIs(mapped);
        }
      })
      .catch(() => {});
  }, []);

  const displayKPIs = liveKPIs.length > 0 ? liveKPIs : kpis;

  return (
    <div className="h-full overflow-auto">
      <PageHeader
        title="Analytics & Operational Intelligence"
        description="Real-time operational KPIs from backend pipeline — OR-Tools optimization, MDPS scoring, and constraint-validated blocks"
        crumbs={[{ label: "Intelligence" }, { label: "Analytics" }]}
      />
      <div className="space-y-4 p-4">
        <div className="grid grid-cols-2 gap-2.5 md:grid-cols-5">
          {displayKPIs.map((k) => (
            <div key={k.label} className="rounded-md border border-border bg-surface px-3 py-2.5">
              <p className="text-[10px] uppercase tracking-wide text-muted-foreground">{k.label}</p>
              <p className="mt-0.5 font-mono text-lg font-semibold text-foreground">
                {k.value}
                {k.unit === "%" ? "%" : k.unit === "min" ? " min" : ""}
              </p>
              <p className={`text-[10px] ${k.trend >= 0 ? "text-ok" : "text-crit"}`}>
                {k.trend >= 0 ? "+" : ""}
                {k.trend}% vs last period
              </p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          <ChartCard title="Block Utilization Trend">
            <LineChart data={blockUtilizationTrend()}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 10 }}
                stroke="var(--color-muted-foreground)"
              />
              <YAxis tick={{ fontSize: 10 }} stroke="var(--color-muted-foreground)" />
              <Tooltip
                contentStyle={{
                  background: "var(--color-surface)",
                  border: "1px solid var(--color-border)",
                  fontSize: 12,
                }}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="var(--color-info)"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ChartCard>

          <ChartCard title="Maintenance Completion Trend">
            <LineChart data={maintenanceCompletionTrend()}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 10 }}
                stroke="var(--color-muted-foreground)"
              />
              <YAxis tick={{ fontSize: 10 }} stroke="var(--color-muted-foreground)" />
              <Tooltip
                contentStyle={{
                  background: "var(--color-surface)",
                  border: "1px solid var(--color-border)",
                  fontSize: 12,
                }}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="var(--color-ok)"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ChartCard>

          <ChartCard title="Deferred Tasks Trend">
            <BarChart data={deferredTasksTrend()}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 10 }}
                stroke="var(--color-muted-foreground)"
              />
              <YAxis tick={{ fontSize: 10 }} stroke="var(--color-muted-foreground)" />
              <Tooltip
                contentStyle={{
                  background: "var(--color-surface)",
                  border: "1px solid var(--color-border)",
                  fontSize: 12,
                }}
              />
              <Bar dataKey="value" fill="var(--color-warn)" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ChartCard>

          <ChartCard title="Department Workload">
            <BarChart data={workload}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis
                dataKey="department"
                tick={{ fontSize: 10 }}
                stroke="var(--color-muted-foreground)"
              />
              <YAxis tick={{ fontSize: 10 }} stroke="var(--color-muted-foreground)" />
              <Tooltip
                contentStyle={{
                  background: "var(--color-surface)",
                  border: "1px solid var(--color-border)",
                  fontSize: 12,
                }}
              />
              <Bar dataKey="open" name="Open" stackId="s" fill="var(--color-info)" />
              <Bar dataKey="overdue" name="Overdue" stackId="s" fill="var(--color-crit)" />
              <Bar
                dataKey="completed"
                name="Completed"
                stackId="s"
                fill="var(--color-ok)"
                radius={[3, 3, 0, 0]}
              />
            </BarChart>
          </ChartCard>

          <ChartCard title="Train Delay Impact (min)">
            <LineChart data={trainDelayImpactTrend()}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 10 }}
                stroke="var(--color-muted-foreground)"
              />
              <YAxis tick={{ fontSize: 10 }} stroke="var(--color-muted-foreground)" />
              <Tooltip
                contentStyle={{
                  background: "var(--color-surface)",
                  border: "1px solid var(--color-border)",
                  fontSize: 12,
                }}
              />
              <Line
                type="monotone"
                dataKey="value"
                name="Avg delay"
                stroke="var(--color-crit)"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ChartCard>

          <ChartCard title="Integrated Block % Trend">
            <LineChart data={integratedBlockPctTrend()}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 10 }}
                stroke="var(--color-muted-foreground)"
              />
              <YAxis tick={{ fontSize: 10 }} stroke="var(--color-muted-foreground)" />
              <Tooltip
                contentStyle={{
                  background: "var(--color-surface)",
                  border: "1px solid var(--color-border)",
                  fontSize: 12,
                }}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="var(--color-ai)"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ChartCard>

          <ChartCard title="AI Recommendation Acceptance %">
            <LineChart data={aiAcceptanceTrend()}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 10 }}
                stroke="var(--color-muted-foreground)"
              />
              <YAxis tick={{ fontSize: 10 }} stroke="var(--color-muted-foreground)" />
              <Tooltip
                contentStyle={{
                  background: "var(--color-surface)",
                  border: "1px solid var(--color-border)",
                  fontSize: 12,
                }}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="var(--color-ai)"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ChartCard>
        </div>

        <div className="rounded-md border border-border bg-surface p-4">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-sm font-semibold text-foreground">
              Traditional Planning vs RailBlock AI Simulation
            </p>
            <span className="rounded border border-ai/30 bg-ai/10 px-1.5 py-0.5 text-[10px] text-ai">
              Simulation / Synthetic Data
            </span>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-[11px] uppercase tracking-wide text-muted-foreground">
                <th className="py-1.5 font-medium">Metric</th>
                <th className="py-1.5 text-right font-medium">Traditional Planning</th>
                <th className="py-1.5 text-right font-medium text-ai">RailBlock AI</th>
                <th className="py-1.5 text-right font-medium">Change</th>
              </tr>
            </thead>
            <tbody>
              {beforeAfter.map((m) => {
                const better = m.betterWhenLower ? m.after < m.before : m.after > m.before;
                const delta = m.after - m.before;
                return (
                  <tr key={m.label} className="border-b border-border/60 last:border-0">
                    <td className="py-1.5">{m.label}</td>
                    <td className="py-1.5 text-right font-mono tabular-nums text-muted-foreground">
                      {m.before}
                      {m.unit === "%" ? "%" : m.unit === "min" ? " min" : ""}
                    </td>
                    <td className="py-1.5 text-right font-mono tabular-nums font-semibold text-foreground">
                      {m.after}
                      {m.unit === "%" ? "%" : m.unit === "min" ? " min" : ""}
                    </td>
                    <td
                      className={`py-1.5 text-right font-mono text-xs ${better ? "text-ok" : "text-crit"}`}
                    >
                      {delta >= 0 ? "+" : ""}
                      {delta}
                      {m.unit === "%" ? "%" : m.unit === "min" ? " min" : ""}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactElement }) {
  return (
    <div className="rounded-md border border-border bg-surface p-3">
      <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </p>
      <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
        {children}
      </ResponsiveContainer>
    </div>
  );
}
