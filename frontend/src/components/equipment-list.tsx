"use client";

import { Wrench } from "lucide-react";

import { ScrollArea } from "@/components/ui/scroll-area";
import type { Customer, Equipment } from "@/lib/types";

function formatDate(iso: string | null) {
  if (!iso) return null;
  return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export function EquipmentList({
  equipment,
  customersById,
}: {
  equipment: Equipment[];
  customersById: Record<string, Customer>;
}) {
  if (equipment.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-8 text-center">
        No equipment on file yet. Units get tracked here as they're installed.
      </p>
    );
  }

  return (
    <ScrollArea className="h-[560px] pr-4">
      <div className="space-y-3">
        {equipment.map((item) => (
          <div key={item.id} className="rounded-lg border p-4 space-y-1.5">
            <div className="flex items-start gap-2.5">
              <div className="rounded-md bg-accent p-1.5 shrink-0">
                <Wrench className="size-3.5 text-accent-foreground" />
              </div>
              <div className="min-w-0">
                <p className="font-medium text-sm">{item.unit_type}</p>
                <p className="text-xs text-muted-foreground">
                  {customersById[item.customer_id]?.name ?? "Unknown customer"}
                </p>
              </div>
            </div>
            {item.brand_model && <p className="text-xs text-muted-foreground pl-9">{item.brand_model}</p>}
            {item.install_date && (
              <p className="text-xs text-muted-foreground pl-9">Installed {formatDate(item.install_date)}</p>
            )}
            {item.notes && <p className="text-xs text-muted-foreground pl-9">{item.notes}</p>}
          </div>
        ))}
      </div>
    </ScrollArea>
  );
}
