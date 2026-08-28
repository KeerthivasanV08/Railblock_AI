import type {
  AIRecommendation,
  AppNotification,
  AuditEvent,
  BlockPlan,
  DisruptionEvent,
} from "@/types";
import { intBetween, mulberry32, pick } from "@/lib/random";
import { SECTIONS } from "./sections";

export const PLAN_DATE = "2026-08-26";
export const PLAN_START_MIN = 6 * 60;
export const PLAN_END_MIN = 20 * 60;

export function generateBlocks(): BlockPlan[] {
  const rand = mulberry32(4021);
  const blocks: BlockPlan[] = [
    {
      block_id: "RB-402",
      section_id: "SEC-ALJN-TDL",
      lane: "Integrated",
      departments: ["Engineering", "TRD", "S&T"],
      task_ids: [
        "TMS-DEF-10234",
        "TMS-DEF-10235",
        "TMS-DEF-10236",
        "TDMS-DEF-10237",
        "TDMS-DEF-10238",
        "SMMS-DEF-10239",
        "SMMS-DEF-10240",
      ],
      start_min: 8 * 60 + 30,
      duration_min: 180,
      date: PLAN_DATE,
      status: "AI RECOMMENDED",
      ai_generated: true,
      locked: false,
      utilization: 91,
      train_impact: "Low",
      train_conflicts: ["12124"],
      from_km: 154.2,
      to_km: 155.6,
      resource_ids: ["MC-TAMP-101", "CRW-PW-200"],
    },
  ];
  const lanes = ["Engineering", "TRD", "S&T"] as const;
  for (let i = 0; i < 11; i++) {
    const lane = lanes[i % 3];
    const section = pick(rand, SECTIONS);
    const start = PLAN_START_MIN + intBetween(rand, 0, 12) * 60 + pick(rand, [0, 15, 30, 45]);
    const from_km =
      Math.round((section.from_km + rand() * (section.to_km - section.from_km)) * 10) / 10;
    blocks.push({
      block_id: `RB-${410 + i}`,
      section_id: section.section_id,
      lane,
      departments: [lane === "Engineering" ? "Engineering" : lane === "TRD" ? "TRD" : "S&T"],
      task_ids: [],
      start_min: start,
      duration_min: pick(rand, [60, 90, 120, 150, 180]),
      date: PLAN_DATE,
      status: pick(rand, ["APPROVED", "SCHEDULED", "PENDING APPROVAL", "ACTIVE", "DRAFT"]),
      ai_generated: rand() > 0.6,
      locked: rand() > 0.85,
      utilization: intBetween(rand, 52, 96),
      train_impact: pick(rand, ["Low", "Medium", "High"]),
      train_conflicts: [],
      from_km,
      to_km: from_km + Math.round(rand() * 30) / 10 + 0.5,
      resource_ids: [],
    });
  }
  return blocks;
}

export function generateRecommendations(): AIRecommendation[] {
  return [
    {
      recommendation_id: "REC-402",
      block_id: "RB-402",
      section_id: "SEC-ALJN-TDL",
      start_min: 8 * 60 + 30,
      duration_min: 180,
      departments: ["Engineering", "TRD", "S&T"],
      task_ids: [
        "TMS-DEF-10234",
        "TMS-DEF-10235",
        "TMS-DEF-10236",
        "TDMS-DEF-10237",
        "TDMS-DEF-10238",
        "SMMS-DEF-10239",
        "SMMS-DEF-10240",
      ],
      priority: 94,
      utilization: 91,
      train_impact: "Low",
      confidence: 92,
      status: "Pending",
      date: PLAN_DATE,
      reasons: [
        "7 compatible tasks spatially overlap between Km 154.20 and Km 155.60",
        "Suitable traffic window identified between two express paths",
        "Required resources (MC-TAMP-101, Tower Wagon, S&T Crew) are available",
        "Cluster contains 3 Severity A defects overdue by 6–34 days",
        "Estimated train disruption is low (2 freight paths re-timed)",
      ],
      factors: [
        { label: "Task compatibility", value: 93 },
        { label: "Spatial overlap", value: 96 },
        { label: "Time window availability", value: 84 },
        { label: "Traffic density penalty", value: 62 },
        { label: "Resource availability", value: 88 },
        { label: "Aggregate task priority", value: 94 },
      ],
    },
    {
      recommendation_id: "REC-417",
      block_id: "RB-417",
      section_id: "SEC-ETW-PHD",
      start_min: 13 * 60,
      duration_min: 120,
      departments: ["TRD"],
      task_ids: [],
      priority: 71,
      utilization: 78,
      train_impact: "Medium",
      confidence: 74,
      status: "Pending",
      date: PLAN_DATE,
      reasons: [
        "OHE wear cluster detected near Km 318",
        "Tower Wagon available at ETW depot",
        "Mid-day window has lowest passenger density on this section",
      ],
      factors: [
        { label: "Task compatibility", value: 70 },
        { label: "Spatial overlap", value: 66 },
        { label: "Time window availability", value: 81 },
        { label: "Traffic density penalty", value: 55 },
        { label: "Resource availability", value: 90 },
        { label: "Aggregate task priority", value: 71 },
      ],
    },
    {
      recommendation_id: "REC-424",
      block_id: "RB-424",
      section_id: "SEC-NDLS-GZB",
      start_min: 1 * 60 + 30,
      duration_min: 90,
      departments: ["S&T", "Engineering"],
      task_ids: [],
      priority: 66,
      utilization: 69,
      train_impact: "Low",
      confidence: 68,
      status: "Pending",
      date: PLAN_DATE,
      reasons: [
        "Night window with minimum suburban traffic",
        "Track circuit and point machine faults are co-located at GZB yard",
        "S&T Crew night shift on duty",
      ],
      factors: [
        { label: "Task compatibility", value: 64 },
        { label: "Spatial overlap", value: 72 },
        { label: "Time window availability", value: 88 },
        { label: "Traffic density penalty", value: 41 },
        { label: "Resource availability", value: 76 },
        { label: "Aggregate task priority", value: 66 },
      ],
    },
  ];
}

