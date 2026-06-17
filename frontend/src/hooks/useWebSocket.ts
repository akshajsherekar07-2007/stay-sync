/**
 * useWebSocket — Custom React hook for real-time WebSocket events.
 *
 * Connects to the backend WebSocket endpoint using the JWT from authStore.
 * Automatically reconnects with exponential backoff on disconnect.
 * Triggers React Query invalidation based on incoming event types.
 *
 * Usage:
 *   const { isConnected, subscribe, unsubscribe } = useWebSocket();
 *
 *   // Auto-subscribes to user notifications on connect.
 *   // Call subscribe("property:<id>") when viewing a property page.
 */

import { useEffect, useRef, useCallback, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "../stores/authStore";

// ── Event types matching backend WSEventType ─────────────────────────────────

const WS_EVENT_TYPES = {
  NOTIFICATION_CREATED: "notification_created",
  HOLD_CREATED: "hold_created",
  HOLD_APPROVED: "hold_approved",
  HOLD_REJECTED: "hold_rejected",
  HOLD_CANCELLED: "hold_cancelled",
  HOLD_EXPIRED: "hold_expired",
  WAITLIST_PROMOTED: "waitlist_promoted",
  BED_STATUS_CHANGED: "bed_status_changed",
} as const;

// ── Query keys to invalidate per event type ──────────────────────────────────

const EVENT_INVALIDATION_MAP: Record<string, string[][]> = {
  [WS_EVENT_TYPES.NOTIFICATION_CREATED]: [
    ["unreadNotificationCount"],
    ["latestNotifications"],
    ["allNotifications"],
  ],
  [WS_EVENT_TYPES.HOLD_CREATED]: [
    ["studentHolds"],
    ["ownerHolds"],
    ["propertyHolds"],
  ],
  [WS_EVENT_TYPES.HOLD_APPROVED]: [
    ["studentHolds"],
    ["ownerHolds"],
    ["unreadNotificationCount"],
    ["latestNotifications"],
  ],
  [WS_EVENT_TYPES.HOLD_REJECTED]: [
    ["studentHolds"],
    ["ownerHolds"],
    ["unreadNotificationCount"],
    ["latestNotifications"],
  ],
  [WS_EVENT_TYPES.HOLD_CANCELLED]: [
    ["studentHolds"],
    ["ownerHolds"],
  ],
  [WS_EVENT_TYPES.HOLD_EXPIRED]: [
    ["studentHolds"],
    ["ownerHolds"],
    ["unreadNotificationCount"],
    ["latestNotifications"],
  ],
  [WS_EVENT_TYPES.WAITLIST_PROMOTED]: [
    ["studentHolds"],
    ["unreadNotificationCount"],
    ["latestNotifications"],
  ],
  [WS_EVENT_TYPES.BED_STATUS_CHANGED]: [
    ["property"],
    ["beds"],
  ],
};

// ── Configuration ────────────────────────────────────────────────────────────

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";
const MAX_RECONNECT_DELAY_MS = 30_000;
const INITIAL_RECONNECT_DELAY_MS = 1_000;

function getWsUrl(token: string): string {
  const loc = window.location;
  const protocol = loc.protocol === "https:" ? "wss:" : "ws:";

  // If BASE_URL is absolute (starts with http), parse it
  if (BASE_URL.startsWith("http")) {
    const url = new URL(BASE_URL);
    const wsProtocol = url.protocol === "https:" ? "wss:" : "ws:";
    return `${wsProtocol}//${url.host}${url.pathname}/ws?token=${token}`;
  }

  // Relative BASE_URL — use current host
  return `${protocol}//${loc.host}${BASE_URL}/ws?token=${token}`;
}

// ── Hook ─────────────────────────────────────────────────────────────────────

export interface UseWebSocketReturn {
  /** Whether the WebSocket is currently connected */
  isConnected: boolean;
  /** Subscribe to a property room for bed updates */
  subscribe: (channel: string) => void;
  /** Unsubscribe from a property room */
  unsubscribe: (channel: string) => void;
}

export function useWebSocket(): UseWebSocketReturn {
  const queryClient = useQueryClient();
  const { isAuthenticated, accessToken } = useAuthStore();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectDelayRef = useRef(INITIAL_RECONNECT_DELAY_MS);
  const [isConnected, setIsConnected] = useState(false);
  const mountedRef = useRef(true);

  // Stable reference to the invalidation handler
  const handleEvent = useCallback(
    (event: MessageEvent) => {
      try {
        const parsed = JSON.parse(event.data);
        const eventType: string = parsed.type;

        if (!eventType || eventType === "pong" || eventType === "subscribed" || eventType === "unsubscribed") {
          return;
        }

        // Look up which query keys to invalidate for this event type
        const queryKeys = EVENT_INVALIDATION_MAP[eventType];
        if (queryKeys) {
          for (const key of queryKeys) {
            queryClient.invalidateQueries({ queryKey: key });
          }
        }
      } catch {
        // Silently ignore malformed messages
      }
    },
    [queryClient]
  );

  // Connect/disconnect lifecycle
  useEffect(() => {
    mountedRef.current = true;

    if (!isAuthenticated || !accessToken) {
      // Close existing connection if user logged out
      if (wsRef.current) {
        wsRef.current.close(1000, "User logged out");
        wsRef.current = null;
        setIsConnected(false);
      }
      return;
    }

    function connect() {
      if (!mountedRef.current || !accessToken) return;

      const url = getWsUrl(accessToken);
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mountedRef.current) return;
        setIsConnected(true);
        reconnectDelayRef.current = INITIAL_RECONNECT_DELAY_MS;
      };

      ws.onmessage = handleEvent;

      ws.onclose = (closeEvent) => {
        if (!mountedRef.current) return;
        setIsConnected(false);
        wsRef.current = null;

        // Don't reconnect on auth failure (4001) or intentional close
        if (closeEvent.code === 4001 || closeEvent.code === 1000) {
          return;
        }

        // Reconnect with exponential backoff
        const delay = reconnectDelayRef.current;
        reconnectTimerRef.current = setTimeout(() => {
          reconnectDelayRef.current = Math.min(delay * 2, MAX_RECONNECT_DELAY_MS);
          connect();
        }, delay);
      };

      ws.onerror = () => {
        // onerror is always followed by onclose — no action needed here
      };
    }

    connect();

    return () => {
      mountedRef.current = false;
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      if (wsRef.current) {
        wsRef.current.close(1000, "Component unmounting");
        wsRef.current = null;
      }
      setIsConnected(false);
    };
  }, [isAuthenticated, accessToken, handleEvent]);

  // Subscribe to a channel (e.g., "property:<uuid>")
  const subscribe = useCallback((channel: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "subscribe", channel }));
    }
  }, []);

  // Unsubscribe from a channel
  const unsubscribe = useCallback((channel: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "unsubscribe", channel }));
    }
  }, []);

  return { isConnected, subscribe, unsubscribe };
}
