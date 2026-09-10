import type {
  AIRecommendation,
  BlockPlan,
  Crew,
  Department,
  DisruptionEvent,
  Machine,
  MaintenanceTask,
  RescheduleOption,
  TrainPath,
} from "@/types";
import { PLAN_DATE } from "@/data/operations";
import { kmOverlaps, overlaps, windowLabel } from "@/utils/dateUtils";
import { sectionById } from "@/data/sections";

export const AI_STAGES = [
  "Analyzing maintenance tasks…",
  "Checking traffic windows…",
  "Checking resource availability…",
  "Evaluating conflicts…",
  "Optimizing integrated blocks…",
  "Generating recommendation…",
] as const;

export interface GeneratePlanInput {
  tasks: MaintenanceTask[];
  trainPaths: TrainPath[];
  machines: Machine[];
  crews: Crew[];
  existingBlocks: BlockPlan[];
  date?: string;
}

interface Cluster {
  section_id: string;
  from_km: number;
  to_km: number;
  tasks: MaintenanceTask[];
}

/** Group pending tasks into spatially compatible clusters (shadow / integrated blocks). */
export function clusterTasks(tasks: MaintenanceTask[], limit = 6): Cluster[] {
  const candidates = tasks
    .filter((t) => t.status === "Pending" || t.status === "Deferred")
    .sort((a, b) => b.priority_score - a.priority_score)
    .slice(0, 400);

  const clusters: Cluster[] = [];
  for (const task of candidates) {
    const existing = clusters.find(
      (c) =>
        c.section_id === task.section_id &&
        kmOverlaps(c.from_km, c.to_km, task.from_km, task.to_km),
    );
    if (existing) {
      existing.from_km = Math.min(existing.from_km, task.from_km);
      existing.to_km = Math.max(existing.to_km, task.to_km);
      existing.tasks.push(task);
    } else if (clusters.length < 60) {
      clusters.push({
        section_id: task.section_id,
        from_km: task.from_km,
        to_km: task.to_km,
        tasks: [task],
      });
    }
  }
  return clusters
    .sort(
      (a, b) =>
        b.tasks.length * 8 + avgPriority(b.tasks) - (a.tasks.length * 8 + avgPriority(a.tasks)),
    )
    .slice(0, limit);
}

const avgPriority = (tasks: MaintenanceTask[]) =>
  tasks.reduce((s, t) => s + t.priority_score, 0) / Math.max(1, tasks.length);

function findWindow(
  duration: number,
  cluster: Cluster,
  input: GeneratePlanInput,
): { start: number; density: number } {
  let best = { start: 6 * 60, density: Number.POSITIVE_INFINITY };
  for (let start = 6 * 60; start <= 20 * 60 - duration; start += 15) {
    const trainClashes = input.trainPaths.filter(
      (p) =>
        kmOverlaps(p.from_km, p.to_km, cluster.from_km, cluster.to_km) &&
        overlaps(start, duration, p.start_min, p.duration_min),
    ).length;
    const blockClashes = input.existingBlocks.filter(
      (b) =>
        b.section_id === cluster.section_id &&
        overlaps(start, duration, b.start_min, b.duration_min),
    ).length;
    const density = trainClashes * 10 + blockClashes * 6 + (start < 8 * 60 ? 1 : 0);
    if (density < best.density) best = { start, density };
    if (density === 0) break;
  }
  return best;
}

