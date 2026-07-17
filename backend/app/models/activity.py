import enum
import uuid
from typing import Any

from sqlalchemy import Enum, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class ActivityType(str, enum.Enum):
    MESSAGE_RECEIVED = "message_received"
    MESSAGE_SENT = "message_sent"
    PLANNING_STARTED = "planning_started"
    PLAN_CREATED = "plan_created"
    PLAN_FAILED = "plan_failed"
    STEP_STARTED = "step_started"
    STEP_SUCCEEDED = "step_succeeded"
    STEP_FAILED = "step_failed"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"


class ActivityEvent(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "activity_events"

    task_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True, index=True
    )
    type: Mapped[ActivityType] = mapped_column(
        Enum(ActivityType, name="activity_type", values_callable=lambda enum: [member.value for member in enum]),
        index=True,
    )
    message: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    task: Mapped["Task"] = relationship(back_populates="activity_events")
