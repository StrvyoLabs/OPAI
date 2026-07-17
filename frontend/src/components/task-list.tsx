"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { StatusBadge } from "@/components/status-badge";
import { WorkflowSteps } from "@/components/workflow-steps";
import { getTask } from "@/lib/api";
import type { Task, TaskDetail } from "@/lib/types";

function formatTime(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function TaskRow({ task }: { task: Task }) {
  const [expanded, setExpanded] = useState(false);
  const [detail, setDetail] = useState<TaskDetail | null>(null);
  const [loading, setLoading] = useState(false);

  const toggle = async () => {
    const next = !expanded;
    setExpanded(next);
    if (next && !detail) {
      setLoading(true);
      try {
        setDetail(await getTask(task.id));
      } finally {
        setLoading(false);
      }
    }
  };

  const steps = detail?.plans[0]?.steps ?? [];

  return (
    <Card className="shadow-none">
      <CardContent className="py-3 px-4 space-y-2">
        <button
          type="button"
          onClick={toggle}
          className="w-full flex items-start justify-between gap-2 text-left cursor-pointer"
        >
          <div className="flex items-start gap-1.5 min-w-0">
            {expanded ? (
              <ChevronDown className="size-4 mt-0.5 shrink-0 text-muted-foreground" />
            ) : (
              <ChevronRight className="size-4 mt-0.5 shrink-0 text-muted-foreground" />
            )}
            <p className="text-sm leading-snug">{task.raw_request}</p>
          </div>
          <StatusBadge status={task.status} />
        </button>
        <div className="flex items-center justify-between text-xs text-muted-foreground pl-5.5">
          <span>{task.owner_phone}</span>
          <span>{formatTime(task.created_at)}</span>
        </div>
        {task.failure_reason && (
          <p className="text-xs text-red-600 dark:text-red-400 pl-5.5">{task.failure_reason}</p>
        )}
        {expanded && (
          <div className="pl-5.5 border-t pt-2 mt-1">
            {loading ? (
              <p className="text-xs text-muted-foreground py-2">Loading...</p>
            ) : (
              <WorkflowSteps steps={steps} />
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function TaskList({ tasks }: { tasks: Task[] }) {
  if (tasks.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-8 text-center">
        No requests yet. Owner requests from WhatsApp will show up here.
      </p>
    );
  }

  return (
    <ScrollArea className="h-[560px] pr-4">
      <div className="space-y-3">
        {tasks.map((task) => (
          <TaskRow key={task.id} task={task} />
        ))}
      </div>
    </ScrollArea>
  );
}
