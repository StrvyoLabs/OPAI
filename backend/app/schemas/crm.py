import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.invoice import InvoiceStatus
from app.models.maintenance_reminder import MaintenanceReminderStatus


class CustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    phone: str | None
    email: str | None
    notes: str | None
    created_at: datetime


class InvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    invoice_number: str
    customer_id: uuid.UUID
    description: str
    amount: float
    currency_symbol: str
    status: InvoiceStatus
    file_url: str | None
    created_at: datetime


class AppointmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    customer_id: uuid.UUID | None
    title: str
    scheduled_at: datetime
    location: str | None
    created_at: datetime


class EquipmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    customer_id: uuid.UUID
    unit_type: str
    brand_model: str | None
    install_date: date | None
    notes: str | None
    created_at: datetime


class MaintenanceReminderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    customer_id: uuid.UUID
    note: str
    remind_at: datetime
    status: MaintenanceReminderStatus
    created_at: datetime
