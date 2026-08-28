import type { BlockSection } from "@/types";
import { STATIONS } from "./stations";

const DENSITY: Record<string, number> = {
  "SEC-NDLS-GZB": 96,
  "SEC-GZB-HPU": 74,
  "SEC-HPU-KSV": 61,
  "SEC-KSV-ALJN": 78,
  "SEC-ALJN-TDL": 88,
  "SEC-TDL-ETW": 82,
  "SEC-ETW-PHD": 69,
  "SEC-PHD-CNB": 85,
};

export const SECTIONS: BlockSection[] = STATIONS.slice(0, -1).map((s, i) => {
  const next = STATIONS[i + 1];
  const section_id = `SEC-${s.station_code}-${next.station_code}`;
  return {
    section_id,
    from_station: s.station_code,
    to_station: next.station_code,
    from_km: s.km,
    to_km: next.km,
    traffic_density: DENSITY[section_id] ?? 70,
    double_line: true,
  };
});

export const sectionById = (id: string) => SECTIONS.find((s) => s.section_id === id);

export function sectionForKm(km: number): BlockSection {
  return SECTIONS.find((s) => km >= s.from_km && km <= s.to_km) ?? SECTIONS[SECTIONS.length - 1];
}
