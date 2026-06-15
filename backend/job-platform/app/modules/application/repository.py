"""
Job application repository.
"""
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.application.models import JobApplication, JobApplicationTimeline


class ApplicationRepository:
    """Database access for job applications."""

    @staticmethod
    async def create(db: AsyncSession, application: JobApplication) -> JobApplication:
        db.add(application)
        await db.commit()
        await db.refresh(application)
        return application

    @staticmethod
    async def update(db: AsyncSession, application: JobApplication) -> JobApplication:
        await db.commit()
        await db.refresh(application)
        return application

    @staticmethod
    async def get_by_id(db: AsyncSession, application_id: int) -> Optional[JobApplication]:
        result = await db.execute(
            select(JobApplication)
            .options(
                selectinload(JobApplication.job),
                selectinload(JobApplication.seeker),
                selectinload(JobApplication.recruiter),
                selectinload(JobApplication.resume),
            )
            .where(JobApplication.id == application_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def add_timeline(db: AsyncSession, timeline: JobApplicationTimeline) -> JobApplicationTimeline:
        db.add(timeline)
        await db.flush()
        return timeline

    @staticmethod
    async def list_timelines(db: AsyncSession, application_id: int) -> list[JobApplicationTimeline]:
        result = await db.execute(
            select(JobApplicationTimeline)
            .where(JobApplicationTimeline.application_id == application_id)
            .order_by(JobApplicationTimeline.created_at.asc(), JobApplicationTimeline.id.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_job_and_seeker(
        db: AsyncSession,
        job_id: int,
        seeker_id: int,
    ) -> Optional[JobApplication]:
        result = await db.execute(
            select(JobApplication).where(
                JobApplication.job_id == job_id,
                JobApplication.seeker_id == seeker_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_seeker(
        db: AsyncSession,
        seeker_id: int,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> tuple[list[JobApplication], int]:
        filters = [JobApplication.seeker_id == seeker_id]
        if status:
            filters.append(JobApplication.status == status)
        return await ApplicationRepository._list(db, filters, skip, limit)

    @staticmethod
    async def list_by_recruiter(
        db: AsyncSession,
        recruiter_id: int,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> tuple[list[JobApplication], int]:
        filters = [JobApplication.recruiter_id == recruiter_id]
        if status:
            filters.append(JobApplication.status == status)
        return await ApplicationRepository._list(db, filters, skip, limit)

    @staticmethod
    async def list_for_admin(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> tuple[list[JobApplication], int]:
        filters = []
        if status:
            filters.append(JobApplication.status == status)
        return await ApplicationRepository._list(db, filters, skip, limit)

    @staticmethod
    async def _list(
        db: AsyncSession,
        filters: list,
        skip: int,
        limit: int,
    ) -> tuple[list[JobApplication], int]:
        total_query = select(func.count()).select_from(JobApplication)
        if filters:
            total_query = total_query.where(*filters)
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()

        query = (
            select(JobApplication)
            .options(
                selectinload(JobApplication.job),
                selectinload(JobApplication.seeker),
                selectinload(JobApplication.recruiter),
            )
            .order_by(JobApplication.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        if filters:
            query = query.where(*filters)

        result = await db.execute(query)
        return list(result.scalars().all()), total
