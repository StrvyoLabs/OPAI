"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Circle } from "lucide-react";

import { ActivityTimeline } from "@/components/activity-timeline";
import { AppointmentList } from "@/components/appointment-list";
import { type View, AppSidebar } from "@/components/app-sidebar";
import { CustomerList } from "@/components/customer-list";
import { EquipmentList } from "@/components/equipment-list";
import { InvoiceList } from "@/components/invoice-list";
import { MaintenanceReminderList } from "@/components/maintenance-reminder-list";
import { NewRequestDialog } from "@/components/new-request-dialog";
import { TaskList } from "@/components/task-list";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useActivityStream } from "@/hooks/use-activity-stream";
import {
  listActivity,
  listAppointments,
  listCustomers,
  listEquipment,
  listInvoices,
  listMaintenanceReminders,
  listTasks,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import type {
  ActivityEvent,
  Appointment,
  Customer,
  Equipment,
  Invoice,
  MaintenanceReminder,
  Task,
} from "@/lib/types";

const VIEW_META: Record<View, { title: string; description: string }> = {
  overview: { title: "Overview", description: "Recent requests and live activity" },
  customers: { title: "Customers", description: "Everyone the business has done work for" },
  invoices: { title: "Invoices", description: "Generated invoices and payment status" },
  appointments: { title: "Appointments", description: "Scheduled jobs and installs" },
  equipment: { title: "Equipment", description: "Units installed at customer properties" },
  reminders: { title: "Reminders", description: "Scheduled follow-ups with customers" },
};

export default function Home() {
  const [view, setView] = useState<View>("overview");
  const [tasks, setTasks] = useState<Task[]>([]);
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [equipment, setEquipment] = useState<Equipment[]>([]);
  const [reminders, setReminders] = useState<MaintenanceReminder[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [taskData, activityData, customerData, invoiceData, appointmentData, equipmentData, reminderData] =
        await Promise.all([
          listTasks(),
          listActivity(100),
          listCustomers(),
          listInvoices(),
          listAppointments(),
          listEquipment(),
          listMaintenanceReminders(),
        ]);
      setTasks(taskData);
      setEvents([...activityData].reverse());
      setCustomers(customerData);
      setInvoices(invoiceData);
      setAppointments(appointmentData);
      setEquipment(equipmentData);
      setReminders(reminderData);
      setLoadError(null);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Failed to load dashboard data");
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleLiveEvent = useCallback(
    (event: ActivityEvent) => {
      setEvents((prev) => [event, ...prev].slice(0, 200));
      refresh();
    },
    [refresh],
  );

  const wsStatus = useActivityStream(handleLiveEvent);

  const customersById = useMemo(
    () => Object.fromEntries(customers.map((c) => [c.id, c])),
    [customers],
  );

  const meta = VIEW_META[view];

  return (
    <div className="flex min-h-screen bg-background">
      <AppSidebar active={view} onNavigate={setView} />

      <div className="flex-1 min-w-0">
        <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80 sticky top-0 z-10">
          <div className="px-8 py-5 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold tracking-tight">{meta.title}</h2>
              <p className="text-sm text-muted-foreground">{meta.description}</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Circle
                  className={cn(
                    "size-2",
                    wsStatus === "open" && "fill-emerald-500 text-emerald-500",
                    wsStatus === "connecting" && "fill-amber-500 text-amber-500",
                    wsStatus === "closed" && "fill-red-500 text-red-500",
                  )}
                />
                {wsStatus === "open" ? "Live" : wsStatus === "connecting" ? "Connecting..." : "Disconnected"}
              </div>
              <NewRequestDialog onCreated={refresh} />
            </div>
          </div>
        </header>

        <main className="px-8 py-6 space-y-6 max-w-5xl">
          {loadError && (
            <p className="text-sm text-destructive">
              {loadError} -- is the backend running at the configured API URL?
            </p>
          )}

          {view === "overview" && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm font-medium text-muted-foreground">Requests</CardTitle>
                </CardHeader>
                <CardContent>
                  <TaskList tasks={tasks} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm font-medium text-muted-foreground">Activity</CardTitle>
                </CardHeader>
                <CardContent>
                  <ActivityTimeline events={events} />
                </CardContent>
              </Card>
            </div>
          )}

          {view === "customers" && (
            <Card>
              <CardContent className="pt-6">
                <CustomerList customers={customers} />
              </CardContent>
            </Card>
          )}

          {view === "invoices" && (
            <Card>
              <CardContent className="pt-6">
                <InvoiceList invoices={invoices} customersById={customersById} onChanged={refresh} />
              </CardContent>
            </Card>
          )}

          {view === "appointments" && (
            <Card>
              <CardContent className="pt-6">
                <AppointmentList appointments={appointments} customersById={customersById} />
              </CardContent>
            </Card>
          )}

          {view === "equipment" && (
            <Card>
              <CardContent className="pt-6">
                <EquipmentList equipment={equipment} customersById={customersById} />
              </CardContent>
            </Card>
          )}

          {view === "reminders" && (
            <Card>
              <CardContent className="pt-6">
                <MaintenanceReminderList reminders={reminders} customersById={customersById} />
              </CardContent>
            </Card>
          )}
        </main>
      </div>
    </div>
  );
}
