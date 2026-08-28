export function minutesToDuration(min: number): string {
  const h = Math.floor(min / 60);
  const m = Math.round(min % 60);
  if (h === 0) return `${m} min`;
  return m === 0 ? `${h} h` : `${h} h ${m} min`;
}

export function km(value: number): string {
  return `Km ${value.toFixed(2)}`;
}

export function pct(value: number): string {
  return `${Math.round(value)}%`;
}
