"""add notification push tasks

Revision ID: r7a9c0d2e506
Revises: q6f8a0b1c405
Create Date: 2026-06-19 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "r7a9c0d2e506"
down_revision: Union[str, None] = "q6f8a0b1c405"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notification_push_tasks",
        sa.Column("id", sa.Integer(), nullable=False, comment="Push task ID"),
        sa.Column("notification_id", sa.Integer(), nullable=False, comment="Notification ID"),
        sa.Column("recipient_id", sa.Integer(), nullable=False, comment="Recipient user ID"),
        sa.Column("channel", sa.String(length=50), nullable=False, server_default="wechat_template", comment="Push channel"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending", comment="pending/deferred/digest_placeholder/sent/failed"),
        sa.Column("title", sa.String(length=200), nullable=False, comment="Push title"),
        sa.Column("detail", sa.Text(), nullable=True, comment="Push detail"),
        sa.Column("action_url", sa.String(length=500), nullable=True, comment="Frontend action URL"),
        sa.Column("payload", sa.JSON(), nullable=True, comment="Structured push payload"),
        sa.Column("scheduled_at", sa.DateTime(), nullable=False, comment="Scheduled push time"),
        sa.Column("send_window_start", sa.String(length=5), nullable=False, server_default="08:00", comment="Daily send window start"),
        sa.Column("send_window_end", sa.String(length=5), nullable=False, server_default="21:00", comment="Daily send window end"),
        sa.Column("daily_sequence", sa.Integer(), nullable=True, comment="Immediate push sequence in recipient day"),
        sa.Column("reason", sa.String(length=100), nullable=True, comment="Scheduling reason"),
        sa.Column("dedupe_key", sa.String(length=240), nullable=True, comment="Idempotency key for push task"),
        sa.Column("sent_at", sa.DateTime(), nullable=True, comment="Sent at"),
        sa.Column("failed_at", sa.DateTime(), nullable=True, comment="Failed at"),
        sa.Column("error_message", sa.Text(), nullable=True, comment="Failure message"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Created at"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Updated at"),
        sa.ForeignKeyConstraint(["notification_id"], ["notifications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipient_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("recipient_id", "dedupe_key", name="uq_notification_push_recipient_dedupe"),
    )
    op.create_index("idx_notification_push_notification", "notification_push_tasks", ["notification_id"])
    op.create_index("idx_notification_push_recipient_scheduled", "notification_push_tasks", ["recipient_id", "scheduled_at"])
    op.create_index("idx_notification_push_status_scheduled", "notification_push_tasks", ["status", "scheduled_at"])


def downgrade() -> None:
    op.drop_index("idx_notification_push_status_scheduled", table_name="notification_push_tasks")
    op.drop_index("idx_notification_push_recipient_scheduled", table_name="notification_push_tasks")
    op.drop_index("idx_notification_push_notification", table_name="notification_push_tasks")
    op.drop_table("notification_push_tasks")
