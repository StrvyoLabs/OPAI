import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.reminder import PaymentReminder, ReminderStatus


class ReminderService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(self, *, invoice_id: uuid.UUID, owner_phone: str, remind_at: datetime) -> PaymentReminder:
        async with self._session_factory() as session:
            reminder = PaymentReminder(invoice_id=invoice_id, owner_phone=owner_phone, remind_at=remind_at)
            session.add(reminder)
            await session.commit()
            await session.refresh(reminder)
            return reminder

    async def due_reminders(self, *, as_of: datetime) -> list[PaymentReminder]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(PaymentReminder).where(
                    PaymentReminder.status == ReminderStatus.PENDING,
                    PaymentReminder.remind_at <= as_of,
                )
            )
            return list(result.scalars().all())

    async def mark_sent(self, reminder_id: uuid.UUID) -> None:
        async with self._session_factory() as session:
            reminder = await session.get(PaymentReminder, reminder_id)
            if reminder is not None:
                reminder.status = ReminderStatus.SENT
                await session.commit()
