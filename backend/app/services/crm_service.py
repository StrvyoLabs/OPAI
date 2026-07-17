from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.customer import Customer


class CustomerNotFoundError(Exception):
    pass


class CRMService:
    """Owns customer lookup/creation. Tools that need a customer (invoices,
    appointments, reminders) go through this instead of talking to the
    Customer model directly, so lookup rules stay in one place.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def find_or_create(
        self, name: str, phone: str | None = None, email: str | None = None
    ) -> Customer:
        async with self._session_factory() as session:
            customer = await self._find(session, name)
            if customer is None:
                customer = Customer(name=name, phone=phone, email=email)
                session.add(customer)
            else:
                if phone and not customer.phone:
                    customer.phone = phone
                if email and not customer.email:
                    customer.email = email
            await session.commit()
            await session.refresh(customer)
            return customer

    async def find(self, name: str) -> Customer:
        async with self._session_factory() as session:
            customer = await self._find(session, name)
            if customer is None:
                raise CustomerNotFoundError(f"No customer found matching '{name}'")
            return customer

    async def _find(self, session: AsyncSession, name: str) -> Customer | None:
        result = await session.execute(
            select(Customer).where(Customer.name.ilike(name.strip())).order_by(Customer.created_at.desc())
        )
        customer = result.scalars().first()
        if customer is not None:
            return customer

        result = await session.execute(
            select(Customer).where(Customer.name.ilike(f"%{name.strip()}%")).order_by(Customer.created_at.desc())
        )
        return result.scalars().first()

    async def list_customers(self) -> list[Customer]:
        async with self._session_factory() as session:
            result = await session.execute(select(Customer).order_by(Customer.name))
            return list(result.scalars().all())
