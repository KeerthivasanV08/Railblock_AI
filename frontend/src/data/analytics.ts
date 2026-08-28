import type {
  AnalyticsKPI,
  BeforeAfterMetric,
  Department,
  DepartmentWorkload,
  MaintenanceTask,
  ReportDefinition,
  TrendPoint,
} from "@/types";
import { mulberry32, intBetween } from "@/lib/random";

/** Deterministic 12-week trend series (AI Simulation / synthetic history). */
function trend(seedValue: number, base: number, spread: number, weeks = 12): TrendPoint[] {
  const rand = mulberry32(seedValue);
  const points: TrendPoint[] = [];
  let v = base;
  for (let i = 0; i < weeks; i++) {
    v = Math.max(0, Math.min(100, v + (rand() - 0.42) * spread));
    points.push({ label: `Wk ${i + 1}`, value: Math.round(v) });
  }
  return points;
}

export function blockUtilizationTrend(): TrendPoint[] {
  return trend(101, 68, 9);
}

export function maintenanceCompletionTrend(): TrendPoint[] {
  return trend(202, 61, 8);
}

export function deferredTasksTrend(): TrendPoint[] {
  const rand = mulberry32(303);
  return Array.from({ length: 12 }, (_, i) => ({
    label: `Wk ${i + 1}`,
    value: intBetween(rand, 40, 260),
  }));
}

export function trainDelayImpactTrend(): TrendPoint[] {
  const rand = mulberry32(404);
  return Array.from({ length: 12 }, (_, i) => ({
    label: `Wk ${i + 1}`,
    value: intBetween(rand, 3, 22),
    secondary: intBetween(rand, 1, 9),
  }));
}

export function integratedBlockPctTrend(): TrendPoint[] {
  return trend(505, 34, 7);
}

export function aiAcceptanceTrend(): TrendPoint[] {
  return trend(606, 72, 6);
}

export function departmentWorkload(tasks: MaintenanceTask[]): DepartmentWorkload[] {
  const depts: Department[] = ["Engineering", "TRD", "S&T"];
  return depts.map((department) => {
    const deptTasks = tasks.filter((t) => t.department === department);
    return {
      department,
      open: deptTasks.filter((t) => t.status === "Pending" || t.status === "Scheduled").length,
      completed: deptTasks.filter((t) => t.status === "Completed").length,
      overdue: deptTasks.filter((t) => t.overdue_days > 0 && t.status !== "Completed").length,
    };
  });
}

export function analyticsKPIs(tasks: MaintenanceTask[]): AnalyticsKPI[] {
  const completed = tasks.filter((t) => t.status === "Completed").length;
  const overdue = tasks.filter((t) => t.overdue_days > 0 && t.status !== "Completed").length;
  const deferred = tasks.filter((t) => t.status === "Deferred").length;
  return [
    { label: "Asset Availability", value: 94, unit: "%", trend: 1.2, status: "ok" },
    {
      label: "Maintenance Completion",
      value: Math.round((completed / tasks.length) * 100),
      unit: "%",
      trend: 2.4,
      status: "ok",
    },
    { label: "Block Utilization", value: 78, unit: "%", trend: 3.1, status: "ok" },
    { label: "Block Wastage", value: 9, unit: "%", trend: -1.6, status: "ok" },
    { label: "Integrated Block %", value: 34, unit: "%", trend: 5.0, status: "ok" },
    { label: "Avg Unused Block Time", value: 14, unit: "min", trend: -3.0, status: "ok" },
    {
      label: "Deferred Tasks",
      value: deferred,
      unit: "count",
      trend: -6.2,
      status: deferred > 500 ? "warn" : "ok",
    },
    { label: "Overdue Tasks", value: overdue, unit: "count", trend: -2.1, status: "warn" },
    { label: "Train Impact", value: 6, unit: "%", trend: -1.1, status: "ok" },
    { label: "Planning Accuracy", value: 91, unit: "%", trend: 1.8, status: "ok" },
  ];
}

export function beforeAfterComparison(): BeforeAfterMetric[] {
  return [
    { label: "Block Utilization", before: 58, after: 78, unit: "%", betterWhenLower: false },
    { label: "Integrated Blocks", before: 11, after: 34, unit: "%", betterWhenLower: false },
    { label: "Unused Block Time", before: 41, after: 14, unit: "min", betterWhenLower: true },
    { label: "Deferred Tasks", before: 940, after: 512, unit: "count", betterWhenLower: true },
    { label: "Train Impact", before: 17, after: 6, unit: "%", betterWhenLower: true },
    { label: "Planning Time", before: 210, after: 46, unit: "min", betterWhenLower: true },
  ];
}

export function generateReports(): ReportDefinition[] {
  return [
    {
      id: "RPT-WBP",
      title: "Weekly Block Plan — SEC-NDLS-CNB",
      category: "Weekly Block Plan",
      description:
        "All planned and approved blocks for the current planning week across the corridor.",
      generated_at: "2026-08-26 06:00",
      rows: 34,
    },
    {
      id: "RPT-MRP",
      title: "Monthly Rolling Plan — August 2026",
      category: "Monthly Rolling Plan",
      description: "26-week rolling maintenance and traffic block outlook for the division.",
      generated_at: "2026-08-01 06:00",
      rows: 182,
    },
    {
      id: "RPT-MSUM",
      title: "Maintenance Summary — Engineering / TRD / S&T",
      category: "Maintenance Summary",
      description: "Task completion, overdue, and deferral summary by department and severity.",
      generated_at: "2026-08-26 07:00",
      rows: 25000,
    },
    {
      id: "RPT-RUTIL",
      title: "Resource Utilization Report",
      category: "Resource Utilization",
      description: "Machine and crew utilization, availability and assignment history.",
      generated_at: "2026-08-26 07:10",
      rows: 84,
    },
    {
      id: "RPT-DSUM",
      title: "Disruption Summary",
      category: "Disruption Summary",
      description: "Detected disruptions, applied reschedules and residual train impact.",
      generated_at: "2026-08-26 09:30",
      rows: 3,
    },
    {
      id: "RPT-AISUM",
      title: "AI Recommendation Summary",
      category: "AI Recommendation Summary",
      description:
        "AI-generated block recommendations, acceptance rate and confidence distribution.",
      generated_at: "2026-08-26 08:15",
      rows: 3,
    },
    {
      id: "RPT-AUDIT",
      title: "Audit Report",
      category: "Audit Report",
      description: "Full audit trail of approvals, rejections, modifications and system actions.",
      generated_at: "2026-08-26 10:00",
      rows: 3,
    },
  ];
}
