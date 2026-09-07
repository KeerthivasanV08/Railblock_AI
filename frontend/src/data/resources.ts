import type { Crew, Machine, ResourceAvailability } from "@/types";
import { intBetween, mulberry32, pick } from "@/lib/random";
import { kmToStationLabel } from "./stations";
import { CORRIDOR } from "./corridor";

const MACHINE_TYPES = [
  { type: "Tamping Machine", department: "Engineering" as const },
  { type: "Ballast Cleaning Machine", department: "Engineering" as const },
  { type: "Rail Grinder", department: "Engineering" as const },
  { type: "Inspection Vehicle", department: "S&T" as const },
  { type: "Tower Wagon", department: "TRD" as const },
  { type: "OHE Recording Car", department: "TRD" as const },
];

// Major station codes from the corridor — verified against data/raw/network/stations.csv
const DEPOTS = ["MS", "CGL", "VM", "TPJ", "MDU", "TN"];
const AVAIL: ResourceAvailability[] = ["Available", "Assigned", "Under Maintenance", "Unavailable"];

export function generateMachines(): Machine[] {
  const rand = mulberry32(99117);
  const machines: Machine[] = [];
  for (let i = 0; i < 48; i++) {
    const t = pick(rand, MACHINE_TYPES);
    const km = Math.round(rand() * CORRIDOR.lengthKm * 10) / 10;
    machines.push({
      resource_id: `MC-${t.type.split(" ")[0].toUpperCase().slice(0, 4)}-${100 + i}`,
      type: t.type,
      department: t.department,
      home_depot: pick(rand, DEPOTS),
      current_location: `Km ${km.toFixed(1)} (${kmToStationLabel(km)})`,
      km,
      availability: rand() > 0.32 ? "Available" : pick(rand, AVAIL),
      last_updated: `${String(intBetween(rand, 6, 12)).padStart(2, "0")}:${String(intBetween(rand, 0, 59)).padStart(2, "0")}`,
      assigned_task_id: null,
      utilization: intBetween(rand, 35, 96),
    });
  }
  machines[0] = {
    ...machines[0],
    resource_id: "MC-TAMP-101",
    type: "Tamping Machine",
    department: "Engineering",
    home_depot: "VM",
    current_location: "Km 154.2 (MYP)",
    km: 154.2,
    availability: "Available",
    assigned_task_id: "TMS-DEF-10234",
  };
  // Curated resource constraint: the second tamper is out of service.
  machines[1] = {
    ...machines[1],
    resource_id: "MC-TAMP-102",
    type: "Tamping Machine",
    department: "Engineering",
    availability: "Under Maintenance",
  };
  return machines;
}

export function generateCrews(): Crew[] {
  const rand = mulberry32(55231);
  const crews: Crew[] = [];
  const kinds = [
    { name: "P-Way Gang", department: "Engineering" as const },
    { name: "TRD Crew", department: "TRD" as const },
    { name: "S&T Crew", department: "S&T" as const },
  ];
  for (let i = 0; i < 36; i++) {
    const k = pick(rand, kinds);
    const km = Math.round(rand() * CORRIDOR.lengthKm * 10) / 10;
    crews.push({
      crew_id: `CRW-${k.department === "Engineering" ? "PW" : k.department === "TRD" ? "TRD" : "SNT"}-${200 + i}`,
      department: k.department,
      depot: pick(rand, DEPOTS),
      shift: rand() > 0.5 ? "Day 08–20" : "Night 20–08",
      headcount: intBetween(rand, 4, 18),
      availability: rand() > 0.3 ? "Available" : pick(rand, AVAIL),
      assigned_block_id: null,
      km,
      utilization: intBetween(rand, 40, 98),
    });
  }
  return crews;
}
