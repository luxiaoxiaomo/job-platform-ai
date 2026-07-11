"""
Service for admin-managed base data.
"""
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.base_data.models import BaseDataOperationLog, StandardPosition, TagLibraryItem
from app.modules.base_data.repository import BaseDataOperationLogRepository, StandardPositionRepository, TagLibraryItemRepository
from app.modules.base_data.schemas import (
    BaseDataOperationLogListResponse,
    BaseDataOperationLogResponse,
    StandardPositionCreate,
    StandardPositionListResponse,
    StandardPositionResponse,
    StandardPositionUpdate,
    TagLibraryItemCreate,
    TagLibraryItemListResponse,
    TagLibraryItemResponse,
    TagLibraryItemUpdate,
)
from app.modules.user.models import User


def _position_snapshot(position: StandardPosition) -> dict:
    return {
        "id": position.id,
        "name": position.name,
        "category": position.category,
        "aliases": list(position.aliases or []),
        "description": position.description,
        "status": position.status,
        "created_by": position.created_by,
        "updated_by": position.updated_by,
    }


def _position_response(position: StandardPosition) -> StandardPositionResponse:
    return StandardPositionResponse(
        id=position.id,
        name=position.name,
        category=position.category,
        aliases=list(position.aliases or []),
        description=position.description,
        status=position.status,
        created_by=position.created_by,
        updated_by=position.updated_by,
        created_at=position.created_at,
        updated_at=position.updated_at,
    )


def _tag_snapshot(tag: TagLibraryItem) -> dict:
    return {
        "id": tag.id,
        "name": tag.name,
        "category": tag.category,
        "parent_id": tag.parent_id,
        "color": tag.color,
        "description": tag.description,
        "sort_order": tag.sort_order,
        "status": tag.status,
        "created_by": tag.created_by,
        "updated_by": tag.updated_by,
    }


def _tag_response(tag: TagLibraryItem) -> TagLibraryItemResponse:
    return TagLibraryItemResponse(
        id=tag.id,
        name=tag.name,
        category=tag.category,
        parent_id=tag.parent_id,
        color=tag.color,
        description=tag.description,
        sort_order=tag.sort_order,
        status=tag.status,
        created_by=tag.created_by,
        updated_by=tag.updated_by,
        created_at=tag.created_at,
        updated_at=tag.updated_at,
    )


def _log_response(log: BaseDataOperationLog) -> BaseDataOperationLogResponse:
    return BaseDataOperationLogResponse(
        id=log.id,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        action=log.action,
        actor_id=log.actor_id,
        before=log.before,
        after=log.after,
        created_at=log.created_at,
    )


