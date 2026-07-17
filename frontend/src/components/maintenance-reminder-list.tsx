"use client";

import { Bell, BellOff } from "lucide-react";

import { ScrollArea } from "@/components/ui/scroll-area";
import { StatusBadge } from "@/components/status-badge";
import { cn } from "@/lib/utils";
import type { Customer, MaintenanceReminder } from "@/lib/types";

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export function MaintenanceReminderList({
  reminders,
  customersById,
}: {
  reminders: MaintenanceReminder[];
  customersById: Record<string, Customer>;
}) {
  if (reminders.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-8 text-center">
        No follow-up reminders scheduled yet.
      </p>
    );
  }

  return (
    <ScrollArea className="h-[560px] pr-4">
      <div className="space-y-3">
        {reminders.map((reminder) => {
          const Icon = reminder.status === "pending" ? Bell : BellOff;
          return (
            <div key={reminder.id} className="rounded-lg border p-4 space-y-1.5">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-start gap-2.5 min-w-0">
                  <Icon
                    className={cn(
                      "size-4 mt-0.5 shrink-0",
                      reminder.status === "pending" ? "text-primary" : "text-muted-foreground",
                    )}
                  />
                  <div className="min-w-0">
                    <p className="text-sm">{reminder.note}</p>
                    <p className="text-xs text-muted-foreground">
                      {customersById[reminder.customer_id]?.name ?? "Unknown customer"}
                    </p>
                  </div>
                </div>
                <StatusBadge status={reminder.status} />
              </div>
              <p className="text-xs text-muted-foreground pl-6.5">Due {formatDate(reminder.remind_at)}</p>
            </div>
          );
        })}
      </div>
    </ScrollArea>
  );
}
