"use client";

import { Bell, Calendar, LayoutDashboard, Receipt, Users, Wrench } from "lucide-react";

import { cn } from "@/lib/utils";

export type View = "overview" | "customers" | "invoices" | "appointments" | "equipment" | "reminders";

const NAV_ITEMS: { id: View; label: string; icon: typeof LayoutDashboard }[] = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "customers", label: "Customers", icon: Users },
  { id: "invoices", label: "Invoices", icon: Receipt },
  { id: "appointments", label: "Appointments", icon: Calendar },
  { id: "equipment", label: "Equipment", icon: Wrench },
  { id: "reminders", label: "Reminders", icon: Bell },
];

export function AppSidebar({
  active,
  onNavigate,
}: {
  active: View;
  onNavigate: (view: View) => void;
}) {
  return (
    <aside className="w-60 shrink-0 border-r bg-sidebar text-sidebar-foreground flex flex-col h-screen sticky top-0">
      <div className="px-5 py-5">
        <h1 className="text-base font-semibold tracking-tight">Operator AI</h1>
        <p className="text-xs text-muted-foreground mt-0.5">Your AI business employee</p>
      </div>

      <nav className="flex-1 px-3 space-y-0.5">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = active === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onNavigate(item.id)}
              className={cn(
                "w-full flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors cursor-pointer",
                isActive
                  ? "bg-accent text-accent-foreground font-medium"
                  : "text-muted-foreground hover:bg-accent/50 hover:text-foreground",
              )}
            >
              <Icon className="size-4 shrink-0" />
              {item.label}
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
