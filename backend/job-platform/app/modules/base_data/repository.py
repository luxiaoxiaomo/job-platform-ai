"""
Repository for admin-managed base data.
"""
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.base_data.models import BaseDataOperationLog, StandardPosition, TagLibraryItem


class StandardPositionRepository:
    """Database access for the standard position library."""

    @staticmethod
    async def list_positions(
        db: AsyncSession,
        *,
        q: str | None = None,
        category: str | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[StandardPosition], int]:
        filters = []
        if q:
            pattern = f"%{q}%"
            filters.append(or_(StandardPosition.name.ilike(pattern), StandardPosition.category.ilike(pattern)))
        if category:
            filters.append(StandardPosition.category == category)
        if status:
            filters.append(StandardPosition.status == status)

        total_query = select(func.count()).select_from(StandardPosition)
        if filters:
            total_query = total_query.where(*filters)
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()

        query = (
            select(StandardPosition)
            .order_by(StandardPosition.status.asc(), StandardPosition.category.asc(), StandardPosition.name.asc())
            .offset(skip)
            .limit(limit)
        )
        if filters:
            query = query.where(*filters)
        result = await db.execute(query)
        return list(result.scalars().all()), total

    @staticmethod
    async def get_by_id(db: AsyncSession, position_id: int) -> StandardPosition | None:
        result = await db.execute(select(StandardPosition).where(StandardPosition.id == position_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_name(db: AsyncSession, name: str) -> StandardPosition | None:
        result = await db.execute(select(StandardPosition).where(StandardPosition.name == name))
        return result.scalar_one_or_none()


class BaseDataOperationLogRepository:
    """Database access for base data operation logs."""

    @staticmethod
    async def list_logs(
        db: AsyncSession,
        *,
        resource_type: str | None = None,
        resource_id: int | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[BaseDataOperationLog], int]:
        filters = []
        if resource_type:
            filters.append(BaseDataOperationLog.resource_type == resource_type)
        if resource_id is not None:
            filters.append(BaseDataOperationLog.resource_id == resource_id)

        total_query = select(func.count()).select_from(BaseDataOperationLog)
        if filters:
            total_query = total_query.where(*filters)
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()

        query = select(BaseDataOperationLog).order_by(BaseDataOperationLog.created_at.desc()).offset(skip).limit(limit)
        if filters:
            query = query.where(*filters)
        result = await db.execute(query)
        return list(result.scalars().all()), total


class TagLibraryItemRepository:
    """Database access for the tag library."""

    @staticmethod
    async def list_tags(
        db: AsyncSession,
        *,
        q: str | None = None,
        category: str | None = None,
        status: str | None = None,
        parent_id: int | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[TagLibraryItem], int]:
        filters = []
        if q:
            pattern = f"%{q}%"
            filters.append(or_(TagLibraryItem.name.ilike(pattern), TagLibraryItem.category.ilike(pattern)))
        if category:
            filters.append(TagLibraryItem.category == category)
        if status:
            filters.append(TagLibraryItem.status == status)
        if parent_id is not None:
            filters.append(TagLibraryItem.parent_id == parent_id)

        total_query = select(func.count()).select_from(TagLibraryItem)
        if filters:
            total_query = total_query.where(*filters)
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()

        query = (
            select(TagLibraryItem)
            .order_by(TagLibraryItem.category.asc(), TagLibraryItem.sort_order.asc(), TagLibraryItem.name.asc())
            .offset(skip)
            .limit(limit)
        )
        if filters:
            query = query.where(*filters)
        result = await db.execute(query)
        return list(result.scalars().all()), total

    @staticmethod
    async def get_by_id(db: AsyncSession, tag_id: int) -> TagLibraryItem | None:
        result = await db.execute(select(TagLibraryItem).where(TagLibraryItem.id == tag_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_ids(db: AsyncSession, tag_ids: list[int]) -> list[TagLibraryItem]:
        if not tag_ids:
            return []
        result = await db.execute(select(TagLibraryItem).where(TagLibraryItem.id.in_(tag_ids)))
        return list(result.scalars().all())

    @staticmethod
    async def get_by_category_name(db: AsyncSession, category: str, name: str) -> TagLibraryItem | None:
        result = await db.execute(
            select(TagLibraryItem).where(TagLibraryItem.category == category, TagLibraryItem.name == name)
        )
        return result.scalar_one_or_none()
