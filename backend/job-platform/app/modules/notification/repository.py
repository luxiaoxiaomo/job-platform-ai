"""
Notification persistence helpers.
"""
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notification.models import Notification, NotificationPushTask


class NotificationRepository:
    @staticmethod
    async def get_by_id(db: AsyncSession, *, recipient_id: int, notification_id: int) -> Notification | None:
        result = await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.recipient_id == recipient_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_dedupe_key(db: AsyncSession, *, recipient_id: int, dedupe_key: str) -> Notification | None:
        result = await db.execute(
            select(Notification).where(
                Notification.recipient_id == recipient_id,
                Notification.dedupe_key == dedupe_key,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, notification: Notification, *, commit: bool = True) -> Notification:
        db.add(notification)
        if commit:
            await db.commit()
            await db.refresh(notification)
        else:
            await db.flush()
        return notification

    @staticmethod
    async def update(db: AsyncSession, notification: Notification, *, commit: bool = True) -> Notification:
        db.add(notification)
        if commit:
            await db.commit()
            await db.refresh(notification)
        else:
            await db.flush()
        return notification

    @staticmethod
    async def list_for_user(
        db: AsyncSession,
        *,
        recipient_id: int,
        skip: int = 0,
        limit: int = 20,
        unread_only: bool = False,
    ) -> tuple[list[Notification], int]:
        filters = [Notification.recipient_id == recipient_id]
        if unread_only:
            filters.append(Notification.read_at.is_(None))
        total_result = await db.execute(select(func.count()).select_from(Notification).where(*filters))
        total = int(total_result.scalar_one() or 0)
        result = await db.execute(
            select(Notification)
            .where(*filters)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    @staticmethod
    async def count_unread(db: AsyncSession, *, recipient_id: int, type_: str | None = None) -> int:
        filters = [Notification.recipient_id == recipient_id, Notification.read_at.is_(None)]
        if type_:
            filters.append(Notification.type == type_)
        result = await db.execute(
            select(func.count())
            .select_from(Notification)
            .where(*filters)
        )
        return int(result.scalar_one() or 0)

    @staticmethod
    async def mark_all_read(db: AsyncSession, *, recipient_id: int, read_at: datetime) -> int:
        result = await db.execute(
            update(Notification)
            .where(Notification.recipient_id == recipient_id, Notification.read_at.is_(None))
            .values(read_at=read_at, updated_at=read_at)
        )
        await db.commit()
        return int(result.rowcount or 0)

    @staticmethod
    async def mark_type_read(db: AsyncSession, *, recipient_id: int, type_: str, read_at: datetime) -> int:
        result = await db.execute(
            update(Notification)
            .where(
                Notification.recipient_id == recipient_id,
                Notification.type == type_,
                Notification.read_at.is_(None),
            )
            .values(read_at=read_at, updated_at=read_at)
        )
        await db.commit()
        return int(result.rowcount or 0)

    @staticmethod
    async def get_push_by_dedupe_key(
        db: AsyncSession,
        *,
        recipient_id: int,
        dedupe_key: str,
    ) -> NotificationPushTask | None:
        result = await db.execute(
            select(NotificationPushTask).where(
                NotificationPushTask.recipient_id == recipient_id,
                NotificationPushTask.dedupe_key == dedupe_key,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_push_task_by_id(db: AsyncSession, task_id: int) -> NotificationPushTask | None:
        result = await db.execute(select(NotificationPushTask).where(NotificationPushTask.id == task_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_push_task(
        db: AsyncSession,
        task: NotificationPushTask,
        *,
        commit: bool = True,
    ) -> NotificationPushTask:
        db.add(task)
        if commit:
            await db.commit()
            await db.refresh(task)
        else:
            await db.flush()
        return task

    @staticmethod
    async def update_push_task(
        db: AsyncSession,
        task: NotificationPushTask,
        *,
        commit: bool = True,
    ) -> NotificationPushTask:
        db.add(task)
        if commit:
            await db.commit()
            await db.refresh(task)
        else:
            await db.flush()
        return task

    @staticmethod
    async def count_immediate_pushes_for_day(
        db: AsyncSession,
        *,
        recipient_id: int,
        day_start: datetime,
        day_end: datetime,
    ) -> int:
        result = await db.execute(
            select(func.count())
            .select_from(NotificationPushTask)
            .where(
                NotificationPushTask.recipient_id == recipient_id,
                NotificationPushTask.status.in_(["pending", "sent"]),
                NotificationPushTask.scheduled_at >= day_start,
                NotificationPushTask.scheduled_at < day_end,
            )
        )
        return int(result.scalar_one() or 0)

    @staticmethod
    async def list_push_tasks(
        db: AsyncSession,
        *,
        recipient_id: int | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[NotificationPushTask], int]:
        filters = []
        if recipient_id is not None:
            filters.append(NotificationPushTask.recipient_id == recipient_id)
        if status:
            filters.append(NotificationPushTask.status == status)

        total_result = await db.execute(select(func.count()).select_from(NotificationPushTask).where(*filters))
        total = int(total_result.scalar_one() or 0)
        result = await db.execute(
            select(NotificationPushTask)
            .where(*filters)
            .order_by(NotificationPushTask.scheduled_at.asc(), NotificationPushTask.id.asc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    @staticmethod
    async def list_due_push_tasks(
        db: AsyncSession,
        *,
        now: datetime,
        limit: int = 50,
    ) -> list[NotificationPushTask]:
        result = await db.execute(
            select(NotificationPushTask)
            .where(
                NotificationPushTask.status.in_(["pending", "deferred", "digest_placeholder"]),
                NotificationPushTask.scheduled_at <= now,
            )
            .order_by(NotificationPushTask.scheduled_at.asc(), NotificationPushTask.id.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
