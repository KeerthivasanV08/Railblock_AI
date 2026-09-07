/**
 * Seasonal Risk Overlay Component
 *
 * Displays Seasonal Risk Score (SRS) for each corridor section,
 * with live weather badge when available.
 *
 * Data provenance: DERIVED — calculated by SeasonalIntelligenceService from
 *   OGD climate data + live weather telemetry (Chennai–Thoothukudi corridor).
 */

import { useEffect, useState, useCallback } from "react";
import {
  CloudRain,
  Flame,
  RefreshCw,
  ShieldAlert,
  Sun,
  Thermometer,
  Wind,
  AlertTriangle,
  Droplets,
} from "lucide-react";
import { seasonalApi, type SectionSeasonalRisk } from "@/api";

// ── Helpers ──────────────────────────────────────────────────────────────────

const RISK_COLOUR: Record<string, string> = {
  LOW: "text-ok border-ok/30 bg-ok/5",
  MEDIUM: "text-warn border-warn/30 bg-warn/5",
  CRITICAL: "text-crit border-crit/30 bg-crit/5",
};

const RISK_BAR: Record<string, string> = {
  LOW: "bg-ok",
  MEDIUM: "bg-warn",
  CRITICAL: "bg-crit",
};

const CONDITION_ICON: Record<string, React.ElementType> = {
  CLEAR: Sun,
  CLOUDY: Wind,
  LIGHT_RAIN: Droplets,
  HEAVY_RAIN: CloudRain,
  CYCLONE: ShieldAlert,
  EXTREME_HEAT: Flame,
  FOG: Wind,
  UNKNOWN: Thermometer,
};

function srsBarWidth(srs: number): string {
  return `${Math.min(100, Math.max(0, srs))}%`;
}

// ── Section Risk Card ────────────────────────────────────────────────────────
function SectionRiskCard({ risk }: { risk: SectionSeasonalRisk }) {
  const riskClass = RISK_COLOUR[risk.risk_level] ?? RISK_COLOUR["LOW"]!;
  const barClass = RISK_BAR[risk.risk_level] ?? RISK_BAR["LOW"]!;
  const WeatherIcon = CONDITION_ICON[risk.live_weather_severity !== undefined ? "CLEAR" : "UNKNOWN"] ?? Thermometer;

  return (
    <div className="rounded border border-border bg-surface px-3 py-2.5 text-xs">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="font-mono text-[11px] font-medium text-muted-foreground">
            {risk.section_id}
          </p>
          <p className="font-semibold text-foreground">
            {risk.start_station} → {risk.end_station}
          </p>
          <p className="text-[11px] text-muted-foreground">
            {risk.climate_zone} · {risk.season_name}
          </p>
        </div>
        <span className={`shrink-0 rounded border px-1.5 py-0.5 text-[10px] font-bold ${riskClass}`}>
          {risk.risk_level}
        </span>
      </div>

      {/* SRS bar */}
      <div className="mt-2 space-y-0.5">
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-muted-foreground">SRS</span>
          <span className="font-mono text-[10px] text-foreground">{risk.srs.toFixed(1)}</span>
        </div>
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-2">
          <div
            className={`h-full rounded-full transition-all ${barClass}`}
            style={{ width: srsBarWidth(risk.srs) }}
          />
        </div>
      </div>

      {/* Hard exclusion flag */}
      {risk.hard_safety_exclusion && (
        <div className="mt-2 flex items-center gap-1.5 rounded bg-crit/10 px-2 py-1 text-[10px] font-semibold text-crit">
          <AlertTriangle className="size-3 shrink-0" aria-hidden />
          Hard Safety Exclusion — Block not recommended
        </div>
      )}

      {/* Live weather badge */}
      {risk.live_weather_severity !== undefined && (
        <div className="mt-1.5 flex items-center gap-1 text-[10px] text-muted-foreground">
          <WeatherIcon className="size-3" aria-hidden />
          Live severity: {risk.live_weather_severity}
        </div>
      )}
    </div>
  );
}

