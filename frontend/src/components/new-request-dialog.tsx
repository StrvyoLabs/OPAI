"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { createRequest } from "@/lib/api";

export function NewRequestDialog({ onCreated }: { onCreated: () => void }) {
  const [open, setOpen] = useState(false);
  const [ownerPhone, setOwnerPhone] = useState("+15555550123");
  const [rawRequest, setRawRequest] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rawRequest.trim()) return;

    setSubmitting(true);
    setError(null);
    try {
      await createRequest(ownerPhone, rawRequest);
      setRawRequest("");
      setOpen(false);
      toast.success("Request submitted");
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit request");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={<Button size="sm" className="gap-1.5" />}>
        <Plus className="size-4" />
        New request
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Send a test request</DialogTitle>
            <DialogDescription>
              Simulates a WhatsApp message from the owner without needing WhatsApp configured yet.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-1.5">
              <Label htmlFor="owner-phone">Owner phone</Label>
              <Input
                id="owner-phone"
                value={ownerPhone}
                onChange={(e) => setOwnerPhone(e.target.value)}
                placeholder="+15555550123"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="raw-request">Request</Label>
              <Textarea
                id="raw-request"
                value={rawRequest}
                onChange={(e) => setRawRequest(e.target.value)}
                placeholder="e.g. Send a note that the vendor invoice is overdue"
                rows={3}
                autoFocus
              />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
          </div>
          <DialogFooter>
            <Button type="submit" disabled={submitting || !rawRequest.trim()}>
              {submitting ? "Submitting..." : "Submit request"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
