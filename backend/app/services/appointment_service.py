import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.appointment import Appointment


class AppointmentService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(
        self,
        *,
        customer_id: uuid.UUID | None,
        title: str,
        scheduled_at: datetime,
        location: str | None,
    ) -> Appointment:
        async with self._session_factory() as session:
            appointment = Appointment(
                customer_id=customer_id, title=title, scheduled_at=scheduled_at, location=location
            )
            session.add(appointment)
            await session.commit()
            await session.refresh(appointment)
            return appointment

    async def list_appointments(self) -> list[Appointment]:
        async with self._session_factory() as session:
            result = await session.execute(select(Appointment).order_by(Appointment.scheduled_at))
            return list(result.scalars().all())

    async def list_for_customer(self, customer_id: uuid.UUID) -> list[Appointment]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(Appointment)
                .where(Appointment.customer_id == customer_id)
                .order_by(Appointment.scheduled_at)
            )
            return list(result.scalars().all())
