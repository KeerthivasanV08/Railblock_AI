import type { BlockPlan, Conflict, Crew, Machine, TrainPath } from "@/types";
import { kmOverlaps, overlaps, windowLabel } from "./dateUtils";

export interface ConflictContext {
  blocks: BlockPlan[];
  trainPaths: TrainPath[];
  machines: Machine[];
  crews: Crew[];
}

function alternatives(block: BlockPlan, ctx: ConflictContext) {
  const options: { start_min: number; duration_min: number; label: string }[] = [];
  for (let start = 6 * 60; start <= 20 * 60 - block.duration_min; start += 15) {
    if (start === block.start_min) continue;
    const clash = ctx.trainPaths.some(
      (p) =>
        kmOverlaps(p.from_km, p.to_km, block.from_km, block.to_km) &&
        overlaps(start, block.duration_min, p.start_min, p.duration_min),
    );
    const blockClash = ctx.blocks.some(
      (b) =>
        b.block_id !== block.block_id &&
        b.section_id === block.section_id &&
        overlaps(start, block.duration_min, b.start_min, b.duration_min),
    );
    if (!clash && !blockClash) {
      options.push({
        start_min: start,
        duration_min: block.duration_min,
        label: windowLabel(start, block.duration_min),
      });
      start += 105; // spread suggestions out
    }
    if (options.length >= 3) break;
  }
  return options;
}

/** Frontend conflict engine — deterministic, runs entirely on local state. */
export function detectConflicts(block: BlockPlan, ctx: ConflictContext): Conflict[] {
  const conflicts: Conflict[] = [];

  for (const path of ctx.trainPaths) {
    if (
      kmOverlaps(path.from_km, path.to_km, block.from_km, block.to_km) &&
      overlaps(block.start_min, block.duration_min, path.start_min, path.duration_min)
    ) {
      conflicts.push({
        id: `${block.block_id}-TRAIN-${path.id}`,
        type: "TRAIN_OVERLAP",
        block_id: block.block_id,
        entity: `Train ${path.train_number}`,
        window: windowLabel(path.start_min, path.duration_min),
        severity: "Critical",
        message: `Block ${block.block_id} overlaps the path of train ${path.train_number} between Km ${path.from_km} and Km ${path.to_km}.`,
        suggestions: alternatives(block, ctx),
      });
    }
  }

  for (const other of ctx.blocks) {
    if (other.block_id === block.block_id) continue;
    if (
      other.section_id === block.section_id &&
      overlaps(block.start_min, block.duration_min, other.start_min, other.duration_min) &&
      kmOverlaps(other.from_km, other.to_km, block.from_km, block.to_km)
    ) {
      conflicts.push({
        id: `${block.block_id}-BLOCK-${other.block_id}`,
        type: "BLOCK_OVERLAP",
        block_id: block.block_id,
        entity: `Block ${other.block_id}`,
        window: windowLabel(other.start_min, other.duration_min),
        severity: "Critical",
        message: `Two blocks occupy the same section (${block.section_id}) at the same time.`,
        suggestions: alternatives(block, ctx),
      });
    }
  }

  for (const rid of block.resource_ids) {
    const machine = ctx.machines.find((m) => m.resource_id === rid);
    if (machine && machine.availability !== "Available" && machine.availability !== "Assigned") {
      conflicts.push({
        id: `${block.block_id}-MC-${rid}`,
        type: "MACHINE_UNAVAILABLE",
        block_id: block.block_id,
        entity: `${machine.type} ${machine.resource_id}`,
        window: windowLabel(block.start_min, block.duration_min),
        severity: "Warning",
        message: `Required machine ${machine.resource_id} is ${machine.availability.toLowerCase()}.`,
        suggestions: [],
      });
    }
    const crew = ctx.crews.find((c) => c.crew_id === rid);
    if (crew && crew.availability !== "Available" && crew.availability !== "Assigned") {
      conflicts.push({
        id: `${block.block_id}-CRW-${rid}`,
        type: "CREW_UNAVAILABLE",
        block_id: block.block_id,
        entity: `Crew ${crew.crew_id}`,
        window: windowLabel(block.start_min, block.duration_min),
        severity: "Warning",
        message: `Required crew ${crew.crew_id} is ${crew.availability.toLowerCase()}.`,
        suggestions: [],
      });
    }
  }

  if (block.start_min + block.duration_min > 24 * 60) {
    conflicts.push({
      id: `${block.block_id}-WINDOW`,
      type: "WINDOW_TOO_SHORT",
      block_id: block.block_id,
      entity: "Planning window",
      window: windowLabel(block.start_min, block.duration_min),
      severity: "Warning",
      message: "Block duration exceeds the available planning window for the selected date.",
      suggestions: alternatives(block, ctx),
    });
  }

  return conflicts;
}

export function detectAllConflicts(ctx: ConflictContext): Conflict[] {
  return ctx.blocks.flatMap((b) => detectConflicts(b, ctx));
}
