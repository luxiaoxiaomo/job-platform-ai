"""
WeChat service-account template-message provider.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.core.config import settings
from app.modules.notification.models import NotificationPushTask
from app.modules.notification.providers.base import PushSendResult
from app.modules.user.models import User


_TOKEN_CACHE: dict[str, Any] = {"access_token": None, "expires_at": None}


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _payload(task: NotificationPushTask) -> dict[str, Any]:
    return dict(task.payload or {})


def _notification_type(task: NotificationPushTask) -> str:
    payload = _payload(task)
    return str(payload.get("notification_type") or payload.get("type") or "default")


def _template_id_for(task: NotificationPushTask) -> str:
    type_to_attr = {
        "job_review": "WECHAT_TEMPLATE_JOB_REVIEW",
        "message": "WECHAT_TEMPLATE_MESSAGE",
        "application": "WECHAT_TEMPLATE_APPLICATION",
        "application_status": "WECHAT_TEMPLATE_APPLICATION_STATUS",
        "match": "WECHAT_TEMPLATE_MATCH",
    }
    attr = type_to_attr.get(_notification_type(task), "WECHAT_TEMPLATE_DEFAULT")
    return getattr(settings, attr, "") or settings.WECHAT_TEMPLATE_DEFAULT


def _action_url(action_url: str | None) -> str | None:
    if not action_url:
        return None
    if action_url.startswith(("http://", "https://")):
        return action_url
    base = settings.WECHAT_TEMPLATE_ACTION_BASE_URL.rstrip("/")
    if not base:
        return None
    return f"{base}/{action_url.lstrip('/')}"


def _template_data(task: NotificationPushTask) -> dict[str, Any]:
    payload = _payload(task)
    explicit = payload.get("wechat_template_data")
    if isinstance(explicit, dict) and explicit:
        return explicit
    detail = task.detail or ""
    return {
        "first": {"value": task.title},
        "keyword1": {"value": task.title[:64]},
        "keyword2": {"value": detail[:120] or "请进入平台查看详情"},
        "remark": {"value": "点击查看详情。"},
    }


class DisabledPushProvider:
    async def send(self, task: NotificationPushTask, recipient: User | None) -> PushSendResult:
        return PushSendResult(
            ok=True,
            skipped=True,
            provider="wechat_template_disabled",
            message="WeChat push is disabled; in-app notification remains available.",
        )


class WeChatDryRunProvider:
    async def send(self, task: NotificationPushTask, recipient: User | None) -> PushSendResult:
        return PushSendResult(
            ok=True,
            provider="wechat_template_dry_run",
            message="Dry run: task is ready for WeChat template delivery.",
            raw_response={
                "template_id": _template_id_for(task) or "<not-configured>",
                "openid_present": bool(recipient and recipient.wechat_openid),
                "notification_type": _notification_type(task),
            },
        )


class WeChatTemplateProvider:
    async def send(self, task: NotificationPushTask, recipient: User | None) -> PushSendResult:
        if recipient is None:
            return PushSendResult(
                ok=False,
                provider="wechat_template",
                message="Recipient not found; in-app notification remains available.",
                error_code="recipient_not_found",
            )
        if not recipient.wechat_openid:
            return PushSendResult(
                ok=False,
                provider="wechat_template",
                message="Recipient has not bound a WeChat OpenID; in-app notification remains available.",
                error_code="missing_wechat_openid",
            )
        template_id = _template_id_for(task)
        if not template_id:
            return PushSendResult(
                ok=False,
                provider="wechat_template",
                message="No WeChat template ID configured for this notification type.",
                error_code="missing_template_id",
            )
        if not settings.WECHAT_APP_ID or not settings.WECHAT_APP_SECRET:
            return PushSendResult(
                ok=False,
                provider="wechat_template",
                message="WECHAT_APP_ID or WECHAT_APP_SECRET is not configured.",
                error_code="missing_wechat_credentials",
            )

        try:
            access_token = await self._access_token()
            response = await self._send_template_message(task, recipient, access_token, template_id)
        except httpx.HTTPError as exc:
            return PushSendResult(
                ok=False,
                retryable=True,
                provider="wechat_template",
                message=str(exc)[:300],
                error_code="wechat_http_error",
            )

        errcode = int(response.get("errcode", 0) or 0)
        if errcode == 0:
            return PushSendResult(
                ok=True,
                provider="wechat_template",
                message="WeChat template message sent.",
                external_id=str(response.get("msgid") or ""),
                raw_response=response,
            )
        return PushSendResult(
            ok=False,
            retryable=errcode in {-1, 40001, 42001, 45009},
            provider="wechat_template",
            message=str(response.get("errmsg") or "WeChat API rejected the template message")[:300],
            error_code=f"wechat_{errcode}",
            raw_response=response,
        )

    async def _access_token(self) -> str:
        cached_token = _TOKEN_CACHE.get("access_token")
        expires_at = _TOKEN_CACHE.get("expires_at")
        if cached_token and isinstance(expires_at, datetime) and expires_at > _now():
            return str(cached_token)

        url = f"{settings.WECHAT_API_BASE_URL.rstrip('/')}/cgi-bin/token"
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(
                url,
                params={
                    "grant_type": "client_credential",
                    "appid": settings.WECHAT_APP_ID,
                    "secret": settings.WECHAT_APP_SECRET,
                },
            )
            response.raise_for_status()
            data = response.json()
        token = data.get("access_token")
        if not token:
            raise httpx.HTTPError(str(data))
        expires_in = int(data.get("expires_in", 7200) or 7200)
        _TOKEN_CACHE["access_token"] = token
        _TOKEN_CACHE["expires_at"] = _now() + timedelta(seconds=max(60, expires_in - 300))
        return str(token)

    async def _send_template_message(
        self,
        task: NotificationPushTask,
        recipient: User,
        access_token: str,
        template_id: str,
    ) -> dict[str, Any]:
        url = f"{settings.WECHAT_API_BASE_URL.rstrip('/')}/cgi-bin/message/template/send"
        body: dict[str, Any] = {
            "touser": recipient.wechat_openid,
            "template_id": template_id,
            "data": _template_data(task),
        }
        action_url = _action_url(task.action_url)
        if action_url:
            body["url"] = action_url
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(url, params={"access_token": access_token}, json=body)
            response.raise_for_status()
            return response.json()
