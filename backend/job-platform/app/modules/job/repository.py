"""
Job repository.
"""
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.job.models import Job


class JobRepository:
    """Database access for job postings."""

    @staticmethod
    async def create(db: AsyncSession, job: Job) -> Job:
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job

    @staticmethod
    async def update(db: AsyncSession, job: Job) -> Job:
        await db.commit()
        await db.refresh(job)
        return job

    @staticmethod
    async def get_by_id(db: AsyncSession, job_id: int) -> Optional[Job]:
        result = await db.execute(
            select(Job)
            .options(selectinload(Job.recruiter))
            .where(Job.id == job_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_recruiter(
        db: AsyncSession,
        recruiter_id: int,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> tuple[list[Job], int]:
        filters = [Job.recruiter_id == recruiter_id]
        if status:
            filters.append(Job.status == status)

        total_result = await db.execute(select(func.count()).select_from(Job).where(*filters))
        total = total_result.scalar_one()

        result = await db.execute(
            select(Job)
            .options(selectinload(Job.recruiter))
            .where(*filters)
            .order_by(Job.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    @staticmethod
    async def list_for_admin(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> tuple[list[Job], int]:
        filters = []
        if status:
            filters.append(Job.status == status)

        total_query = select(func.count()).select_from(Job)
        if filters:
            total_query = total_query.where(*filters)
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()

        query = (
            select(Job)
            .options(selectinload(Job.recruiter))
            .order_by(Job.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        if filters:
            query = query.where(*filters)

        result = await db.execute(query)
        return list(result.scalars().all()), total

    @staticmethod
    async def list_public_active(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        city: Optional[str] = None,
    ) -> tuple[list[Job], int]:
        filters = [Job.status == "active"]
        if city:
            filters.append(Job.city.contains(city))

        total_result = await db.execute(select(func.count()).select_from(Job).where(*filters))
        total = total_result.scalar_one()

        result = await db.execute(
            select(Job)
            .options(selectinload(Job.recruiter))
            .where(*filters)
            .order_by(Job.published_at.desc().nullslast(), Job.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total
