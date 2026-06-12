"""
Enterprise certification repository.
"""
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.company_certification.models import CompanyCertification


class CompanyCertificationRepository:
    """Data access helpers for enterprise certification."""

    @staticmethod
    async def get_by_id(db: AsyncSession, certification_id: int) -> Optional[CompanyCertification]:
        result = await db.execute(
            select(CompanyCertification)
            .options(
                selectinload(CompanyCertification.recruiter),
                selectinload(CompanyCertification.reviewer),
            )
            .where(CompanyCertification.id == certification_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_recruiter_id(db: AsyncSession, recruiter_id: int) -> Optional[CompanyCertification]:
        result = await db.execute(
            select(CompanyCertification)
            .options(
                selectinload(CompanyCertification.recruiter),
                selectinload(CompanyCertification.reviewer),
            )
            .where(CompanyCertification.recruiter_id == recruiter_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, certification: CompanyCertification) -> CompanyCertification:
        db.add(certification)
        await db.commit()
        await db.refresh(certification)
        return certification

    @staticmethod
    async def update(db: AsyncSession, certification: CompanyCertification) -> CompanyCertification:
        await db.commit()
        await db.refresh(certification)
        return certification

    @staticmethod
    async def list(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> tuple[list[CompanyCertification], int]:
        query = select(CompanyCertification).options(
            selectinload(CompanyCertification.recruiter),
            selectinload(CompanyCertification.reviewer),
        )
        count_query = select(func.count(CompanyCertification.id))

        if status:
            query = query.where(CompanyCertification.status == status)
            count_query = count_query.where(CompanyCertification.status == status)

        query = query.order_by(CompanyCertification.updated_at.desc()).offset(skip).limit(limit)

        items_result = await db.execute(query)
        total_result = await db.execute(count_query)

        return items_result.scalars().all(), int(total_result.scalar_one())
