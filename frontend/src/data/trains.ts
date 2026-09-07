import type { Train, TrainCategory, TrainPath } from "@/types";
import { intBetween, mulberry32, pick } from "@/lib/random";
import { sectionForKm } from "./sections";
import { CORRIDOR } from "./corridor";

const NAMES: Record<TrainCategory, string[]> = {
  Express: [
    "Shatabdi Express",
    "Rajdhani Express",
    "Vande Bharat Express",
    "Shram Shakti Express",
    "Prayagraj Express",
    "Gomti Express",
  ],
  Passenger: ["MS–CGL Passenger", "CGL–VM MEMU", "VM–TPJ Passenger", "TPJ–MDU MEMU"],
  Freight: ["Container Rake", "Coal Rake", "BOXN Goods", "Parcel Rake", "Tanker Rake"],
};

function mins(h: number, m: number) {
  return h * 60 + m;
}

export function generateTrains(): Train[] {
  const rand = mulberry32(770429);
  const trains: Train[] = [];
  const total = 140;
  const usedNumbers = new Set<string>(["12124", "G-88"]);

  for (let i = 0; i < total; i++) {
    const category: TrainCategory = i % 3 === 0 ? "Express" : i % 3 === 1 ? "Passenger" : "Freight";
    const km = Math.round(rand() * CORRIDOR.lengthKm * 10) / 10;
    const section = sectionForKm(km);
    const direction = i % 2 === 0 ? "UP" : "DOWN";

    let number = "";
    let attempts = 0;
    while (!number || usedNumbers.has(number)) {
      attempts++;
      if (category === "Express") {
        number = `${12000 + ((i * 17 + attempts) % 990)}`;
      } else if (category === "Passenger") {
        number = `${54000 + ((i * 19 + attempts) % 990)}`;
      } else {
        number = `G-${100 + i}`;
      }
    }
    usedNumbers.add(number);

    const dep = mins(intBetween(rand, 0, 22), pick(rand, [0, 10, 15, 25, 35, 45, 50]));
    const dur = intBetween(rand, 90, 400);
    trains.push({
      train_number: number,
      name: pick(rand, NAMES[category]),
      category,
      direction,
      section_id: section.section_id,
      km,
      speed_kmph: category === "Freight" ? intBetween(rand, 45, 75) : intBetween(rand, 90, 140),
      delay_min: rand() > 0.72 ? intBetween(rand, 5, 65) : 0,
      origin: direction === "UP" ? CORRIDOR.destination.code : CORRIDOR.origin.code,
      destination: direction === "UP" ? CORRIDOR.origin.code : CORRIDOR.destination.code,
      scheduled_dep: `${String(Math.floor(dep / 60)).padStart(2, "0")}:${String(dep % 60).padStart(2, "0")}`,
      scheduled_arr: `${String(Math.floor(((dep + dur) % 1440) / 60)).padStart(2, "0")}:${String((dep + dur) % 60).padStart(2, "0")}`,
    });
  }
  if (trains[0]) {
    trains[0] = {
      ...trains[0],
      train_number: "12124",
      name: "Pandian Express",
      category: "Express",
      km: 150.4,
      delay_min: 0,
      section_id: "SEC_030",
    };
  }
  if (trains[1]) {
    trains[1] = {
      ...trains[1],
      train_number: "G-88",
      name: "Container Rake",
      category: "Freight",
      km: 141.2,
      delay_min: 42,
      section_id: "SEC_028",
    };
  }
  return trains;
}

/** Planner timeline train paths for the demo date, within the 06:00–20:00 planning window. */
export function generateTrainPaths(): TrainPath[] {
  const rand = mulberry32(31415);
  const paths: TrainPath[] = [];
  const lanes: TrainCategory[] = ["Passenger", "Express", "Freight"];
  const numbers: Record<TrainCategory, string[]> = {
    Passenger: ["54471", "54472", "54301", "54312"],
    Express: ["12124", "12002", "12801", "12451"],
    Freight: ["G-88", "G-41", "G-64", "G-23"],
  };
  lanes.forEach((lane) => {
    numbers[lane].forEach((num, i) => {
      const start = mins(6, 0) + i * intBetween(rand, 120, 200) + intBetween(rand, 0, 40);
      const from_km = Math.round(rand() * 300);
      paths.push({
        id: `PATH-${num}-${i}`,
        train_number: num,
        lane,
        start_min: start,
        duration_min: intBetween(rand, 45, 110),
        section_id: sectionForKm(from_km).section_id,
        from_km,
        to_km: from_km + intBetween(rand, 20, 90),
      });
    });
  });
  // Curated conflict: express 12124 occupies 09:45–10:15 across the RB-402 corridor.
  paths.push({
    id: "PATH-12124-CONFLICT",
    train_number: "12124",
    lane: "Express",
    start_min: mins(9, 45),
    duration_min: 30,
    section_id: "SEC_030",
    from_km: 148,
    to_km: 162,
  });
  return paths;
}
