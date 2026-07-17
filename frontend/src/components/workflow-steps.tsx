"use client";

import { CheckCircle2, CircleDashed, Loader2, XCircle } from "lucide-react";

import { cn } from "@/lib/utils";
import type { PlanStep } from "@/lib/types";

const ICONS = {
  pending: CircleDashed,
  running: Loader2,
  succeeded: CheckCircle2,
  failed: XCircle,
  skipped: CircleDashed,
};

const ICON_STYLES = {
  pending: "text-muted-foreground",
  running: "text-amber-600 dark:text-amber-400 animate-spin",
  succeeded: "text-emerald-600 dark:text-emerald-400",
  failed: "text-red-600 dark:text-red-400",
  skipped: "text-muted-foreground",
};

function formatToolName(name: string) {
  return name.replace(/_/g, " ");
}

export function WorkflowSteps({ steps }: { steps: PlanStep[] }) {
  if (steps.length === 0) {
    return <p className="text-xs text-muted-foreground py-2">No plan yet.</p>;
  }

  return (
    <ol className="space-y-2 pt-2">
      {steps.map((step) => {
        const Icon = ICONS[step.status];
        return (
          <li key={step.id} className="flex items-start gap-2">
            <Icon className={cn("size-4 mt-0.5 shrink-0", ICON_STYLES[step.status])} />
            <div className="min-w-0">
              <p className="text-sm capitalize">{formatToolName(step.tool_name)}</p>
              {step.status === "failed" && step.error && (
                <p className="text-xs text-red-600 dark:text-red-400 break-words">{step.error}</p>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