// ── Main component ───────────────────────────────────────────────────────────
interface SeasonalRiskOverlayProps {
  /** When provided, shows only the given section's risk. */
  sectionId?: string;
  /** Asset type filter: "TRACK" | "OHE" | "SIGNAL" */
  assetType?: string;
  /** Whether to render inline (no card wrapper) */
  compact?: boolean;
}

export function SeasonalRiskOverlay({
  sectionId,
  assetType = "TRACK",
  compact = false,
}: SeasonalRiskOverlayProps) {
  const [risks, setRisks] = useState<SectionSeasonalRisk[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"ALL" | "CRITICAL" | "MEDIUM" | "LOW">("ALL");

  const fetchRisks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (sectionId) {
        const ctx = await seasonalApi.getSectionContext(sectionId);
        setRisks([ctx.risk]);
      } else {
        const res = await seasonalApi.getAllSectionRisks(assetType);
        setRisks(Array.isArray(res) ? res : []);
      }
    } catch {
      setError("Seasonal data unavailable — backend not reachable.");
    } finally {
      setLoading(false);
    }
  }, [sectionId, assetType]);

  useEffect(() => { void fetchRisks(); }, [fetchRisks]);

  const filtered = filter === "ALL"
    ? risks
    : risks.filter((r) => r.risk_level === filter);

  const criticalCount = risks.filter((r) => r.risk_level === "CRITICAL").length;
  const mediumCount = risks.filter((r) => r.risk_level === "MEDIUM").length;

  return (
    <div className={compact ? "" : "flex flex-col gap-4"}>
      {/* Header row */}
      {!compact && (
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Seasonal Risk Intelligence
            </p>
            <p className="mt-0.5 text-[11px] text-muted-foreground">
              {risks.length} sections · Asset type: {assetType} ·{" "}
              <span className="text-crit">{criticalCount} CRITICAL</span>
              {" · "}
              <span className="text-warn">{mediumCount} MEDIUM</span>
              <span className="ml-2 rounded bg-primary/10 px-1.5 py-0.5 text-[10px] text-primary">DERIVED</span>
            </p>
          </div>
          <button
            id="seasonal-refresh"
            onClick={() => void fetchRisks()}
            className="flex items-center gap-1.5 rounded border border-border bg-surface px-2.5 py-1.5 text-[11px] text-foreground transition-colors hover:bg-surface-2"
          >
            <RefreshCw className="size-3" aria-hidden /> Refresh
          </button>
        </div>
      )}

      {/* Filter pills */}
      {!compact && risks.length > 0 && (
        <div className="flex gap-1.5">
          {(["ALL", "CRITICAL", "MEDIUM", "LOW"] as const).map((f) => (
            <button
              key={f}
              id={`seasonal-filter-${f.toLowerCase()}`}
              onClick={() => setFilter(f)}
              className={`rounded border px-2.5 py-1 text-[11px] font-medium transition-colors ${
                filter === f
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-border bg-surface text-muted-foreground hover:border-border-strong"
              }`}
            >
              {f}
              {f !== "ALL" && (
                <span className="ml-1 text-[10px] opacity-70">
                  ({risks.filter((r) => r.risk_level === f).length})
                </span>
              )}
            </button>
          ))}
        </div>
      )}

      {/* Content */}
      {loading && (
        <p className="py-6 text-center text-xs text-muted-foreground">Loading seasonal data…</p>
      )}

      {error && (
        <div className="rounded border border-warn/30 bg-warn/5 px-3 py-2 text-xs text-warn">
          {error}
        </div>
      )}

      {!loading && !error && filtered.length === 0 && (
        <p className="py-6 text-center text-xs text-muted-foreground">
          No sections match the selected filter.
        </p>
      )}

      <div className="grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-3">
        {filtered.map((risk) => (
          <SectionRiskCard key={risk.section_id} risk={risk} />
        ))}
      </div>
    </div>
  );
}
