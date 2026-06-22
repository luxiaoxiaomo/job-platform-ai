"""add notifications

Revision ID: q6f8a0b1c405
Revises: p5e7f9a1b304
Create Date: 2026-06-19 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "q6f8a0b1c405"
down_revision: Union[str, None] = "p5e7f9a1b304"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False, comment="Notification ID"),
        sa.Column("recipient_id", sa.Integer(), nullable=False, comment="Recipient user ID"),
        sa.Column("type", sa.String(length=50), nullable=False, comment="Notification type"),
        sa.Column("title", sa.String(length=200), nullable=False, comment="Notification title"),
        sa.Column("detail", sa.Text(), nullable=True, comment="Notification detail"),
        sa.Column("action_url", sa.String(length=500), nullable=True, comment="Frontend action URL"),
        sa.Column("payload", sa.JSON(), nullable=True, comment="Structured notification payload"),
        sa.Column("dedupe_key", sa.String(length=200), nullable=True, comment="Idempotency key for generated notifications"),
        sa.Column("read_at", sa.DateTime(), nullable=True, comment="Read at"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Created at"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Updated at"),
        sa.ForeignKeyConstraint(["recipient_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("recipient_id", "dedupe_key", name="uq_notifications_recipient_dedupe"),
    )
    op.create_index("idx_notifications_recipient_created", "notifications", ["recipient_id", "created_at"])
    op.create_index("idx_notifications_recipient_read", "notifications", ["recipient_id", "read_at"])
    op.create_index("idx_notifications_type", "notifications", ["type"])


def downgrade() -> None:
    op.drop_index("idx_notifications_type", table_name="notifications")
    op.drop_index("idx_notifications_recipient_read", table_name="notifications")
    op.drop_index("idx_notifications_recipient_created", table_name="notifications")
    op.drop_table("notifications")
