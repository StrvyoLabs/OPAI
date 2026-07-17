import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.invoice import Invoice, InvoiceStatus


class InvoiceService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(
        self,
        *,
        invoice_number: str,
        customer_id: uuid.UUID,
        description: str,
        amount: float,
        currency_symbol: str,
        file_url: str,
    ) -> Invoice:
        async with self._session_factory() as session:
            invoice = Invoice(
                invoice_number=invoice_number,
                customer_id=customer_id,
                description=description,
                amount=amount,
                currency_symbol=currency_symbol,
                status=InvoiceStatus.PENDING,
                file_url=file_url,
            )
            session.add(invoice)
            await session.commit()
            await session.refresh(invoice)
            return invoice

    async def most_recent_pending_for_customer(self, customer_id: uuid.UUID) -> Invoice | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(Invoice)
                .where(Invoice.customer_id == customer_id, Invoice.status == InvoiceStatus.PENDING)
                .order_by(Invoice.created_at.desc())
            )
            return result.scalars().first()

    async def list_invoices(self) -> list[Invoice]:
        async with self._session_factory() as session:
            result = await session.execute(select(Invoice).order_by(Invoice.created_at.desc()))
            return list(result.scalars().all())

    async def list_for_customer(self, customer_id: uuid.UUID) -> list[Invoice]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(Invoice)
                .where(Invoice.customer_id == customer_id)
                .order_by(Invoice.created_at.desc())
            )
            return list(result.scalars().all())

    async def find_by_number(self, invoice_number: str) -> Invoice | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(Invoice).where(Invoice.invoice_number == invoice_number)
            )
            return result.scalars().first()

    async def mark_paid(self, invoice_id: uuid.UUID) -> Invoice:
        async with self._session_factory() as session:
            invoice = await session.get(Invoice, invoice_id)
            if invoice is None:
                raise ValueError(f"No invoice with id {invoice_id}")
            invoice.status = InvoiceStatus.PAID
            await session.commit()
            await session.refresh(invoice)
            return invoice
