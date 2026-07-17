"use client";

import { MapPin } from "lucide-react";

import { ScrollArea } from "@/components/ui/scroll-area";
import type { Appointment, Customer } from "@/lib/types";

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function AppointmentList({
  appointments,
  customersById,
}: {
  appointments: Appointment[];
  customersById: Record<string, Customer>;
}) {
  if (appointments.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-8 text-center">
        No appointments scheduled yet.
      </p>
    );
  }

  return (
    <ScrollArea className="h-[560px] pr-4">
      <div className="space-y-3">
        {appointments.map((appointment) => (
          <div key={appointment.id} className="rounded-lg border p-4 space-y-1">
            <div className="flex items-start justify-between gap-2">
              <p className="font-medium text-sm">{appointment.title}</p>
              <span className="text-xs font-mono text-muted-foreground shrink-0">
                {formatDateTime(appointment.scheduled_at)}
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              {appointment.customer_id ? customersById[appointment.customer_id]?.name : "No customer linked"}
            </p>
            {appointment.location && (
              <p className="flex items-center gap-1 text-xs text-muted-foreground">
                <MapPin className="size-3" />
                {appointment.location}
              </p>
            )}
          </div>
        ))}
      </div>
    </ScrollArea>
  );
}
