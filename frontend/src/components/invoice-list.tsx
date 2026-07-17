"use client";

import { useState } from "react";
import { CheckCircle2, Download } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { StatusBadge } from "@/components/status-badge";
import { markInvoicePaid } from "@/lib/api";
import type { Customer, Invoice } from "@/lib/types";

function formatTime(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function InvoiceList({
  invoices,
  customersById,
  onChanged,
}: {
  invoices: Invoice[];
  customersById: Record<string, Customer>;
  onChanged: () => void;
}) {
  const [markingId, setMarkingId] = useState<string | null>(null);

  const handleMarkPaid = async (invoice: Invoice) => {
    setMarkingId(invoice.id);
    try {
      await markInvoicePaid(invoice.id);
      toast.success(`${invoice.invoice_number} marked as paid`);
      onChanged();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to mark invoice as paid");
    } finally {
      setMarkingId(null);
    }
  };

  if (invoices.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-8 text-center">
        No invoices yet. They'll appear here as they're generated.
      </p>
    );
  }

  return (
    <ScrollArea className="h-[560px] pr-4">
      <div className="space-y-3">
        {invoices.map((invoice) => (
          <div key={invoice.id} className="rounded-lg border p-4 space-y-2">
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="font-medium text-sm">{invoice.invoice_number}</p>
                <p className="text-xs text-muted-foreground">
                  {customersById[invoice.customer_id]?.name ?? "Unknown customer"}
                </p>
              </div>
              <StatusBadge status={invoice.status} />
            </div>
            <p className="text-sm text-muted-foreground">{invoice.description}</p>
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold">
                {invoice.currency_symbol}
                {invoice.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </p>
              <div className="flex items-center gap-3">
                <span className="text-xs text-muted-foreground">{formatTime(invoice.created_at)}</span>
                {invoice.file_url && (
                  <a
                    href={invoice.file_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-xs text-primary hover:underline"
                  >
                    <Download className="size-3" />
                    PDF
                  </a>
                )}
              </div>
            </div>
            {invoice.status === "pending" && (
              <Button
                variant="outline"
                size="sm"
                className="w-full gap-1.5"
                disabled={markingId === invoice.id}
                onClick={() => handleMarkPaid(invoice)}
              >
                <CheckCircle2 className="size-3.5" />
                {markingId === invoice.id ? "Marking..." : "Mark as paid"}
              </Button>
            )}
          </div>
        ))}
      </div>
    </ScrollArea>
  );
}