export function generateDisruptions(): DisruptionEvent[] {
  return [
    {
      event_id: "EVT-9001",
      type: "Train Delay",
      detected_at: "09:12",
      train_number: "G-88",
      delay_min: 42,
      section_id: "SEC-ALJN-TDL",
      location: "Aligarh Jn (ALJN)",
      affected_block_id: "RB-402",
      original_window: "09:00–12:00",
      available_window: "09:00–10:18",
      status: "Open",
      severity: "Critical",
    },
    {
      event_id: "EVT-9002",
      type: "Resource Breakdown",
      detected_at: "07:48",
      delay_min: 0,
      section_id: "SEC-TDL-ETW",
      location: "Tundla Jn (TDL)",
      affected_block_id: "RB-411",
      original_window: "10:00–12:00",
      available_window: "Resource unavailable",
      status: "Open",
      severity: "Warning",
    },
    {
      event_id: "EVT-9003",
      type: "Weather",
      detected_at: "06:20",
      delay_min: 15,
      section_id: "SEC-PHD-CNB",
      location: "Phaphund (PHD)",
      affected_block_id: null,
      original_window: "—",
      available_window: "—",
      status: "Dismissed",
      severity: "Info",
    },
  ];
}

export function generateNotifications(): AppNotification[] {
  return [
    {
      id: "N-1",
      type: "AI Recommendation",
      title: "Integrated block RB-402 recommended",
      body: "7 tasks across Engineering, TRD and S&T can be executed in a single 3-hour block.",
      at: "08:04",
      read: false,
      href: "/recommendations/REC-402",
      severity: "Info",
    },
    {
      id: "N-2",
      type: "Critical Defect",
      title: "Severity A defect TMS-DEF-10234 overdue 17 days",
      body: "Track parameter deviation at Km 154.20–154.85 on SEC-ALJN-TDL.",
      at: "08:11",
      read: false,
      href: "/tasks/TMS-DEF-10234",
      severity: "Critical",
    },
    {
      id: "N-3",
      type: "Train Delay",
      title: "Freight G-88 running 42 min late",
      body: "Delay impacts the available maintenance window for block RB-402.",
      at: "09:12",
      read: false,
      href: "/disruptions/EVT-9001",
      severity: "Warning",
    },
    {
      id: "N-4",
      type: "Approval Required",
      title: "3 blocks awaiting controller approval",
      body: "Pending approvals for today's plan on the New Delhi – Kanpur corridor.",
      at: "09:20",
      read: true,
      href: "/planner",
      severity: "Info",
    },
  ];
}

export function generateAudit(): AuditEvent[] {
  return [
    {
      id: "A-1",
      at: "09:42",
      role: "Section Controller",
      action: "Approved Block",
      entity: "RB-410",
      result: "Success",
    },
    {
      id: "A-2",
      at: "09:55",
      role: "Engineering Planner",
      action: "Modified Task",
      entity: "TMS-DEF-10236",
      result: "Success",
    },
    {
      id: "A-3",
      at: "10:03",
      role: "System Administrator",
      action: "Refreshed Simulated Feed",
      entity: "COA",
      result: "Success",
    },
  ];
}
