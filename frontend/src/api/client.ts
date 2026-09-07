/**
 * Central HTTP client for RailBlock AI backend integration.
 */

export const API_BASE_URL =
  (typeof import.meta !== "undefined" && import.meta.env?.["VITE_API_BASE_URL"]) ||
  "http://localhost:8000/api";

export const WS_BASE_URL =
  (typeof import.meta !== "undefined" && import.meta.env?.["VITE_WS_BASE_URL"]) ||
  "ws://localhost:8000";

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
