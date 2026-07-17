import logging
from datetime import date, datetime, timedelta, timezone

from app.services.crm_service import CRMService, CustomerNotFoundError
from app.services.equipment_service import EquipmentService
from app.services.invoice_service import InvoiceService
from app.services.maintenance_reminder_service import MaintenanceReminderService
from app.tools.base import ToolAdapter, ToolResult

logger = logging.getLogger(__name__)


class MarkInvoicePaidTool(ToolAdapter):
    name = "mark_invoice_paid"
    description = (
        "Mark an invoice as paid, e.g. when the owner reports a customer has paid. "
        "Stops any pending payment reminders for it. Provide either the exact "
        "invoice_number, or a customer_name to mark their most recent pending invoice paid."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "invoice_number": {"type": "string"},
            "customer_name": {"type": "string"},
        },
    }

    def __init__(self, crm_service: CRMService, invoice_service: InvoiceService) -> None:
        self._crm_service = crm_service
        self._invoice_service = invoice_service

    async def execute(self, tool_input: dict) -> ToolResult:
        invoice_number = tool_input.get("invoice_number")
        customer_name = tool_input.get("customer_name")
        if not invoice_number and not customer_name:
            return ToolResult(success=False, error="Either 'invoice_number' or 'customer_name' is required")

        try:
            if invoice_number:
                invoice = await self._invoice_service.find_by_number(invoice_number)
                if invoice is None:
                    return ToolResult(success=False, error=f"No invoice found with number {invoice_number}")
            else:
                customer = await self._crm_service.find(customer_name)
                invoice = await self._invoice_service.most_recent_pending_for_customer(customer.id)
                if invoice is None:
                    return ToolResult(
                        success=False, error=f"No pending invoice found for customer '{customer_name}'"
                    )

            updated = await self._invoice_service.mark_paid(invoice.id)
        except CustomerNotFoundError as exc:
            return ToolResult(success=False, error=str(exc))
        except Exception as exc:  # noqa: BLE001
            logger.exception("mark_invoice_paid failed")
            return ToolResult(success=False, error=str(exc))

        return ToolResult(
            success=True,
            output={"invoice_number": updated.invoice_number, "status": updated.status.value},
        )


class AddEquipmentTool(ToolAdapter):
    name = "add_equipment"
    description = (
        "Register a piece of equipment (e.g. an AC unit) installed at a customer's property, "
        "for service history and future maintenance tracking."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "customer_name": {"type": "string"},
            "unit_type": {"type": "string", "description": "e.g. 'Split AC', 'Central HVAC unit'"},
            "brand_model": {"type": "string"},
            "install_date": {"type": "string", "description": "YYYY-MM-DD, optional"},
            "notes": {"type": "string"},
        },
        "required": ["customer_name", "unit_type"],
    }

    def __init__(self, crm_service: CRMService, equipment_service: EquipmentService) -> None:
        self._crm_service = crm_service
        self._equipment_service = equipment_service

    async def execute(self, tool_input: dict) -> ToolResult:
        customer_name = tool_input.get("customer_name")
        unit_type = tool_input.get("unit_type")
        if not customer_name or not unit_type:
            return ToolResult(success=False, error="'customer_name' and 'unit_type' are required")

        install_date_raw = tool_input.get("install_date")
        install_date: date | None = None
        if install_date_raw:
            try:
                install_date = date.fromisoformat(install_date_raw)
            except ValueError as exc:
                return ToolResult(success=False, error=f"Invalid install_date: {exc}")

        try:
            customer = await self._crm_service.find_or_create(name=customer_name)
            equipment = await self._equipment_service.add(
                customer_id=customer.id,
                unit_type=unit_type,
                brand_model=tool_input.get("brand_model"),
                install_date=install_date,
                notes=tool_input.get("notes"),
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("add_equipment failed")
            return ToolResult(success=False, error=str(exc))

        return ToolResult(
            success=True,
            output={
                "equipment_id": str(equipment.id),
                "unit_type": equipment.unit_type,
                "brand_model": equipment.brand_model,
            },
        )


class ScheduleMaintenanceReminderTool(ToolAdapter):
    name = "schedule_maintenance_reminder"
    description = (
        "Schedule a follow-up reminder to reach out to a customer in the future, independent of "
        "any invoice -- e.g. seasonal AC servicing reminders. Use 'days' for the delay "
        "(e.g. 180 for roughly 6 months)."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "customer_name": {"type": "string"},
            "owner_phone": {
                "type": "string",
                "description": "The owner's own phone number (from the 'Owner phone' context), not the customer's.",
            },
            "note": {"type": "string", "description": "What to remind the owner about."},
            "days": {"type": "integer", "description": "Number of days from now to send the reminder."},
        },
        "required": ["customer_name", "owner_phone", "note", "days"],
    }

    def __init__(self, crm_service: CRMService, maintenance_reminder_service: MaintenanceReminderService) -> None:
        self._crm_service = crm_service
        self._maintenance_reminder_service = maintenance_reminder_service

    async def execute(self, tool_input: dict) -> ToolResult:
        customer_name = tool_input.get("customer_name")
        owner_phone = tool_input.get("owner_phone")
        note = tool_input.get("note")
        days = tool_input.get("days")
        if not customer_name or not owner_phone or not note or days is None:
            return ToolResult(
                success=False, error="'customer_name', 'owner_phone', 'note' and 'days' are required"
            )

        try:
            customer = await self._crm_service.find_or_create(name=customer_name)
            remind_at = datetime.now(timezone.utc) + timedelta(days=int(days))
            reminder = await self._maintenance_reminder_service.create(
                customer_id=customer.id, owner_phone=owner_phone, note=note, remind_at=remind_at
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("schedule_maintenance_reminder failed")
            return ToolResult(success=False, error=str(exc))

        return ToolResult(
            success=True,
            output={"reminder_id": str(reminder.id), "remind_at": remind_at.isoformat(), "note": note},
        )
