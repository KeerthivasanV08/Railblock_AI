import type { Department, MaintenanceTask, Severity, SourceSystem, TaskStatus } from "@/types";
import { SECTIONS, sectionForKm } from "./sections";
import { kmToStationLabel } from "./stations";
import { intBetween, mulberry32, pick } from "@/lib/random";
import { calculatePriority } from "@/utils/scoring";

export const DEFECTS: Record<Department, string[]> = {
  Engineering: [
    "Rail Fracture Risk",
    "Weld Failure",
    "Track Parameter Deviation",
    "Deep Screening Overdue",
    "Ballast Issue",
    "Gauge Widening",
    "Rail Wear Beyond Limit",
  ],
  "S&T": [
    "Interlocking Fault",
    "Track Circuit Failure",
    "Axle Counter Error",
    "Cable Fault",
    "Point Machine Issue",
    "Signal Lamp Failure",
  ],
  TRD: [
    "Catenary Wear",
    "Neutral Section Fault",
    "Substation Feed Issue",
    "Insulator Damage",
    "Dropper Breakage",
    "OHE Sag Deviation",
  ],
};

const ASSETS: Record<Department, string[]> = {
  Engineering: ["Track Section", "Turnout", "Bridge Approach", "Level Crossing", "Rail Weld"],
  "S&T": ["Signal Post", "Point Machine", "Track Circuit", "Axle Counter", "Relay Room"],
  TRD: ["OHE Mast", "Neutral Section", "Feeder Post", "Insulator String", "Traction Substation"],
};

const RESOURCES: Record<Department, string[]> = {
  Engineering: ["Tamping Machine", "Ballast Cleaning Machine", "Rail Grinder", "P-Way Gang"],
  "S&T": ["S&T Crew", "Inspection Vehicle", "Cable Testing Kit"],
  TRD: ["Tower Wagon", "TRD Crew", "OHE Recording Car"],
};

const SOURCE: Record<Department, SourceSystem> = {
  Engineering: "TMS",
  "S&T": "SMMS",
  TRD: "TDMS",
};

const PREFIX: Record<Department, string> = {
  Engineering: "TMS-DEF",
  "S&T": "SMMS-DEF",
  TRD: "TDMS-DEF",
};

const DEPARTMENTS: Department[] = ["Engineering", "S&T", "TRD"];
const SEVERITIES: Severity[] = ["A", "B", "C"];
const STATUSES: TaskStatus[] = ["Pending", "Scheduled", "In Progress", "Completed", "Deferred"];

/** Full synthetic dataset scale (records held in memory, never all rendered). */
export const TASK_DATASET_SIZE = 25000;

function buildTask(
  index: number,
  rand: () => number,
  overrides?: Partial<MaintenanceTask>,
): MaintenanceTask {
  const department = overrides?.department ?? pick(rand, DEPARTMENTS);
  const from_km = overrides?.from_km ?? Math.round(rand() * 440 * 100) / 100;
  const to_km = overrides?.to_km ?? Math.round((from_km + 0.2 + rand() * 1.4) * 100) / 100;
  const section = sectionForKm(from_km);
  const severity = overrides?.severity ?? pick(rand, SEVERITIES);
  const overdue_days = overrides?.overdue_days ?? intBetween(rand, 0, 60);
  const previous_deferrals = overrides?.previous_deferrals ?? intBetween(rand, 0, 4);
  const asset_criticality = overrides?.asset_criticality ?? intBetween(rand, 35, 100);
  const { score, breakdown } = calculatePriority({
    severity,
    overdue_days,
    traffic_density: section.traffic_density,
    asset_criticality,
    previous_deferrals,
  });
  const defect = overrides?.defect ?? pick(rand, DEFECTS[department]);
  const id = overrides?.task_id ?? `${PREFIX[department]}-${10000 + index}`;
  const reportedDays = intBetween(rand, 1, 90);
  const reported = new Date(Date.UTC(2026, 7, 26) - reportedDays * 86400000).toISOString();

  const task: MaintenanceTask = {
    task_id: id,
    source_system: SOURCE[department],
    department,
    asset: pick(rand, ASSETS[department]),
    asset_criticality,
    section_id: section.section_id,
    from_km,
    to_km,
    location_label: `Km ${from_km.toFixed(2)}–${to_km.toFixed(2)} (${kmToStationLabel(from_km)})`,
    defect,
    severity,
    overdue_days,
    previous_deferrals,
    required_duration_min:
      overrides?.required_duration_min ?? pick(rand, [45, 60, 90, 120, 150, 180]),
    required_resource: overrides?.required_resource ?? pick(rand, RESOURCES[department]),
    status: overrides?.status ?? pick(rand, STATUSES),
    priority_score: score,
    priority_breakdown: breakdown,
    recommended_block_id: overrides?.recommended_block_id ?? null,
    reported_on: reported,
    history: [
      { date: reported.slice(0, 10), note: `Defect reported by ${SOURCE[department]} inspection.` },
      ...(previous_deferrals > 0
        ? [
            {
              date: new Date(Date.UTC(2026, 7, 26) - intBetween(rand, 5, 40) * 86400000)
                .toISOString()
                .slice(0, 10),
              note: `Deferred — traffic block not granted (${previous_deferrals} occurrence(s)).`,
            },
          ]
        : []),
    ],
    ...(department === "TRD"
      ? { mast_number: `OHE/${intBetween(rand, 100, 999)}/${intBetween(rand, 1, 40)}` }
      : {}),
    ...(department === "S&T"
      ? { signal_id: `SIG-${kmToStationLabel(from_km)}-${intBetween(rand, 1, 60)}` }
      : {}),
    ...overrides,
  };
  return task;
}

