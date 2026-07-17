import enum
import uuid

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class TaskStatus(str, enum.Enum):
    RECEIVED = "received"
    PLANNING = "planning"
    PLANNED = "planned"
    EXECUTING = "executing"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"


class Task(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "tasks"

    owner_phone: Mapped[str] = mapped_column(String(32), index=True)
    raw_request: Mapped[str] = mapped_column(Text)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status", values_callable=lambda enum: [member.value for member in enum]),
        default=TaskStatus.RECEIVED,
        index=True,
    )
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    plans: Mapped[list["Plan"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    messages: Mapped[list["WhatsAppMessage"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    activity_events: Mapped[list["ActivityEvent"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