class BaseDataService:
    """Business logic for base data CRUD and operation logs."""

    @staticmethod
    async def list_standard_positions(
        db: AsyncSession,
        *,
        q: str | None = None,
        category: str | None = None,
        status_: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> StandardPositionListResponse:
        items, total = await StandardPositionRepository.list_positions(
            db,
            q=q.strip() if q else None,
            category=category.strip() if category else None,
            status=status_,
            skip=skip,
            limit=limit,
        )
        return StandardPositionListResponse(
            items=[_position_response(item) for item in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    async def get_standard_position(db: AsyncSession, position_id: int) -> StandardPositionResponse:
        position = await StandardPositionRepository.get_by_id(db, position_id)
        if position is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Standard position not found")
        return _position_response(position)

    @staticmethod
    async def create_standard_position(
        db: AsyncSession,
        admin: User,
        data: StandardPositionCreate,
    ) -> StandardPositionResponse:
        existing = await StandardPositionRepository.get_by_name(db, data.name)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Standard position name already exists")

        position = StandardPosition(
            name=data.name,
            category=data.category,
            aliases=data.aliases,
            description=data.description,
            status=data.status,
            created_by=admin.id,
            updated_by=admin.id,
        )
        db.add(position)
        await db.flush()
        after = _position_snapshot(position)
        db.add(
            BaseDataOperationLog(
                resource_type="standard_position",
                resource_id=position.id,
                action="create",
                actor_id=admin.id,
                before=None,
                after=after,
            )
        )
        await db.commit()
        await db.refresh(position)
        return _position_response(position)

    @staticmethod
    async def update_standard_position(
        db: AsyncSession,
        admin: User,
        position_id: int,
        data: StandardPositionUpdate,
    ) -> StandardPositionResponse:
        position = await StandardPositionRepository.get_by_id(db, position_id)
        if position is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Standard position not found")

        updates = data.model_dump(exclude_unset=True)
        if "name" in updates:
            existing = await StandardPositionRepository.get_by_name(db, updates["name"])
            if existing is not None and existing.id != position.id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Standard position name already exists")

        before = _position_snapshot(position)
        old_status = position.status
        for field, value in updates.items():
            setattr(position, field, value)
        position.updated_by = admin.id
        await db.flush()

        action = "deactivate" if old_status != "inactive" and position.status == "inactive" else "update"
        db.add(
            BaseDataOperationLog(
                resource_type="standard_position",
                resource_id=position.id,
                action=action,
                actor_id=admin.id,
                before=before,
                after=_position_snapshot(position),
            )
        )
        await db.commit()
        await db.refresh(position)
        return _position_response(position)

    @staticmethod
    async def list_tags(
        db: AsyncSession,
        *,
        q: str | None = None,
        category: str | None = None,
        status_: str | None = None,
        parent_id: int | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> TagLibraryItemListResponse:
        items, total = await TagLibraryItemRepository.list_tags(
            db,
            q=q.strip() if q else None,
            category=category.strip() if category else None,
            status=status_,
            parent_id=parent_id,
            skip=skip,
            limit=limit,
        )
        return TagLibraryItemListResponse(
            items=[_tag_response(item) for item in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    async def get_tag(db: AsyncSession, tag_id: int) -> TagLibraryItemResponse:
        tag = await TagLibraryItemRepository.get_by_id(db, tag_id)
        if tag is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
        return _tag_response(tag)

    @staticmethod
    async def create_tag(db: AsyncSession, admin: User, data: TagLibraryItemCreate) -> TagLibraryItemResponse:
        existing = await TagLibraryItemRepository.get_by_category_name(db, data.category, data.name)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tag name already exists in category")
        if data.parent_id is not None:
            parent = await TagLibraryItemRepository.get_by_id(db, data.parent_id)
            if parent is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent tag not found")

        tag = TagLibraryItem(
            name=data.name,
            category=data.category,
            parent_id=data.parent_id,
            color=data.color,
            description=data.description,
            sort_order=data.sort_order,
            status=data.status,
            created_by=admin.id,
            updated_by=admin.id,
        )
        db.add(tag)
        await db.flush()
        db.add(
            BaseDataOperationLog(
                resource_type="tag",
                resource_id=tag.id,
                action="create",
                actor_id=admin.id,
                before=None,
                after=_tag_snapshot(tag),
            )
        )
        await db.commit()
        await db.refresh(tag)
        return _tag_response(tag)

    @staticmethod
    async def update_tag(
        db: AsyncSession,
        admin: User,
        tag_id: int,
        data: TagLibraryItemUpdate,
    ) -> TagLibraryItemResponse:
        tag = await TagLibraryItemRepository.get_by_id(db, tag_id)
        if tag is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

        updates = data.model_dump(exclude_unset=True)
        next_category = updates.get("category", tag.category)
        next_name = updates.get("name", tag.name)
        if "category" in updates or "name" in updates:
            existing = await TagLibraryItemRepository.get_by_category_name(db, next_category, next_name)
            if existing is not None and existing.id != tag.id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tag name already exists in category")
        if "parent_id" in updates and updates["parent_id"] is not None:
            if updates["parent_id"] == tag.id:
                raise HTTPException(status_code=422, detail="Tag cannot be its own parent")
            parent = await TagLibraryItemRepository.get_by_id(db, updates["parent_id"])
            if parent is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent tag not found")

        before = _tag_snapshot(tag)
        old_status = tag.status
        for field, value in updates.items():
            setattr(tag, field, value)
        tag.updated_by = admin.id
        await db.flush()

        action = "deactivate" if old_status != "inactive" and tag.status == "inactive" else "update"
        db.add(
            BaseDataOperationLog(
                resource_type="tag",
                resource_id=tag.id,
                action=action,
                actor_id=admin.id,
                before=before,
                after=_tag_snapshot(tag),
            )
        )
        await db.commit()
        await db.refresh(tag)
        return _tag_response(tag)

    @staticmethod
    async def list_operation_logs(
        db: AsyncSession,
        *,
        resource_type: str | None = None,
        resource_id: int | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> BaseDataOperationLogListResponse:
        logs, total = await BaseDataOperationLogRepository.list_logs(
            db,
            resource_type=resource_type,
            resource_id=resource_id,
            skip=skip,
            limit=limit,
        )
        return BaseDataOperationLogListResponse(
            items=[_log_response(log) for log in logs],
            total=total,
            skip=skip,
            limit=limit,
        )
