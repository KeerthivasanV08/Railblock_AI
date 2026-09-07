/**
 * Canonical Corridor Configuration — Chennai Egmore → Tuticorin
 *
 * This is the SINGLE authoritative source of corridor identity for the
 * RailBlock AI frontend.  Every component that needs to display corridor
 * metadata must import from here.
 *
 * Values are derived from the actual project datasets:
 *   - Station names / codes  →  data/raw/network/stations.csv  (STATIONS array)
 *   - Station sequence       →  src/data/stations.ts
 *   - Divisions              →  data/raw/network/stations.csv  (division column)
 *   - Corridor distance      →  STATIONS[last].km (648.2 km, from dataset)
 *
 * DO NOT duplicate corridor identity in individual components.
 * DO NOT invent values not present in the dataset.
 */

import { STATIONS } from "./stations";

const ORIGIN = STATIONS[0]!;       // Chennai Egmore  | MS  | Km 0.0
const DEST   = STATIONS[STATIONS.length - 1]!; // Tuticorin | TN  | Km 648.2

/** Immutable canonical corridor descriptor. */
export const CORRIDOR = {
  /** Short display name, e.g. for header pills and chart titles. */
  displayName: `${ORIGIN.name} – ${DEST.name}` as const,

  /** Human-readable short name (e.g. Chennai – Thoothukudi). */
  shortName: "Chennai – Thoothukudi" as const,

  /** Station code pair. */
  code: `${ORIGIN.station_code}-${DEST.station_code}` as const,

  /** Start kilometer chainage. */
  startKm: ORIGIN.km,

  /** End kilometer chainage. */
  endKm: DEST.km,

  /** Origin station (derived from dataset). */
  origin: {
    name: ORIGIN.name,           // "Chennai Egmore"
    code: ORIGIN.station_code,   // "MS"
    km:   ORIGIN.km,             // 0.0
  },

  /** Destination station (derived from dataset). */
  destination: {
    name: DEST.name,             // "Tuticorin"
    code: DEST.station_code,     // "TN"
    km:   DEST.km,               // 648.2
  },

  /**
   * Total corridor length in km, taken directly from the last station's
   * chainage in the dataset (data/raw/network/stations.csv, stations.ts).
   * Source: OSM-derived; provenance = DERIVED.
   */
  lengthKm: DEST.km,             // 648.2

  /**
   * Divisions present in data/raw/network/stations.csv (division column).
   * Listed in order of occurrence along the corridor.
   * Source: OGD-derived; provenance = DERIVED.
   */
  divisions: ["Chennai (MAS)", "Tiruchchirappalli (TPJ)", "Madurai (MDU)"] as const,

  /** Route identifier used as a value in select / filter controls. */
  routeId: "ms-tn" as const,

  /** Environment label shown in demo badges. */
  demoLabel: "Synthetic Demo" as const,
} as const;

export type CorridorConfig = typeof CORRIDOR;
