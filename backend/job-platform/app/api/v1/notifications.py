"""
Notification API.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.modules.notification.schemas import (
    NotificationListResponse,
    NotificationMarkReadResponse,
    NotificationPushTaskListResponse,
    NotificationPushTaskResponse,
    NotificationPushTaskStatusUpdate,
    NotificationPushWorkerRunResponse,
    NotificationUnreadCountResponse,
)
from app.modules.notification.service import NotificationService
from app.modules.user.models import User

router = APIRouter()


@router.get("", response_model=NotificationListResponse)
async def list_my_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List current user's persisted notifications."""
    return await NotificationService.list_my_notifications(
        db,
        current_user,
        skip=skip,
        limit=limit,
        unread_only=unread_only,
    )


@router.get("/unread-count", response_model=NotificationUnreadCountResponse)
async def get_my_notification_unread_count(
    type_: str | None = Query(None, alias="type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return current user's unread notification count."""
    return await NotificationService.unread_count(db, current_user, type_=type_)


@router.get("/push-tasks", response_model=NotificationPushTaskListResponse)
async def list_my_notification_push_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List current user's queued external push tasks."""
    return await NotificationService.list_my_push_tasks(
        db,
        current_user,
        skip=skip,
        limit=limit,
        status_filter=status_filter,
    )


@router.get("/admin/push-tasks", response_model=NotificationPushTaskListResponse)
async def list_admin_notification_push_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """List all queued external push tasks for admin operations."""
    return await NotificationService.list_admin_push_tasks(
        db,
        current_user,
        skip=skip,
        limit=limit,
        status_filter=status_filter,
    )


@router.post("/admin/push-tasks/{task_id}/status", response_model=NotificationPushTaskResponse)
async def update_admin_notification_push_task_status(
    task_id: int,
    data: NotificationPushTaskStatusUpdate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Manually mark one push task as sent or failed."""
    return await NotificationService.update_admin_push_task_status(db, current_user, task_id, data)


@router.post("/admin/push-tasks/run-worker", response_model=NotificationPushWorkerRunResponse)
async def run_admin_notification_push_worker(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Run the placeholder push worker for due tasks. It does not call real WeChat APIs."""
    return await NotificationService.run_admin_push_worker(db, current_user, limit=limit)


@router.post("/types/{type_}/read", response_model=NotificationMarkReadResponse)
async def mark_my_notification_type_read(
    type_: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark unread notifications of one supported type as read."""
    return await NotificationService.mark_type_read(db, current_user, type_)


@router.post("/{notification_id}/read", response_model=NotificationMarkReadResponse)
async def mark_my_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark one notification as read."""
    return await NotificationService.mark_read(db, current_user, notification_id)


@router.post("/read-all", response_model=NotificationMarkReadResponse)
async def mark_all_my_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all current user's notifications as read."""
    return await NotificationService.mark_all_read(db, current_user)
