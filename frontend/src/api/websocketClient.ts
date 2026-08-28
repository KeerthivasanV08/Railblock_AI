import { WS_BASE_URL } from "./client";

export type WebSocketMessageHandler = (data: {
  event_type: string;
  timestamp: string;
  source?: string;
  data: unknown;
}) => void;

export class RailBlockWebSocket {
  private url: string;
  private ws: WebSocket | null = null;
  private handlers: Set<WebSocketMessageHandler> = new Set();
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  private isExplicitlyClosed = false;

  constructor(endpoint = "/ws/live") {
    const base = WS_BASE_URL.replace(/\/$/, "");
    const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
    this.url = `${base}${cleanEndpoint}`;
  }

  connect(): void {
    if (typeof window === "undefined") return;
    if (
      this.ws &&
      (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }

    this.isExplicitlyClosed = false;

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        // Connected
      };

      this.ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          this.handlers.forEach((handler) => handler(parsed));
        } catch {
          // Non-JSON or malformed payload
        }
      };

      this.ws.onclose = () => {
        if (!this.isExplicitlyClosed) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = () => {
        this.ws?.close();
      };
    } catch {
      this.scheduleReconnect();
    }
  }

  subscribe(handler: WebSocketMessageHandler): () => void {
    this.handlers.add(handler);
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      this.connect();
    }
    return () => {
      this.handlers.delete(handler);
    };
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimeout || this.isExplicitlyClosed) return;
    this.reconnectTimeout = setTimeout(() => {
      this.reconnectTimeout = null;
      this.connect();
    }, 5000);
  }

  disconnect(): void {
    this.isExplicitlyClosed = true;
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export const liveTrainSocket = new RailBlockWebSocket("/ws/live");
export const blockUpdateSocket = new RailBlockWebSocket("/ws/blocks");
