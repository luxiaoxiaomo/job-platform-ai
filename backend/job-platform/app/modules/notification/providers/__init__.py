"""
External notification push providers.
"""
from app.core.config import settings
from app.modules.notification.providers.base import NotificationPushProvider
from app.modules.notification.providers.wechat import (
    DisabledPushProvider,
    WeChatDryRunProvider,
    WeChatTemplateProvider,
)


def get_notification_push_provider() -> NotificationPushProvider:
    mode = settings.WECHAT_PUSH_MODE.strip().lower()
    if mode == "live":
        return WeChatTemplateProvider()
    if mode == "disabled":
        return DisabledPushProvider()
    return WeChatDryRunProvider()
