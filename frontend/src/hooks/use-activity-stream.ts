"use client";

import { useEffect, useRef, useState } from "react";

import { WS_BASE_URL } from "@/lib/config";
import type { ActivityEvent } from "@/lib/types";

type ConnectionStatus = "connecting" | "open" | "closed";

interface ActivityStreamMessage {
  event: "activity";
  data: ActivityEvent;
}

export function useActivityStream(onEvent: (event: ActivityEvent) => void) {
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  useEffect(() => {
    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let cancelled = false;

    const connect = () => {
      if (cancelled) return;
      setStatus("connecting");
      socket = new WebSocket(`${WS_BASE_URL}/ws/activity`);

      socket.onopen = () => setStatus("open");

      socket.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data) as ActivityStreamMessage;
          if (parsed.event === "activity") {
            onEventRef.current(parsed.data);
          }
        } catch {
          // ignore malformed frames
        }
      };

      socket.onclose = () => {
        setStatus("closed");
        if (!cancelled) {
          reconnectTimer = setTimeout(connect, 2000);
        }
      };

      socket.onerror = () => {
        socket?.close();
      };
    };

    connect();

    return () => {
      cancelled = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, []);

  return status;
}
