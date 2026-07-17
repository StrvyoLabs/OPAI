import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.maintenance_reminder import MaintenanceReminder, MaintenanceReminderStatus


class MaintenanceReminderService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(
        self, *, customer_id: uuid.UUID, owner_phone: str, note: str, remind_at: datetime
    ) -> MaintenanceReminder:
        async with self._session_factory() as session:
            reminder = MaintenanceReminder(
                customer_id=customer_id, owner_phone=owner_phone, note=note, remind_at=remind_at
            )
            session.add(reminder)
            await session.commit()
            await session.refresh(reminder)
            return reminder

    async def due_reminders(self, *, as_of: datetime) -> list[MaintenanceReminder]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(MaintenanceReminder).where(
                    MaintenanceReminder.status == MaintenanceReminderStatus.PENDING,
                    MaintenanceReminder.remind_at <= as_of,
                )
            )
            return list(result.scalars().all())

    async def mark_sent(self, reminder_id: uuid.UUID) -> None:
        async with self._session_factory() as session:
            reminder = await session.get(MaintenanceReminder, reminder_id)
            if reminder is not None:
                reminder.status = MaintenanceReminderStatus.SENT
                await session.commit()

    async def list_for_customer(self, customer_id: uuid.UUID) -> list[MaintenanceReminder]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(MaintenanceReminder)
                .where(MaintenanceReminder.customer_id == customer_id)
                .order_by(MaintenanceReminder.remind_at)
            )
            return list(result.scalars().all())
