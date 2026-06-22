"""
Notification business logic.
"""
from datetime import datetime, time, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notification.models import Notification, NotificationPushTask
from app.modules.notification.providers import get_notification_push_provider
from app.modules.notification.providers.base import PushSendResult
from app.modules.notification.repository import NotificationRepository
from app.modules.notification.schemas import (
    NotificationListResponse,
    NotificationMarkReadResponse,
    NotificationPushTaskListResponse,
    NotificationPushTaskResponse,
    NotificationPushWorkerRunResponse,
    NotificationPushTaskStatusUpdate,
    NotificationResponse,
    NotificationUnreadCountResponse,
)
from app.modules.user.models import User
from app.modules.user.repository import UserRepository


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _to_response(notification: Notification) -> NotificationResponse:
    return NotificationResponse(
        id=notification.id,
        type=notification.type,
        title=notification.title,
        detail=notification.detail,
        action_url=notification.action_url,
        payload=notification.payload or {},
        read=notification.read_at is not None,
        read_at=notification.read_at,
        created_at=notification.created_at,
    )


def _to_push_response(task: NotificationPushTask) -> NotificationPushTaskResponse:
    return NotificationPushTaskResponse(
        id=task.id,
        notification_id=task.notification_id,
        recipient_id=task.recipient_id,
        channel=task.channel,
        status=task.status,
        title=task.title,
        detail=task.detail,
        action_url=task.action_url,
        payload=task.payload or {},
        scheduled_at=task.scheduled_at,
        send_window_start=task.send_window_start,
        send_window_end=task.send_window_end,
        daily_sequence=task.daily_sequence,
        reason=task.reason,
        dedupe_key=task.dedupe_key,
        attempt_count=task.attempt_count or 0,
        sent_at=task.sent_at,
        failed_at=task.failed_at,
        error_message=task.error_message,
        created_at=task.created_at,
    )


