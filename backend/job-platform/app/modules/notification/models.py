"""
Notification data model.
"""
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Notification(Base):
    """A persisted in-app notification for one user."""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, comment="Notification ID")
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="Recipient user ID")
    type = Column(String(50), nullable=False, comment="Notification type")
    title = Column(String(200), nullable=False, comment="Notification title")
    detail = Column(Text, nullable=True, comment="Notification detail")
    action_url = Column(String(500), nullable=True, comment="Frontend action URL")
    payload = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True, comment="Structured notification payload")
    dedupe_key = Column(String(200), nullable=True, comment="Idempotency key for generated notifications")
    read_at = Column(DateTime, nullable=True, comment="Read at")
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="Created at")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="Updated at")

    recipient = relationship("User")

    __table_args__ = (
        UniqueConstraint("recipient_id", "dedupe_key", name="uq_notifications_recipient_dedupe"),
        Index("idx_notifications_recipient_created", "recipient_id", "created_at"),
        Index("idx_notifications_recipient_read", "recipient_id", "read_at"),
        Index("idx_notifications_type", "type"),
    )


class NotificationPushTask(Base):
    """A queued external push task derived from an in-app notification."""

    __tablename__ = "notification_push_tasks"

    id = Column(Integer, primary_key=True, index=True, comment="Push task ID")
    notification_id = Column(Integer, ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False, comment="Notification ID")
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="Recipient user ID")
    channel = Column(String(50), nullable=False, default="wechat_template", comment="Push channel")
    status = Column(String(50), nullable=False, default="pending", comment="pending/deferred/digest_placeholder/sent/failed")
    title = Column(String(200), nullable=False, comment="Push title")
    detail = Column(Text, nullable=True, comment="Push detail")
    action_url = Column(String(500), nullable=True, comment="Frontend action URL")
    payload = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True, comment="Structured push payload")
    scheduled_at = Column(DateTime, nullable=False, comment="Scheduled push time")
    send_window_start = Column(String(5), nullable=False, default="08:00", comment="Daily send window start")
    send_window_end = Column(String(5), nullable=False, default="21:00", comment="Daily send window end")
    daily_sequence = Column(Integer, nullable=True, comment="Immediate push sequence in recipient day")
    reason = Column(String(100), nullable=True, comment="Scheduling reason")
    dedupe_key = Column(String(240), nullable=True, comment="Idempotency key for push task")
    attempt_count = Column(Integer, nullable=False, default=0, server_default="0", comment="External provider attempt count")
    sent_at = Column(DateTime, nullable=True, comment="Sent at")
    failed_at = Column(DateTime, nullable=True, comment="Failed at")
    error_message = Column(Text, nullable=True, comment="Failure message")
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="Created at")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="Updated at")

    notification = relationship("Notification")
    recipient = relationship("User")

    __table_args__ = (
        UniqueConstraint("recipient_id", "dedupe_key", name="uq_notification_push_recipient_dedupe"),
        Index("idx_notification_push_recipient_scheduled", "recipient_id", "scheduled_at"),
        Index("idx_notification_push_status_scheduled", "status", "scheduled_at"),
        Index("idx_notification_push_notification", "notification_id"),
    )
