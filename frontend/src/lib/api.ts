import { API_BASE_URL } from "@/lib/config";
import type {
  ActivityEvent,
  Appointment,
  Customer,
  Equipment,
  Invoice,
  MaintenanceReminder,
  Task,
  TaskDetail,
} from "@/lib/types";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });

  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new Error(`${init?.method ?? "GET"} ${path} failed: ${response.status} ${body}`);
  }

  return response.json() as Promise<T>;
}

export function listTasks(limit = 50): Promise<Task[]> {
  return apiFetch(`/tasks?limit=${limit}`);
}

export function getTask(id: string): Promise<TaskDetail> {
  return apiFetch(`/tasks/${id}`);
}

export function listActivity(limit = 50): Promise<ActivityEvent[]> {
  return apiFetch(`/activity?limit=${limit}`);
}

export function createRequest(ownerPhone: string, rawRequest: string): Promise<Task> {
  return apiFetch(`/planner/plan`, {
    method: "POST",
    body: JSON.stringify({ owner_phone: ownerPhone, raw_request: rawRequest }),
  });
}

export function listCustomers(): Promise<Customer[]> {
  return apiFetch(`/customers`);
}

export function listInvoices(): Promise<Invoice[]> {
  return apiFetch(`/invoices`);
}

export function markInvoicePaid(invoiceId: string): Promise<Invoice> {
  return apiFetch(`/invoices/${invoiceId}/mark-paid`, { method: "POST" });
}

export function listAppointments(): Promise<Appointment[]> {
  return apiFetch(`/appointments`);
}

export function listEquipment(): Promise<Equipment[]> {
  return apiFetch(`/equipment`);
}

export function listMaintenanceReminders(): Promise<MaintenanceReminder[]> {
  return apiFetch(`/maintenance-reminders`);
}
