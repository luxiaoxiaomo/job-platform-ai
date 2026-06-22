"""
Notification schemas.
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class NotificationResponse(BaseModel):
    id: int
    type: str
    title: str
    detail: Optional[str] = None
    action_url: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)
    read: bool = False
    read_at: Optional[datetime] = None
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    unread_count: int
    skip: int
    limit: int


class NotificationUnreadCountResponse(BaseModel):
    unread_count: int


class NotificationMarkReadResponse(BaseModel):
    ok: bool
    unread_count: int


class NotificationPushTaskResponse(BaseModel):
    id: int
    notification_id: int
    recipient_id: int
    channel: str
    status: str
    title: str
    detail: Optional[str] = None
    action_url: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)
    scheduled_at: datetime
    send_window_start: str
    send_window_end: str
    daily_sequence: Optional[int] = None
    reason: Optional[str] = None
    dedupe_key: Optional[str] = None
    attempt_count: int = 0
    sent_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime


class NotificationPushTaskListResponse(BaseModel):
    items: list[NotificationPushTaskResponse]
    total: int
    skip: int
    limit: int


class NotificationPushTaskStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(sent|failed)$")
    error_message: Optional[str] = Field(None, max_length=500)


class NotificationPushWorkerRunResponse(BaseModel):
    processed_count: int = 0
    sent_count: int = 0
    digest_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    items: list[NotificationPushTaskResponse] = Field(default_factory=list)
