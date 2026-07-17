"use client";

import { ScrollArea } from "@/components/ui/scroll-area";
import type { Customer } from "@/lib/types";

export function CustomerList({ customers }: { customers: Customer[] }) {
  if (customers.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-8 text-center">
        No customers yet. They're created automatically as requests reference them.
      </p>
    );
  }

  return (
    <ScrollArea className="h-[560px] pr-4">
      <div className="space-y-3">
        {customers.map((customer) => (
          <div key={customer.id} className="rounded-lg border p-4 space-y-1">
            <p className="font-medium text-sm">{customer.name}</p>
            <div className="text-xs text-muted-foreground space-y-0.5">
              {customer.phone && <p>{customer.phone}</p>}
              {customer.email && <p>{customer.email}</p>}
              {!customer.phone && !customer.email && <p>No contact info on file</p>}
            </div>
            {customer.notes && <p className="text-xs text-muted-foreground pt-1">{customer.notes}</p>}
          </div>
        ))}
      </div>
    </ScrollArea>
  );
}
