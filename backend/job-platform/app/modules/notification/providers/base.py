"""
Provider contract for external notification delivery.
"""
from dataclasses import dataclass, field
from typing import Any, Protocol

from app.modules.notification.models import NotificationPushTask
from app.modules.user.models import User


@dataclass
class PushSendResult:
    ok: bool
    provider: str
    message: str
    skipped: bool = False
    retryable: bool = False
    error_code: str | None = None
    external_id: str | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)


class NotificationPushProvider(Protocol):
    async def send(self, task: NotificationPushTask, recipient: User | None) -> PushSendResult:
        """Send or intentionally skip one external push task."""
