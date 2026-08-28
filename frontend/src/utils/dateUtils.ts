/** Minute-of-day helpers used by the planner timeline and simulation engine. */

export function toHHMM(min: number): string {
  const m = ((min % 1440) + 1440) % 1440;
  return `${String(Math.floor(m / 60)).padStart(2, "0")}:${String(Math.round(m % 60)).padStart(2, "0")}`;
}

export function windowLabel(start: number, duration: number): string {
  return `${toHHMM(start)}–${toHHMM(start + duration)}`;
}

export function overlaps(aStart: number, aDur: number, bStart: number, bDur: number): boolean {
  return aStart < bStart + bDur && bStart < aStart + aDur;
}

export function kmOverlaps(a1: number, a2: number, b1: number, b2: number): boolean {
  const [aLo, aHi] = a1 <= a2 ? [a1, a2] : [a2, a1];
  const [bLo, bHi] = b1 <= b2 ? [b1, b2] : [b2, b1];
  return aLo <= bHi + 2 && bLo <= aHi + 2;
}

export function clockNow(): string {
  const d = new Date();
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}
