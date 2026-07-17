import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class ReminderStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    CANCELLED = "cancelled"


class PaymentReminder(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "payment_reminders"

    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), index=True)
    owner_phone: Mapped[str] = mapped_column(String(32))
    remind_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[ReminderStatus] = mapped_column(
        Enum(ReminderStatus, name="reminder_status", values_callable=lambda enum: [m.value for m in enum]),
        default=ReminderStatus.PENDING,
        index=True,
    )

    invoice: Mapped["Invoice"] = relationship(back_populates="reminders")
