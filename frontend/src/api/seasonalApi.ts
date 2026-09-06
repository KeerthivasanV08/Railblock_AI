/**
 * Seasonal Intelligence & Weather Risk API Client.
 */

import { apiClient } from "./client";

export interface LiveWeatherReport {
  section_id: string;
  weather_status: "AVAILABLE" | "UNAVAILABLE" | "UNKNOWN";
  weather_source_status: string;
  temperature_c?: number;
  rainfall_mm?: number;
  wind_speed_kmh?: number;
  weather_severity?: number;
  condition: "CLEAR" | "CLOUDY" | "LIGHT_RAIN" | "HEAVY_RAIN" | "CYCLONE" | "EXTREME_HEAT" | "FOG" | "UNKNOWN";
  timestamp?: string;
}

export interface SectionSeasonalRisk {
  section_id: string;
  section_name: string;
  start_station: string;
  end_station: string;
  climate_zone: string;
  season_name: string;
  season_score: number;
  vulnerability_score: number;
  live_weather_severity?: number;
  raw_srs: number;
  asset_type: string;
  asset_multiplier: number;
  srs: number;
  risk_level: "LOW" | "MEDIUM" | "CRITICAL";
  hard_safety_exclusion: boolean;
  weather_source_status: string;
}

export interface SeasonalContextResponse {
  section_id: string;
  corridor: string;
  date: string;
  season: string;
  risk: SectionSeasonalRisk;
  live_weather: LiveWeatherReport;
  recommendations: string[];
}

export const seasonalApi = {
  getSectionContext: (sectionId: string): Promise<SeasonalContextResponse> => {
    return apiClient<SeasonalContextResponse>(`/seasonal/context/${encodeURIComponent(sectionId)}`);
  },

  getAllSectionRisks: (assetType = "TRACK"): Promise<SectionSeasonalRisk[]> => {
    return apiClient<SectionSeasonalRisk[]>(`/seasonal/sections?asset_type=${encodeURIComponent(assetType)}`);
  },

  getLiveWeather: (sectionId: string): Promise<LiveWeatherReport> => {
    return apiClient<LiveWeatherReport>(`/seasonal/live/${encodeURIComponent(sectionId)}`);
  },
};