/** Local AI plan generator (AI Simulation — deterministic optimisation heuristic). */
export function generateAIPlan(input: GeneratePlanInput): {
  blocks: BlockPlan[];
  recommendations: AIRecommendation[];
} {
  const date = input.date ?? PLAN_DATE;
  const clusters = clusterTasks(input.tasks);
  const blocks: BlockPlan[] = [];
  const recommendations: AIRecommendation[] = [];

  clusters.forEach((cluster, i) => {
    const duration = Math.min(
      240,
      Math.max(
        60,
        Math.round(cluster.tasks.reduce((s, t) => s + t.required_duration_min, 0) * 0.62),
      ),
    );
    const win = findWindow(duration, cluster, input);
    const departments = Array.from(new Set(cluster.tasks.map((t) => t.department))) as Department[];
    const section = sectionById(cluster.section_id);
    const resourceOk = input.machines.some((m) => m.availability === "Available");
    const crewOk = input.crews.some((c) => c.availability === "Available");
    const utilization = Math.min(
      98,
      Math.round(
        60 +
          departments.length * 7 +
          Math.min(18, cluster.tasks.length * 2.5) -
          (win.density > 0 ? 6 : 0),
      ),
    );
    const trainImpact: BlockPlan["train_impact"] =
      win.density === 0 ? "Low" : win.density < 12 ? "Medium" : "High";
    const block_id = `RB-${Math.round(500 + i * 7 + (cluster.from_km % 40))}`;

    blocks.push({
      block_id,
      section_id: cluster.section_id,
      lane: departments.length > 1 ? "Integrated" : (departments[0] ?? "Engineering"),
      departments,
      task_ids: cluster.tasks.map((t) => t.task_id),
      start_min: win.start,
      duration_min: duration,
      date,
      status: "AI RECOMMENDED",
      ai_generated: true,
      locked: false,
      utilization,
      train_impact: trainImpact,
      train_conflicts: [],
      from_km: cluster.from_km,
      to_km: cluster.to_km,
      resource_ids: [],
    });

    const priority = Math.round(avgPriority(cluster.tasks));
    recommendations.push({
      recommendation_id: `REC-${block_id.replace("RB-", "")}`,
      block_id,
      section_id: cluster.section_id,
      start_min: win.start,
      duration_min: duration,
      departments,
      task_ids: cluster.tasks.map((t) => t.task_id),
      priority,
      utilization,
      train_impact: trainImpact,
      confidence: Math.min(97, 60 + Math.round(utilization * 0.3) + (win.density === 0 ? 8 : 0)),
      status: "Pending",
      date,
      reasons: [
        `${cluster.tasks.length} compatible task(s) overlap between Km ${cluster.from_km.toFixed(2)} and Km ${cluster.to_km.toFixed(2)}`,
        win.density === 0
          ? "A completely clear traffic window was found"
          : "Lowest-traffic window selected after path evaluation",
        resourceOk && crewOk
          ? "Required machines and crew are available on the section"
          : "Partial resource availability — assignment required",
        `Aggregate maintenance priority ${priority}/100`,
        `Section traffic density ${section?.traffic_density ?? 70}%`,
      ],
      factors: [
        { label: "Task compatibility", value: Math.min(99, 55 + cluster.tasks.length * 6) },
        { label: "Spatial overlap", value: Math.min(99, 60 + cluster.tasks.length * 5) },
        { label: "Time window availability", value: win.density === 0 ? 92 : 74 },
        { label: "Traffic density penalty", value: section?.traffic_density ?? 70 },
        { label: "Resource availability", value: resourceOk && crewOk ? 88 : 58 },
        { label: "Aggregate task priority", value: priority },
      ],
    });
  });

  return { blocks, recommendations };
}

export function checkResourceAvailability(
  task: MaintenanceTask,
  machines: Machine[],
  crews: Crew[],
): { feasible: boolean; detail: string } {
  const machine = machines.find(
    (m) => m.type === task.required_resource && m.availability === "Available",
  );
  const crew = crews.find(
    (c) => c.department === task.department && c.availability === "Available",
  );
  if (machine)
    return {
      feasible: true,
      detail: `${machine.resource_id} available at ${machine.current_location}`,
    };
  if (crew) return { feasible: true, detail: `${crew.crew_id} available at ${crew.depot} depot` };
  return { feasible: false, detail: `No available ${task.required_resource} on the corridor` };
}

/** Self-healing rescheduler (RL Rescheduler v1.0-demo — simulated). */
export function generateRescheduleOptions(
  event: DisruptionEvent,
  block: BlockPlan | undefined,
  ctx: { trainPaths: TrainPath[]; blocks: BlockPlan[] },
): RescheduleOption[] {
  const duration = block?.duration_min ?? 180;
  const base = (block?.start_min ?? 9 * 60) + Math.max(45, event.delay_min);
  const candidates = [base + 15, base + 5 * 60, base + 9 * 60];

  return candidates.map((start, i) => {
    const clashes = ctx.trainPaths.filter(
      (p) =>
        block &&
        kmOverlaps(p.from_km, p.to_km, block.from_km, block.to_km) &&
        overlaps(start, duration, p.start_min, p.duration_min),
    ).length;
    const impact: RescheduleOption["train_impact"] =
      clashes === 0 ? "Low" : clashes < 2 ? "Medium" : "High";
    const nextDay = start >= 24 * 60;
    return {
      id: `OPT-${String.fromCharCode(65 + i)}`,
      label: nextDay ? "Next day (early window)" : windowLabel(start % 1440, duration),
      start_min: start % 1440,
      duration_min: duration,
      train_impact: nextDay ? "High" : impact,
      maintenance_impact:
        i === 0 ? "No task lost" : i === 1 ? "No task lost" : "2 tasks deferred to next cycle",
      resource_impact:
        i === 2 ? "Tamping machine re-mobilisation required" : "Resources remain available",
      utilization: Math.max(52, 92 - i * 11 - clashes * 4),
      confidence: Math.max(48, 94 - i * 14 - clashes * 6),
      added_train_delay_min: i === 0 ? 8 : i === 1 ? 3 : 0,
    };
  });
}
