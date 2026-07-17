import enum
import uuid
from typing import Any

from sqlalchemy import Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class PlanStepStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class Plan(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "plans"

    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    model_used: Mapped[str] = mapped_column(String(128))
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_response: Mapped[dict[str, Any]] = mapped_column(JSON)

    task: Mapped["Task"] = relationship(back_populates="plans")
    steps: Mapped[list["PlanStep"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan", order_by="PlanStep.step_number"
    )


class PlanStep(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "plan_steps"

    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("plans.id", ondelete="CASCADE"), index=True)
    step_number: Mapped[int] = mapped_column(Integer)
    tool_name: Mapped[str] = mapped_column(String(128))
    tool_input: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[PlanStepStatus] = mapped_column(
        Enum(
            PlanStepStatus,
            name="plan_step_status",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=PlanStepStatus.PENDING,
    )
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    plan: Mapped["Plan"] = relationship(back_populates="steps")
