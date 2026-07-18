"use client";

import { useEffect, useRef, useState } from "react";
import type { RealtimeChannel } from "@supabase/supabase-js";

import { supabase } from "@/lib/supabase-client";
import type { ActivityEvent } from "@/lib/types";

type ConnectionStatus = "connecting" | "open" | "closed";

/** Raw shape of a row from Supabase Realtime's postgres_changes payload. */
interface ActivityEventRow {
  id: string;
  task_id: string | null;
  type: string;
  message: string;
  payload: Record<string, unknown> | null;
  created_at: string;
}

function toActivityEvent(row: ActivityEventRow): ActivityEvent {
  return {
    id: row.id,
    task_id: row.task_id,
    type: row.type as ActivityEvent["type"],
    message: row.message,
    payload: row.payload,
    created_at: row.created_at,
  };
}

/**
 * Subscribes to new activity_events rows directly via Supabase Realtime,
 * instead of a WebSocket server we'd have to host ourselves -- this is what
 * lets the dashboard get live updates with a fully serverless backend.
 */
export function useActivityStream(onEvent: (event: ActivityEvent) => void) {
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  useEffect(() => {
    let channel: RealtimeChannel | null = null;
    let cancelled = false;

    channel = supabase
      .channel("activity_events_live")
      .on(
        "postgres_changes",
        { event: "INSERT", schema: "public", table: "activity_events" },
        (payload) => {
          onEventRef.current(toActivityEvent(payload.new as ActivityEventRow));
        },
      )
      .subscribe((subscribeStatus) => {
        if (cancelled) return;
        if (subscribeStatus === "SUBSCRIBED") setStatus("open");
        else if (subscribeStatus === "CHANNEL_ERROR" || subscribeStatus === "TIMED_OUT") setStatus("closed");
        else if (subscribeStatus === "CLOSED") setStatus("closed");
      });

    return () => {
      cancelled = true;
      if (channel) supabase.removeChannel(channel);
    };
  }, []);

  return status;
}
