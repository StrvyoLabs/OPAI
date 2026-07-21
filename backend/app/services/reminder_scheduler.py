import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.customer import Customer
from app.models.invoice import Invoice, InvoiceStatus
from app.models.maintenance_reminder import MaintenanceReminder, MaintenanceReminderStatus
from app.models.reminder import PaymentReminder, ReminderStatus
from app.services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)


class ReminderScheduler:
    """Polls for due payment and maintenance reminders and nudges the owner
    over WhatsApp. Runs as a background task for the lifetime of the app --
    no external cron needed for a single-process deployment.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        whatsapp_service: WhatsAppService,
        poll_interval_seconds: int = 300,
    ) -> None:
        self._session_factory = session_factory
        self._whatsapp_service = whatsapp_service
        self._poll_interval_seconds = poll_interval_seconds

    async def run_forever(self) -> None:
        while True:
            try:
                await self._process_due_payment_reminders()
                await self._process_due_maintenance_reminders()
            except Exception:  # noqa: BLE001 - keep the loop alive regardless
                logger.exception("Reminder scheduler tick failed")
            await asyncio.sleep(self._poll_interval_seconds)

    async def _process_due_payment_reminders(self) -> None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(PaymentReminder).where(
                    PaymentReminder.status == ReminderStatus.PENDING,
                    PaymentReminder.remind_at <= datetime.now(timezone.utc),
                )
            )
            due = list(result.scalars().all())

            for reminder in due:
                invoice = await session.get(Invoice, reminder.invoice_id)
                if invoice is not None and invoice.status == InvoiceStatus.PENDING:
                    body = (
                        f"Reminder: invoice {invoice.invoice_number} for "
                        f"{invoice.currency_symbol}{invoice.amount:,.2f} is still unpaid."
                    )
                    try:
                        await self._whatsapp_service.send_message(to=reminder.owner_phone, body=body)
                    except Exception:  # noqa: BLE001
                        logger.exception("Failed to send payment reminder for invoice %s", invoice.invoice_number)

                reminder.status = ReminderStatus.SENT

            if due:
                await session.commit()

    async def _process_due_maintenance_reminders(self) -> None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(MaintenanceReminder).where(
                    MaintenanceReminder.status == MaintenanceReminderStatus.PENDING,
                    MaintenanceReminder.remind_at <= datetime.now(timezone.utc),
                )
            )
            due = list(result.scalars().all())

            for reminder in due:
                customer = await session.get(Customer, reminder.customer_id)
                customer_name = customer.name if customer is not None else "a customer"
                body = f"Reminder for {customer_name}: {reminder.note}"
                try:
                    await self._whatsapp_service.send_message(to=reminder.owner_phone, body=body)
                except Exception:  # noqa: BLE001
                    logger.exception("Failed to send maintenance reminder %s", reminder.id)

                reminder.status = MaintenanceReminderStatus.SENT

            if due:
                await session.commit()