class NotificationService:
    SEND_WINDOW_START = time(hour=8)
    SEND_WINDOW_END = time(hour=21)
    SEND_WINDOW_START_TEXT = "08:00"
    SEND_WINDOW_END_TEXT = "21:00"
    DAILY_IMMEDIATE_LIMIT = 5
    MAX_PROVIDER_ATTEMPTS = 3
    EXTERNAL_PUSH_TYPES = {
        "match",
        "job_review",
        "message",
        "application",
        "application_status",
    }

    @staticmethod
    def _push_now() -> datetime:
        return _now()

    @staticmethod
    def _day_bounds(moment: datetime) -> tuple[datetime, datetime]:
        day_start = datetime.combine(moment.date(), time.min)
        return day_start, day_start + timedelta(days=1)

    @staticmethod
    def _next_window_start(moment: datetime) -> datetime:
        today_start = datetime.combine(moment.date(), NotificationService.SEND_WINDOW_START)
        today_end = datetime.combine(moment.date(), NotificationService.SEND_WINDOW_END)
        if moment < today_start:
            return today_start
        if moment >= today_end:
            return today_start + timedelta(days=1)
        return moment

    @staticmethod
    async def _schedule_push_task(
        db: AsyncSession,
        *,
        recipient_id: int,
        notification: Notification,
        now: datetime,
    ) -> tuple[str, datetime, int | None, str]:
        scheduled_at = NotificationService._next_window_start(now)
        in_window = scheduled_at == now
        day_start, day_end = NotificationService._day_bounds(scheduled_at)
        immediate_count = await NotificationRepository.count_immediate_pushes_for_day(
            db,
            recipient_id=recipient_id,
            day_start=day_start,
            day_end=day_end,
        )
        if in_window and immediate_count < NotificationService.DAILY_IMMEDIATE_LIMIT:
            return "pending", scheduled_at, immediate_count + 1, "within_window"
        if in_window:
            return "digest_placeholder", day_end + timedelta(hours=8), None, "daily_limit_exceeded"
        return "deferred", scheduled_at, None, "outside_send_window"

    @staticmethod
    async def _sync_push_task(
        db: AsyncSession,
        notification: Notification,
        *,
        commit: bool = True,
    ) -> NotificationPushTask | None:
        if notification.type not in NotificationService.EXTERNAL_PUSH_TYPES:
            return None
        if notification.id is None:
            await db.flush()

        dedupe_key = f"push:{notification.id}:{notification.type}"
        existing = await NotificationRepository.get_push_by_dedupe_key(
            db,
            recipient_id=notification.recipient_id,
            dedupe_key=dedupe_key,
        )
        now = NotificationService._push_now()
        payload = dict(notification.payload or {})
        payload["notification_type"] = notification.type
        if existing is not None:
            existing.channel = "wechat_template"
            existing.title = notification.title
            existing.detail = notification.detail
            existing.action_url = notification.action_url
            existing.payload = payload
            existing.send_window_start = NotificationService.SEND_WINDOW_START_TEXT
            existing.send_window_end = NotificationService.SEND_WINDOW_END_TEXT
            existing.updated_at = now
            return await NotificationRepository.update_push_task(db, existing, commit=commit)

        status_value, scheduled_at, daily_sequence, reason = await NotificationService._schedule_push_task(
            db,
            recipient_id=notification.recipient_id,
            notification=notification,
            now=now,
        )
        return await NotificationRepository.create_push_task(
            db,
            NotificationPushTask(
                notification_id=notification.id,
                recipient_id=notification.recipient_id,
                channel="wechat_template",
                status=status_value,
                title=notification.title,
                detail=notification.detail,
                action_url=notification.action_url,
                payload=payload,
                scheduled_at=scheduled_at,
                send_window_start=NotificationService.SEND_WINDOW_START_TEXT,
                send_window_end=NotificationService.SEND_WINDOW_END_TEXT,
                daily_sequence=daily_sequence,
                reason=reason,
                dedupe_key=dedupe_key,
            ),
            commit=commit,
        )

    @staticmethod
    def _user_name(user: User | None, fallback: str) -> str:
        if user is None:
            return fallback
        return user.display_name or fallback

    @staticmethod
    async def _sync_generated_notifications(db: AsyncSession, current_user: User) -> None:
        if current_user.role != "seeker":
            return

        from app.modules.job.repository import JobRepository
        from app.modules.job.service import JobService

        subscriptions, _ = await JobRepository.list_subscriptions(
            db,
            seeker_id=current_user.id,
            skip=0,
            limit=100,
        )
        for subscription in subscriptions:
            matched_jobs, match_count = await JobService._subscription_matches(db, subscription)
            await JobService._sync_subscription_match_notification(db, subscription, matched_jobs, match_count)

    @staticmethod
    async def create_or_update(
        db: AsyncSession,
        *,
        recipient_id: int,
        type_: str,
        title: str,
        detail: str | None = None,
        action_url: str | None = None,
        payload: dict[str, Any] | None = None,
        dedupe_key: str | None = None,
        commit: bool = True,
    ) -> Notification:
        existing = None
        if dedupe_key:
            existing = await NotificationRepository.get_by_dedupe_key(
                db,
                recipient_id=recipient_id,
                dedupe_key=dedupe_key,
            )
        if existing is not None:
            existing.type = type_
            existing.title = title
            existing.detail = detail
            existing.action_url = action_url
            existing.payload = payload or {}
            existing.updated_at = _now()
            updated = await NotificationRepository.update(db, existing, commit=False)
            await NotificationService._sync_push_task(db, updated, commit=False)
            if commit:
                await db.commit()
                await db.refresh(updated)
            return updated

        if dedupe_key:
            try:
                async with db.begin_nested():
                    created = await NotificationRepository.create(
                        db,
                        Notification(
                            recipient_id=recipient_id,
                            type=type_,
                            title=title,
                            detail=detail,
                            action_url=action_url,
                            payload=payload or {},
                            dedupe_key=dedupe_key,
                        ),
                        commit=False,
                    )
                await NotificationService._sync_push_task(db, created, commit=False)
                if commit:
                    await db.commit()
                    await db.refresh(created)
                return created
            except IntegrityError:
                existing = await NotificationRepository.get_by_dedupe_key(
                    db,
                    recipient_id=recipient_id,
                dedupe_key=dedupe_key,
            )
            if existing is None:
                raise
            existing.type = type_
            existing.title = title
            existing.detail = detail
            existing.action_url = action_url
            existing.payload = payload or {}
            existing.updated_at = _now()
            updated = await NotificationRepository.update(db, existing, commit=False)
            await NotificationService._sync_push_task(db, updated, commit=False)
            if commit:
                await db.commit()
                await db.refresh(updated)
            return updated

        created = await NotificationRepository.create(
            db,
            Notification(
                recipient_id=recipient_id,
                type=type_,
                title=title,
                detail=detail,
                action_url=action_url,
                payload=payload or {},
                dedupe_key=None,
            ),
            commit=False,
        )
        await NotificationService._sync_push_task(db, created, commit=False)
        if commit:
            await db.commit()
            await db.refresh(created)
        return created

    @staticmethod
    async def notify_job_reviewed(
        db: AsyncSession,
        *,
        job: Any,
        action: str,
        reject_reason: str | None = None,
        commit: bool = True,
    ) -> Notification:
        approved = action == "approve"
        title = f"岗位「{job.title}」审核通过" if approved else f"岗位「{job.title}」审核未通过"
        detail = "岗位已上线，求职者现在可以看到该岗位。" if approved else (reject_reason or "请修改后重新提交审核。")
        return await NotificationService.create_or_update(
            db,
            recipient_id=job.recruiter_id,
            type_="job_review",
            title=title,
            detail=detail,
            action_url=f"/recruiter/job/{job.id}",
            payload={
                "job_id": job.id,
                "job_title": job.title,
                "review_action": action,
                "job_status": job.status,
                "reject_reason": reject_reason,
            },
            dedupe_key=f"job_review:{job.id}:{action}:{job.reviewed_at.isoformat() if job.reviewed_at else 'pending'}",
            commit=commit,
        )

    @staticmethod
    async def notify_message_received(
        db: AsyncSession,
        *,
        conversation: Any,
        sender: User,
        message: Any,
        commit: bool = True,
    ) -> Notification:
        recipient_id = conversation.recruiter_id if sender.id == conversation.seeker_id else conversation.seeker_id
        recipient_role = "recruiter" if recipient_id == conversation.recruiter_id else "seeker"
        sender_name = NotificationService._user_name(sender, "对方")
        job_title = conversation.job.title if conversation.job else "相关岗位"
        preview = (message.content or "").strip()
        if len(preview) > 80:
            preview = f"{preview[:80]}..."
        return await NotificationService.create_or_update(
            db,
            recipient_id=recipient_id,
            type_="message",
            title=f"{sender_name} 发来一条新留言",
            detail=f"{job_title}：{preview}",
            action_url=f"/{recipient_role}/chat/{conversation.id}",
            payload={
                "conversation_id": conversation.id,
                "message_id": message.id,
                "job_id": conversation.job_id,
                "job_title": job_title,
                "sender_id": sender.id,
                "sender_role": sender.role,
            },
            dedupe_key=f"message:{message.id}",
            commit=commit,
        )

    @staticmethod
    async def notify_application_submitted(
        db: AsyncSession,
        *,
        application: Any,
        commit: bool = True,
    ) -> Notification:
        seeker_name = NotificationService._user_name(application.seeker, "求职者")
        job_title = application.job.title if application.job else f"岗位 #{application.job_id}"
        return await NotificationService.create_or_update(
            db,
            recipient_id=application.recruiter_id,
            type_="application",
            title=f"{seeker_name} 投递了「{job_title}」",
            detail=application.cover_message or "请及时查看简历并处理投递。",
            action_url=f"/recruiter/applications/{application.id}",
            payload={
                "application_id": application.id,
                "job_id": application.job_id,
                "job_title": job_title,
                "seeker_id": application.seeker_id,
                "seeker_display_name": seeker_name,
                "status": application.status,
            },
            dedupe_key=f"application_submitted:{application.id}",
            commit=commit,
        )

    @staticmethod
    async def notify_application_status_changed(
        db: AsyncSession,
        *,
        application: Any,
        old_status: str,
        new_status: str,
        reject_reason: str | None = None,
        commit: bool = True,
    ) -> Notification:
        status_text = {
            "viewed": "已查看",
            "interview_invited": "已邀面",
            "rejected": "未通过",
            "hired": "已录用",
        }.get(new_status, new_status)
        job_title = application.job.title if application.job else f"岗位 #{application.job_id}"
        detail = reject_reason if new_status == "rejected" and reject_reason else f"你的投递状态已更新为：{status_text}。"
        return await NotificationService.create_or_update(
            db,
            recipient_id=application.seeker_id,
            type_="application_status",
            title=f"「{job_title}」投递状态更新",
            detail=detail,
            action_url=f"/seeker/applications?applicationId={application.id}",
            payload={
                "application_id": application.id,
                "job_id": application.job_id,
                "job_title": job_title,
                "from_status": old_status,
                "to_status": new_status,
                "status_text": status_text,
                "reject_reason": reject_reason,
            },
            dedupe_key=f"application_status:{application.id}:{new_status}:{application.status_updated_at.isoformat() if application.status_updated_at else 'pending'}",
            commit=commit,
        )

    @staticmethod
    async def list_my_notifications(
        db: AsyncSession,
        current_user: User,
        *,
        skip: int = 0,
        limit: int = 20,
        unread_only: bool = False,
    ) -> NotificationListResponse:
        await NotificationService._sync_generated_notifications(db, current_user)

        items, total = await NotificationRepository.list_for_user(
            db,
            recipient_id=current_user.id,
            skip=skip,
            limit=limit,
            unread_only=unread_only,
        )
        unread_count = await NotificationRepository.count_unread(db, recipient_id=current_user.id)
        return NotificationListResponse(
            items=[_to_response(item) for item in items],
            total=total,
            unread_count=unread_count,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    async def list_my_push_tasks(
        db: AsyncSession,
        current_user: User,
        *,
        skip: int = 0,
        limit: int = 20,
        status_filter: str | None = None,
    ) -> NotificationPushTaskListResponse:
        items, total = await NotificationRepository.list_push_tasks(
            db,
            recipient_id=current_user.id,
            status=status_filter,
            skip=skip,
            limit=limit,
        )
        return NotificationPushTaskListResponse(
            items=[_to_push_response(item) for item in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    async def list_admin_push_tasks(
        db: AsyncSession,
        current_user: User,
        *,
        skip: int = 0,
        limit: int = 20,
        status_filter: str | None = None,
    ) -> NotificationPushTaskListResponse:
        if current_user.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can view push tasks")
        items, total = await NotificationRepository.list_push_tasks(
            db,
            status=status_filter,
            skip=skip,
            limit=limit,
        )
        return NotificationPushTaskListResponse(
            items=[_to_push_response(item) for item in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    async def update_admin_push_task_status(
        db: AsyncSession,
        current_user: User,
        task_id: int,
        data: NotificationPushTaskStatusUpdate,
    ) -> NotificationPushTaskResponse:
        if current_user.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can update push tasks")
        task = await NotificationRepository.get_push_task_by_id(db, task_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Push task not found")
        now = NotificationService._push_now()
        task.status = data.status
        task.updated_at = now
        if data.status == "sent":
            task.sent_at = now
            task.failed_at = None
            task.error_message = None
        else:
            task.failed_at = now
            task.error_message = data.error_message or "Manual failure mark"
        updated = await NotificationRepository.update_push_task(db, task)
        return _to_push_response(updated)

    @staticmethod
    def _mark_push_sent(task: NotificationPushTask, now: datetime, *, detail: str | None = None) -> None:
        task.status = "sent"
        task.sent_at = now
        task.failed_at = None
        task.error_message = None
        task.updated_at = now
        if detail is not None:
            task.detail = detail

    @staticmethod
    def _record_provider_result(task: NotificationPushTask, result: PushSendResult) -> None:
        payload = dict(task.payload or {})
        payload["push_provider"] = {
            "provider": result.provider,
            "ok": result.ok,
            "skipped": result.skipped,
            "retryable": result.retryable,
            "error_code": result.error_code,
            "external_id": result.external_id,
            "message": result.message,
            "raw_response": result.raw_response,
        }
        task.payload = payload

    @staticmethod
    def _mark_push_failed_or_deferred(task: NotificationPushTask, now: datetime, result: PushSendResult) -> None:
        task.failed_at = now
        task.error_message = result.message[:500]
        task.updated_at = now
        if result.retryable and (task.attempt_count or 0) < NotificationService.MAX_PROVIDER_ATTEMPTS:
            task.status = "deferred"
            task.scheduled_at = now + timedelta(minutes=10)
            task.reason = result.error_code or "provider_retry"
            return
        task.status = "failed"

    @staticmethod
    async def run_admin_push_worker(
        db: AsyncSession,
        current_user: User,
        *,
        limit: int = 50,
    ) -> NotificationPushWorkerRunResponse:
        if current_user.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can run push worker")
        now = NotificationService._push_now()
        tasks = await NotificationRepository.list_due_push_tasks(db, now=now, limit=limit)
        sent_count = 0
        digest_count = 0
        failed_count = 0
        skipped_count = 0
        items: list[NotificationPushTask] = []
        provider = get_notification_push_provider()
        recipients: dict[int, User | None] = {}

        for task in tasks:
            try:
                task.attempt_count = (task.attempt_count or 0) + 1
                is_digest = task.status == "digest_placeholder"
                if is_digest:
                    digest_count += 1
                    payload = dict(task.payload or {})
                    payload["digest_generated_at"] = now.isoformat()
                    payload["digest_source_status"] = "digest_placeholder"
                    task.payload = payload
                    task.detail = task.detail or "今日通知较多，已合并为摘要提醒。请进入平台查看详情。"

                if task.recipient_id not in recipients:
                    recipients[task.recipient_id] = await UserRepository.get_by_id(db, task.recipient_id)
                result = await provider.send(task, recipients[task.recipient_id])
                NotificationService._record_provider_result(task, result)
                if result.ok:
                    if result.skipped:
                        skipped_count += 1
                    elif not is_digest:
                        sent_count += 1
                    NotificationService._mark_push_sent(
                        task,
                        now,
                    )
                else:
                    failed_count += 1
                    NotificationService._mark_push_failed_or_deferred(task, now, result)
                items.append(await NotificationRepository.update_push_task(db, task, commit=False))
            except Exception as exc:  # pragma: no cover - defensive guard for future real providers
                failed_count += 1
                task.status = "failed"
                task.failed_at = now
                task.error_message = str(exc)[:500]
                task.updated_at = now
                items.append(await NotificationRepository.update_push_task(db, task, commit=False))

        await db.commit()
        for item in items:
            await db.refresh(item)

        return NotificationPushWorkerRunResponse(
            processed_count=len(items),
            sent_count=sent_count,
            digest_count=digest_count,
            failed_count=failed_count,
            skipped_count=skipped_count,
            items=[_to_push_response(item) for item in items],
        )

    @staticmethod
    async def unread_count(
        db: AsyncSession,
        current_user: User,
        type_: str | None = None,
    ) -> NotificationUnreadCountResponse:
        if type_ is not None and type_ not in {"match"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported notification type")
        await NotificationService._sync_generated_notifications(db, current_user)
        return NotificationUnreadCountResponse(
            unread_count=await NotificationRepository.count_unread(db, recipient_id=current_user.id, type_=type_)
        )

    @staticmethod
    async def mark_read(
        db: AsyncSession,
        current_user: User,
        notification_id: int,
    ) -> NotificationMarkReadResponse:
        notification = await NotificationRepository.get_by_id(
            db,
            recipient_id=current_user.id,
            notification_id=notification_id,
        )
        if notification is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

        if notification.read_at is None:
            notification.read_at = _now()
            notification.updated_at = notification.read_at
            await NotificationRepository.update(db, notification)
        return NotificationMarkReadResponse(
            ok=True,
            unread_count=await NotificationRepository.count_unread(db, recipient_id=current_user.id),
        )

    @staticmethod
    async def mark_all_read(db: AsyncSession, current_user: User) -> NotificationMarkReadResponse:
        await NotificationRepository.mark_all_read(db, recipient_id=current_user.id, read_at=_now())
        return NotificationMarkReadResponse(ok=True, unread_count=0)

    @staticmethod
    async def mark_type_read(
        db: AsyncSession,
        current_user: User,
        type_: str,
    ) -> NotificationMarkReadResponse:
        if type_ not in {"match"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported notification type")
        await NotificationService._sync_generated_notifications(db, current_user)
        await NotificationRepository.mark_type_read(
            db,
            recipient_id=current_user.id,
            type_=type_,
            read_at=_now(),
        )
        return NotificationMarkReadResponse(
            ok=True,
            unread_count=await NotificationRepository.count_unread(db, recipient_id=current_user.id),
        )
