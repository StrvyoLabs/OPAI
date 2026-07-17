import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_invoice_service
from app.db.session import get_session
from app.models.appointment import Appointment
from app.models.customer import Customer
from app.models.equipment import Equipment
from app.models.invoice import Invoice
from app.models.maintenance_reminder import MaintenanceReminder
from app.schemas.crm import (
    AppointmentRead,
    CustomerRead,
    EquipmentRead,
    InvoiceRead,
    MaintenanceReminderRead,
)
from app.services.invoice_service import InvoiceService

router = APIRouter(tags=["crm"])


@router.get("/customers", response_model=list[CustomerRead])
async def list_customers(session: AsyncSession = Depends(get_session)) -> list[Customer]:
    result = await session.execute(select(Customer).order_by(Customer.name))
    return list(result.scalars().all())


@router.get("/invoices", response_model=list[InvoiceRead])
async def list_invoices(session: AsyncSession = Depends(get_session)) -> list[Invoice]:
    result = await session.execute(select(Invoice).order_by(Invoice.created_at.desc()))
    return list(result.scalars().all())


@router.post("/invoices/{invoice_id}/mark-paid", response_model=InvoiceRead)
async def mark_invoice_paid(
    invoice_id: uuid.UUID, invoice_service: InvoiceService = Depends(get_invoice_service)
) -> Invoice:
    try:
        return await invoice_service.mark_paid(invoice_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/appointments", response_model=list[AppointmentRead])
async def list_appointments(session: AsyncSession = Depends(get_session)) -> list[Appointment]:
    result = await session.execute(select(Appointment).order_by(Appointment.scheduled_at))
    return list(result.scalars().all())


@router.get("/equipment", response_model=list[EquipmentRead])
async def list_equipment(session: AsyncSession = Depends(get_session)) -> list[Equipment]:
    result = await session.execute(select(Equipment).order_by(Equipment.created_at.desc()))
    return list(result.scalars().all())


@router.get("/maintenance-reminders", response_model=list[MaintenanceReminderRead])
async def list_maintenance_reminders(session: AsyncSession = Depends(get_session)) -> list[MaintenanceReminder]:
    result = await session.execute(select(MaintenanceReminder).order_by(MaintenanceReminder.remind_at))
    return list(result.scalars().all())
