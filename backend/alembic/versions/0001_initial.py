"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

task_status = sa.Enum(
    "received",
    "planning",
    "planned",
    "executing",
    "completed",
    "failed",
    name="task_status",
)
plan_step_status = sa.Enum(
    "pending",
    "running",
    "succeeded",
    "failed",
    "skipped",
    name="plan_step_status",
)
activity_type = sa.Enum(
    "message_received",
    "message_sent",
    "planning_started",
    "plan_created",
    "plan_failed",
    "step_started",
    "step_succeeded",
    "step_failed",
    "task_completed",
    "task_failed",
    name="activity_type",
)
message_direction = sa.Enum("inbound", "outbound", name="message_direction")


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("owner_phone", sa.String(length=32), nullable=False),
        sa.Column("raw_request", sa.Text(), nullable=False),
        sa.Column("status", task_status, nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tasks_owner_phone", "tasks", ["owner_phone"])
    op.create_index("ix_tasks_status", "tasks", ["status"])

    op.create_table(
        "plans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("model_used", sa.String(length=128), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("raw_response", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_plans_task_id", "plans", ["task_id"])

    op.create_table(
        "plan_steps",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("tool_name", sa.String(length=128), nullable=False),
        sa.Column("tool_input", sa.JSON(), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("status", plan_step_status, nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_plan_steps_plan_id", "plan_steps", ["plan_id"])

    op.create_table(
        "activity_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=True),
        sa.Column("type", activity_type, nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_activity_events_task_id", "activity_events", ["task_id"])
    op.create_index("ix_activity_events_type", "activity_events", ["type"])

    op.create_table(
        "whatsapp_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=True),
        sa.Column("direction", message_direction, nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("wa_message_id", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_whatsapp_messages_task_id", "whatsapp_messages", ["task_id"])
    op.create_index("ix_whatsapp_messages_phone", "whatsapp_messages", ["phone"])


def downgrade() -> None:
    op.drop_table("whatsapp_messages")
    op.drop_table("activity_events")
    op.drop_table("plan_steps")
    op.drop_table("plans")
    op.drop_table("tasks")

    bind = op.get_bind()
    message_direction.drop(bind, checkfirst=True)
    activity_type.drop(bind, checkfirst=True)
    plan_step_status.drop(bind, checkfirst=True)
    task_status.drop(bind, checkfirst=True)
