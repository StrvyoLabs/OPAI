export type TaskStatus =
  | "received"
  | "planning"
  | "planned"
  | "executing"
  | "completed"
  | "completed_with_errors"
  | "failed";

export type PlanStepStatus = "pending" | "running" | "succeeded" | "failed" | "skipped";

export type ActivityType =
  | "message_received"
  | "message_sent"
  | "planning_started"
  | "plan_created"
  | "plan_failed"
  | "step_started"
  | "step_succeeded"
  | "step_failed"
  | "task_completed"
  | "task_failed";

export interface PlanStep {
  id: string;
  step_number: number;
  tool_name: string;
  tool_input: Record<string, unknown>;
  reasoning: string | null;
  status: PlanStepStatus;
  result: Record<string, unknown> | null;
  error: string | null;
}

export interface Plan {
  id: string;
  model_used: string;
  summary: string | null;
  created_at: string;
  steps: PlanStep[];
}

export interface Task {
  id: string;
  owner_phone: string;
  raw_request: string;
  status: TaskStatus;
  failure_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskDetail extends Task {
  plans: Plan[];
}

export interface ActivityEvent {
  id: string;
  task_id: string | null;
  type: ActivityType;
  message: string;
  payload: Record<string, unknown> | null;
  created_at: string;
}

export interface Customer {
  id: string;
  name: string;
  phone: string | null;
  email: string | null;
  notes: string | null;
  created_at: string;
}

export type InvoiceStatus = "pending" | "paid" | "overdue" | "cancelled";

export interface Invoice {
  id: string;
  invoice_number: string;
  customer_id: string;
  description: string;
  amount: number;
  currency_symbol: string;
  status: InvoiceStatus;
  file_url: string | null;
  created_at: string;
}

export interface Appointment {
  id: string;
  customer_id: string | null;
  title: string;
  scheduled_at: string;
  location: string | null;
  created_at: string;
}

export interface Equipment {
  id: string;
  customer_id: string;
  unit_type: string;
  brand_model: string | null;
  install_date: string | null;
  notes: string | null;
  created_at: string;
}

export type MaintenanceReminderStatus = "pending" | "sent" | "cancelled";

export interface MaintenanceReminder {
  id: string;
  customer_id: string;
  note: string;
  remind_at: string;
  status: MaintenanceReminderStatus;
  created_at: string;
}
