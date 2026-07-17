import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class MaintenanceReminderStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    CANCELLED = "cancelled"


class MaintenanceReminder(UUIDPKMixin, TimestampMixin, Base):
    """A recurring/follow-up reminder unrelated to payment -- e.g. "reach out
    to this customer in 6 months for seasonal servicing"."""

    __tablename__ = "maintenance_reminders"

    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    owner_phone: Mapped[str] = mapped_column(String(32))
    note: Mapped[str] = mapped_column(Text)
    remind_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[MaintenanceReminderStatus] = mapped_column(
        Enum(
            MaintenanceReminderStatus,
            name="maintenance_reminder_status",
            values_callable=lambda enum: [m.value for m in enum],
        ),
        default=MaintenanceReminderStatus.PENDING,
        index=True,
    )

    customer: Mapped["Customer"] = relationship(back_populates="maintenance_reminders")
