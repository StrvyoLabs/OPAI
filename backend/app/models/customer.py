import uuid

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class Customer(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "customers"

    name: Mapped[str] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    invoices: Mapped[list["Invoice"]] = relationship(back_populates="customer")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="customer")
    equipment: Mapped[list["Equipment"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    maintenance_reminders: Mapped[list["MaintenanceReminder"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )
