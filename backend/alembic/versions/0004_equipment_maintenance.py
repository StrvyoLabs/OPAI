"""equipment and maintenance reminders

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

maintenance_reminder_status = sa.Enum(
    "pending", "sent", "cancelled", name="maintenance_reminder_status"
)


def upgrade() -> None:
    op.create_table(
        "equipment",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("unit_type", sa.String(length=255), nullable=False),
        sa.Column("brand_model", sa.String(length=255), nullable=True),
        sa.Column("install_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_equipment_customer_id", "equipment", ["customer_id"])

    op.create_table(
        "maintenance_reminders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("owner_phone", sa.String(length=32), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("remind_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", maintenance_reminder_status, nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_maintenance_reminders_customer_id", "maintenance_reminders", ["customer_id"])
    op.create_index("ix_maintenance_reminders_remind_at", "maintenance_reminders", ["remind_at"])
    op.create_index("ix_maintenance_reminders_status", "maintenance_reminders", ["status"])


def downgrade() -> None:
    op.drop_table("maintenance_reminders")
    op.drop_table("equipment")

    bind = op.get_bind()
    maintenance_reminder_status.drop(bind, checkfirst=True)
