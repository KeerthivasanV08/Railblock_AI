import type { Station } from "@/types";

/** Synthetic but geographically grounded New Delhi – Kanpur corridor. */
export const STATIONS: Station[] = [
  { station_code: "NDLS", name: "New Delhi", km: 0, lat: 28.6431, lng: 77.2197, major: true },
  { station_code: "GZB", name: "Ghaziabad", km: 25, lat: 28.6675, lng: 77.4376, major: true },
  { station_code: "HPU", name: "Hapur", km: 57, lat: 28.7301, lng: 77.7806, major: false },
  { station_code: "KSV", name: "Khurja Jn", km: 87, lat: 28.2528, lng: 77.8556, major: false },
  { station_code: "ALJN", name: "Aligarh Jn", km: 126, lat: 27.8974, lng: 78.0781, major: true },
  { station_code: "TDL", name: "Tundla Jn", km: 183, lat: 27.2144, lng: 78.238, major: true },
  { station_code: "ETW", name: "Etawah Jn", km: 300, lat: 26.7855, lng: 79.0155, major: true },
  { station_code: "PHD", name: "Phaphund", km: 372, lat: 26.6002, lng: 79.4501, major: false },
  { station_code: "CNB", name: "Kanpur Central", km: 440, lat: 26.4499, lng: 80.3319, major: true },
];

export const stationByCode = (code: string) => STATIONS.find((s) => s.station_code === code);

export const CORRIDOR_START_KM = STATIONS[0].km;
export const CORRIDOR_END_KM = STATIONS[STATIONS.length - 1].km;

/** Interpolate a lat/lng along the corridor for an arbitrary chainage. */
export function kmToLatLng(km: number): { lat: number; lng: number } {
  const clamped = Math.min(Math.max(km, CORRIDOR_START_KM), CORRIDOR_END_KM);
  for (let i = 0; i < STATIONS.length - 1; i++) {
    const a = STATIONS[i];
    const b = STATIONS[i + 1];
    if (clamped >= a.km && clamped <= b.km) {
      const t = (clamped - a.km) / (b.km - a.km || 1);
      return { lat: a.lat + (b.lat - a.lat) * t, lng: a.lng + (b.lng - a.lng) * t };
    }
  }
  const last = STATIONS[STATIONS.length - 1];
  return { lat: last.lat, lng: last.lng };
}

export function kmToStationLabel(km: number): string {
  let nearest = STATIONS[0];
  for (const s of STATIONS) if (Math.abs(s.km - km) < Math.abs(nearest.km - km)) nearest = s;
  return nearest.station_code;
}
