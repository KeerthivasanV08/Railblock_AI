import type { MaintenanceTask, PriorityBreakdown, Severity } from "@/types";

const SEVERITY_WEIGHT: Record<Severity, number> = { A: 40, B: 26, C: 13 };

export interface PriorityInput {
  severity: Severity;
  overdue_days: number;
  traffic_density: number;
  asset_criticality: number;
  previous_deferrals: number;
}

/**
 * Deterministic, explainable priority model (AI Simulation).
 * priority = severity + overdue risk + traffic impact + asset criticality + deferral risk
 */
export function calculatePriority(input: PriorityInput): {
  score: number;
  breakdown: PriorityBreakdown;
} {
  const severity = SEVERITY_WEIGHT[input.severity];
  const overdue_risk = Math.round(Math.min(30, Math.sqrt(Math.max(0, input.overdue_days)) * 7.2));
  const traffic_impact = Math.round((input.traffic_density / 100) * 16);
  const asset_criticality = Math.round((input.asset_criticality / 100) * 10);
  const deferral_risk = Math.min(12, input.previous_deferrals * 4);
  const raw = severity + overdue_risk + traffic_impact + asset_criticality + deferral_risk;
  const score = Math.max(0, Math.min(100, Math.round((raw / 108) * 100)));
  return {
    score,
    breakdown: { severity, overdue_risk, traffic_impact, asset_criticality, deferral_risk },
  };
}

export function explainPriority(task: MaintenanceTask): string {
  const parts: string[] = [];
  parts.push(
    task.severity === "A"
      ? "the defect is classified Severity A (safety critical)"
      : task.severity === "B"
        ? "the defect is Severity B (service affecting)"
        : "the defect is Severity C (routine)",
  );
  if (task.overdue_days > 0) parts.push(`it is overdue by ${task.overdue_days} days`);
  if (task.previous_deferrals > 0)
    parts.push(`it has been deferred ${task.previous_deferrals} time(s)`);
  parts.push(`it sits on section ${task.section_id} with high traffic utilisation`);
  if (task.asset_criticality > 70) parts.push("the asset is rated high criticality");
  return `Priority ${task.priority_score}/100 because ${parts.join(", ")}. Scoring is produced by the local MDPS priority model (AI Simulation) and is fully deterministic and auditable.`;
}
