"use client";

import {
  AlertTriangle,
  CheckCircle2,
  Loader2,
  MessageCircle,
  PlayCircle,
  Send,
  Sparkles,
  XCircle,
} from "lucide-react";

import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import type { ActivityEvent, ActivityType } from "@/lib/types";

const ICONS: Record<ActivityType, typeof MessageCircle> = {
  message_received: MessageCircle,
  message_sent: Send,
  planning_started: Loader2,
  plan_created: Sparkles,
  plan_failed: XCircle,
  step_started: PlayCircle,
  step_succeeded: CheckCircle2,
  step_failed: AlertTriangle,
  task_completed: CheckCircle2,
  task_failed: XCircle,
};

const ICON_STYLES: Record<ActivityType, string> = {
  message_received: "text-blue-600 dark:text-blue-400",
  message_sent: "text-blue-600 dark:text-blue-400",
  planning_started: "text-amber-600 dark:text-amber-400 animate-spin",
  plan_created: "text-indigo-600 dark:text-indigo-400",
  plan_failed: "text-red-600 dark:text-red-400",
  step_started: "text-amber-600 dark:text-amber-400",
  step_succeeded: "text-emerald-600 dark:text-emerald-400",
  step_failed: "text-red-600 dark:text-red-400",
  task_completed: "text-emerald-600 dark:text-emerald-400",
  task_failed: "text-red-600 dark:text-red-400",
};

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function ActivityTimeline({ events }: { events: ActivityEvent[] }) {
  if (events.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-8 text-center">
        No activity yet. Send a WhatsApp request or submit one below to see it appear here live.
      </p>
    );
  }

  return (
    <ScrollArea className="h-[560px] pr-4">
      <ol className="space-y-4">
        {events.map((event) => {
          const Icon = ICONS[event.type];
          return (
            <li key={event.id} className="flex gap-3">
              <div className="flex flex-col items-center">
                <Icon className={cn("size-4 mt-0.5 shrink-0", ICON_STYLES[event.type])} />
                <div className="w-px flex-1 bg-border mt-1" />
              </div>
              <div className="pb-4 min-w-0">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span className="font-mono">{formatTime(event.created_at)}</span>
                  <span className="capitalize">{event.type.replace(/_/g, " ")}</span>
                </div>
                <p className="text-sm leading-snug break-words">{event.message}</p>
              </div>
            </li>
          );
        })}
      </ol>
    </ScrollArea>
  );
}
