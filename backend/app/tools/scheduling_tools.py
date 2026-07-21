import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.services.appointment_service import AppointmentService
from app.services.crm_service import CRMService, CustomerNotFoundError
from app.services.invoice_service import InvoiceService
from app.services.reminder_service import ReminderService
from app.tools.base import ToolAdapter, ToolResult

logger = logging.getLogger(__name__)


class CreateAppointmentTool(ToolAdapter):
    name = "create_appointment"
    description = (
        "Schedule an appointment/event on the internal calendar for a customer. "
        "'scheduled_at' must be an ISO 8601 datetime, resolved from the current date given in the prompt."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "customer_name": {"type": "string"},
            "title": {"type": "string"},
            "scheduled_at": {"type": "string", "description": "ISO 8601 datetime, e.g. 2026-07-24T14:00:00"},
            "location": {"type": "string"},
        },
        "required": ["customer_name", "title", "scheduled_at"],
    }

    def __init__(
        self, crm_service: CRMService, appointment_service: AppointmentService, business_timezone: str
    ) -> None:
        self._crm_service = crm_service
        self._appointment_service = appointment_service
        self._timezone = ZoneInfo(business_timezone)

    async def execute(self, tool_input: dict) -> ToolResult:
        customer_name = tool_input.get("customer_name")
        title = tool_input.get("title")
        scheduled_at_raw = tool_input.get("scheduled_at")
        if not customer_name or not title or not scheduled_at_raw:
            return ToolResult(success=False, error="'customer_name', 'title' and 'scheduled_at' are required")

        try:
            scheduled_at = datetime.fromisoformat(scheduled_at_raw)
            if scheduled_at.tzinfo is None:
                scheduled_at = scheduled_at.replace(tzinfo=self._timezone)
        except ValueError as exc:
            return ToolResult(success=False, error=f"Invalid scheduled_at: {exc}")

        try:
            customer = await self._crm_service.find_or_create(name=customer_name)
            appointment = await self._appointment_service.create(
                customer_id=customer.id,
                title=title,
                scheduled_at=scheduled_at,
                location=tool_input.get("location"),
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("create_appointment failed")
            return ToolResult(success=False, error=str(exc))

        return ToolResult(
            success=True,
            output={
                "appointment_id": str(appointment.id),
                "title": appointment.title,
                # Pre-localized on purpose: this result feeds the WhatsApp
                # reply composer, which reads times as plain text -- a raw
                # UTC ISO string gets its hour read literally (e.g. "11:00
                # am" instead of "4:30 pm" for an 11:00 UTC / IST+5:30
                # appointment), so give it the only string it needs.
                "scheduled_at_local": appointment.scheduled_at.astimezone(self._timezone).strftime(
                    "%A, %d %b %Y at %I:%M %p"
                ),
            },
        )


class CreatePaymentReminderTool(ToolAdapter):
    name = "create_payment_reminder"
    description = (
        "Schedule a reminder to the owner if a customer's most recent pending invoice "
        "hasn't been paid by the given number of days from now."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "customer_name": {"type": "string"},
            "owner_phone": {
                "type": "string",
                "description": "The owner's own phone number (from the 'Owner phone' context), not the customer's.",
            },
            "days": {"type": "integer", "description": "Number of days from now to send the reminder."},
        },
        "required": ["customer_name", "owner_phone", "days"],
    }

    def __init__(
        self,
        crm_service: CRMService,
        invoice_service: InvoiceService,
        reminder_service: ReminderService,
        business_timezone: str,
    ) -> None:
        self._crm_service = crm_service
        self._invoice_service = invoice_service
        self._reminder_service = reminder_service
        self._timezone = ZoneInfo(business_timezone)

    async def execute(self, tool_input: dict) -> ToolResult:
        customer_name = tool_input.get("customer_name")
        owner_phone = tool_input.get("owner_phone")
        days = tool_input.get("days")
        if not customer_name or not owner_phone or days is None:
            return ToolResult(success=False, error="'customer_name', 'owner_phone' and 'days' are required")

        try:
            customer = await self._crm_service.find(customer_name)
        except CustomerNotFoundError as exc:
            return ToolResult(success=False, error=str(exc))

        invoice = await self._invoice_service.most_recent_pending_for_customer(customer.id)
        if invoice is None:
            return ToolResult(
                success=False, error=f"No pending invoice found for customer '{customer_name}' to remind about"
            )

        remind_at = datetime.now(timezone.utc) + timedelta(days=int(days))
        reminder = await self._reminder_service.create(
            invoice_id=invoice.id, owner_phone=owner_phone, remind_at=remind_at
        )

        return ToolResult(
            success=True,
            output={
                "reminder_id": str(reminder.id),
                "invoice_number": invoice.invoice_number,
                # Pre-localized -- see the comment in CreateAppointmentTool.
                "remind_at_local": remind_at.astimezone(self._timezone).strftime("%A, %d %b %Y"),
            },
        )