/** Curated demo cluster: spatially compatible multi-department tasks near Km 154. */
function demoCluster(rand: () => number): MaintenanceTask[] {
  const base: Array<Partial<MaintenanceTask>> = [
    {
      task_id: "TMS-DEF-10234",
      department: "Engineering",
      asset: "Track Section",
      defect: "Track Parameter Deviation",
      severity: "A",
      overdue_days: 17,
      previous_deferrals: 3,
      from_km: 154.2,
      to_km: 154.85,
      required_duration_min: 120,
      required_resource: "Tamping Machine",
      status: "Pending",
      asset_criticality: 92,
    },
    {
      task_id: "TMS-DEF-10235",
      department: "Engineering",
      asset: "Rail Weld",
      defect: "Weld Failure",
      severity: "A",
      overdue_days: 11,
      previous_deferrals: 2,
      from_km: 154.6,
      to_km: 154.9,
      required_duration_min: 90,
      required_resource: "P-Way Gang",
      status: "Pending",
      asset_criticality: 88,
    },
    {
      task_id: "TMS-DEF-10236",
      department: "Engineering",
      asset: "Turnout",
      defect: "Deep Screening Overdue",
      severity: "B",
      overdue_days: 34,
      previous_deferrals: 2,
      from_km: 155.1,
      to_km: 155.6,
      required_duration_min: 150,
      required_resource: "Ballast Cleaning Machine",
      status: "Pending",
      asset_criticality: 74,
    },
    {
      task_id: "TDMS-DEF-10237",
      department: "TRD",
      asset: "OHE Mast",
      defect: "Catenary Wear",
      severity: "A",
      overdue_days: 9,
      previous_deferrals: 1,
      from_km: 154.3,
      to_km: 154.8,
      required_duration_min: 100,
      required_resource: "Tower Wagon",
      status: "Pending",
      asset_criticality: 90,
    },
    {
      task_id: "TDMS-DEF-10238",
      department: "TRD",
      asset: "Insulator String",
      defect: "Insulator Damage",
      severity: "B",
      overdue_days: 21,
      previous_deferrals: 1,
      from_km: 155.0,
      to_km: 155.4,
      required_duration_min: 75,
      required_resource: "TRD Crew",
      status: "Pending",
      asset_criticality: 68,
    },
    {
      task_id: "SMMS-DEF-10239",
      department: "S&T",
      asset: "Track Circuit",
      defect: "Track Circuit Failure",
      severity: "A",
      overdue_days: 6,
      previous_deferrals: 0,
      from_km: 154.4,
      to_km: 154.7,
      required_duration_min: 60,
      required_resource: "S&T Crew",
      status: "Pending",
      asset_criticality: 85,
    },
    {
      task_id: "SMMS-DEF-10240",
      department: "S&T",
      asset: "Point Machine",
      defect: "Point Machine Issue",
      severity: "B",
      overdue_days: 14,
      previous_deferrals: 2,
      from_km: 155.2,
      to_km: 155.3,
      required_duration_min: 60,
      required_resource: "S&T Crew",
      status: "Pending",
      asset_criticality: 79,
    },
  ];
  return base.map((o, i) => buildTask(i, rand, { ...o, recommended_block_id: "RB-402" }));
}

let cache: MaintenanceTask[] | null = null;

export function getAllTasks(): MaintenanceTask[] {
  if (cache) return cache;
  const rand = mulberry32(20260826);
  const cluster = demoCluster(rand);
  const rest: MaintenanceTask[] = new Array(TASK_DATASET_SIZE - cluster.length);
  for (let i = 0; i < rest.length; i++) rest[i] = buildTask(i + 500, rand);
  cache = [...cluster, ...rest];
  return cache;
}

export const SECTION_IDS = SECTIONS.map((s) => s.section_id);
