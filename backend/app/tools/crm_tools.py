import logging
from zoneinfo import ZoneInfo

from app.services.appointment_service import AppointmentService
from app.services.crm_service import CRMService
from app.services.equipment_service import EquipmentService
from app.services.invoice_service import InvoiceService
from app.services.maintenance_reminder_service import MaintenanceReminderService
from app.tools.base import ToolAdapter, ToolResult

logger = logging.getLogger(__name__)


class FindOrCreateCustomerTool(ToolAdapter):
    name = "find_customer"
    description = (
        "Look up a customer's full profile by name -- contact details, upcoming appointments, "
        "invoices, installed equipment, and scheduled maintenance reminders -- creating a new bare "
        "record if none exists. Use this to answer any question about a customer (e.g. 'when is X's "
        "appointment', 'has X paid', 'what unit does X have'), not just before creating a record."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "phone": {"type": "string", "description": "Optional; fills in the record if not already on file."},
            "email": {"type": "string", "description": "Optional; fills in the record if not already on file."},
        },
        "required": ["name"],
    }

    def __init__(
        self,
        crm_service: CRMService,
        appointment_service: AppointmentService,
        invoice_service: InvoiceService,
        equipment_service: EquipmentService,
        maintenance_reminder_service: MaintenanceReminderService,
        business_timezone: str,
    ) -> None:
        self._crm_service = crm_service
        self._appointment_service = appointment_service
        self._invoice_service = invoice_service
        self._equipment_service = equipment_service
        self._maintenance_reminder_service = maintenance_reminder_service
        self._timezone = ZoneInfo(business_timezone)

    async def execute(self, tool_input: dict) -> ToolResult:
        name = tool_input.get("name")
        if not name:
            return ToolResult(success=False, error="'name' is required")

        try:
            customer = await self._crm_service.find_or_create(
                name=name, phone=tool_input.get("phone"), email=tool_input.get("email")
            )
            appointments = await self._appointment_service.list_for_customer(customer.id)
            invoices = await self._invoice_service.list_for_customer(customer.id)
            equipment = await self._equipment_service.list_for_customer(customer.id)
            maintenance_reminders = await self._maintenance_reminder_service.list_for_customer(customer.id)
        except Exception as exc:  # noqa: BLE001
            logger.exception("find_customer failed")
            return ToolResult(success=False, error=str(exc))

        return ToolResult(
            success=True,
            output={
                "customer_id": str(customer.id),
                "name": customer.name,
                "phone": customer.phone,
                "email": customer.email,
                "appointments": [
                    {
                        "title": a.title,
                        "scheduled_at_local": a.scheduled_at.astimezone(self._timezone).strftime(
                            "%A, %d %b %Y at %I:%M %p"
                        ),
                        "location": a.location,
                    }
                    for a in appointments
                ],
                "invoices": [
                    {
                        "invoice_number": i.invoice_number,
                        "description": i.description,
                        "amount": i.amount,
                        "currency_symbol": i.currency_symbol,
                        "status": i.status.value,
                    }
                    for i in invoices
                ],
                "equipment": [
                    {
                        "unit_type": e.unit_type,
                        "brand_model": e.brand_model,
                        "install_date": e.install_date.isoformat() if e.install_date else None,
                        "notes": e.notes,
                    }
                    for e in equipment
                ],
                "maintenance_reminders": [
                    {
                        "note": m.note,
                        "remind_at_local": m.remind_at.astimezone(self._timezone).strftime("%A, %d %b %Y"),
                        "status": m.status.value,
                    }
                    for m in maintenance_reminders
                ],
            },
        )
