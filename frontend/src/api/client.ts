/**
 * Central HTTP client for RailBlock AI backend integration.
 */

const rawEnvApiUrl =
  (typeof import.meta !== "undefined" &&
    (import.meta.env?.["VITE_API_URL"] || import.meta.env?.["VITE_API_BASE_URL"])) ||
  "http://127.0.0.1:8000";

// Normalize API_BASE_URL: ensure it points to the /api root
function resolveApiBaseUrl(rawUrl: string): string {
  const trimmed = rawUrl.replace(/\/+$/, "");
  return trimmed.endsWith("/api") ? trimmed : `${trimmed}/api`;
}

// Normalize WS_BASE_URL: match API host with ws:// or wss://
function resolveWsBaseUrl(rawUrl: string): string {
  if (typeof import.meta !== "undefined" && import.meta.env?.["VITE_WS_BASE_URL"]) {
    return import.meta.env["VITE_WS_BASE_URL"];
  }
  const wsPrefix = rawUrl.startsWith("https") ? "wss://" : "ws://";
  const stripped = rawUrl.replace(/^https?:\/\//, "").replace(/\/+$/, "").replace(/\/api$/, "");
  return `${wsPrefix}${stripped}`;
}

export const API_BASE_URL = resolveApiBaseUrl(rawEnvApiUrl);
export const WS_BASE_URL = resolveWsBaseUrl(rawEnvApiUrl);

export interface ApiErrorResponse {
  error?: string;
  message?: string;
  detail?: string | Record<string, unknown>[];
  status?: number;
}

export class ApiError extends Error {
  status: number;
  data: ApiErrorResponse;

  constructor(status: number, data: ApiErrorResponse, defaultMessage = "API Request Failed") {
    const msg =
      data.message ||
      (typeof data.detail === "string" ? data.detail : null) ||
      data.error ||
      defaultMessage;
    super(msg);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

export async function apiClient<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = endpoint.startsWith("http")
    ? endpoint
    : `${API_BASE_URL.replace(/\/$/, "")}/${endpoint.replace(/^\//, "")}`;

  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...(options.headers as Record<string, string>),
  };

  try {
    const res = await fetch(url, {
      ...options,
      headers,
    });

    if (!res.ok) {
      let errData: ApiErrorResponse = {};
      try {
        errData = await res.json();
      } catch {
        errData = { message: res.statusText };
      }
      throw new ApiError(res.status, errData, `Request failed with status ${res.status}`);
    }

    // Handle 204 No Content
    if (res.status === 204) {
      return {} as T;
    }

    return (await res.json()) as T;
  } catch (err: unknown) {
    if (err instanceof ApiError) {
      throw err;
    }
    const message = err instanceof Error ? err.message : "Network error or backend unavailable";
    throw new ApiError(0, { message, error: "NETWORK_ERROR" }, message);
  }
}
