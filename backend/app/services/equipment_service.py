import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.equipment import Equipment


class EquipmentService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def add(
        self,
        *,
        customer_id: uuid.UUID,
        unit_type: str,
        brand_model: str | None,
        install_date: date | None,
        notes: str | None,
    ) -> Equipment:
        async with self._session_factory() as session:
            equipment = Equipment(
                customer_id=customer_id,
                unit_type=unit_type,
                brand_model=brand_model,
                install_date=install_date,
                notes=notes,
            )
            session.add(equipment)
            await session.commit()
            await session.refresh(equipment)
            return equipment

    async def list_for_customer(self, customer_id: uuid.UUID) -> list[Equipment]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(Equipment)
                .where(Equipment.customer_id == customer_id)
                .order_by(Equipment.created_at)
            )
            return list(result.scalars().all())

    async def list_all(self) -> list[Equipment]:
        async with self._session_factory() as session:
            result = await session.execute(select(Equipment).order_by(Equipment.created_at.desc()))
            return list(result.scalars().all())
