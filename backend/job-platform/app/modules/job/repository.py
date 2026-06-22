"""
Job repository.
"""
from typing import Optional

from sqlalchemy import delete, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.application.models import JobApplication
from app.modules.job.models import Job, JobFavorite, JobSubscription, JobVisit
from app.modules.message.models import Conversation
from app.modules.user.models import User


class JobRepository:
    """Database access for job postings."""

    @staticmethod
    async def create(db: AsyncSession, job: Job) -> Job:
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job

    @staticmethod
    async def update(db: AsyncSession, job: Job, *, commit: bool = True) -> Job:
        if commit:
            await db.commit()
            await db.refresh(job)
        else:
            await db.flush()
        return job

    @staticmethod
    async def create_visit(db: AsyncSession, visit: JobVisit) -> JobVisit:
        db.add(visit)
        await db.commit()
        await db.refresh(visit)
        return visit

    @staticmethod
    async def create_favorite(db: AsyncSession, favorite: JobFavorite) -> JobFavorite:
        db.add(favorite)
        await db.commit()
        await db.refresh(favorite)
        return favorite

    @staticmethod
    async def get_favorite(db: AsyncSession, *, seeker_id: int, job_id: int) -> Optional[JobFavorite]:
        result = await db.execute(
            select(JobFavorite)
            .options(selectinload(JobFavorite.job).selectinload(Job.recruiter))
            .where(
                JobFavorite.seeker_id == seeker_id,
                JobFavorite.job_id == job_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_favorite(db: AsyncSession, *, seeker_id: int, job_id: int) -> bool:
        result = await db.execute(
            delete(JobFavorite).where(
                JobFavorite.seeker_id == seeker_id,
                JobFavorite.job_id == job_id,
            )
        )
        await db.commit()
        return bool(result.rowcount)

    @staticmethod
    async def list_favorites(
        db: AsyncSession,
        *,
        seeker_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[JobFavorite], int]:
        filters = [JobFavorite.seeker_id == seeker_id]
        total_result = await db.execute(select(func.count()).select_from(JobFavorite).where(*filters))
        total = int(total_result.scalar_one() or 0)
        result = await db.execute(
            select(JobFavorite)
            .options(selectinload(JobFavorite.job).selectinload(Job.recruiter))
            .where(*filters)
            .order_by(JobFavorite.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

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

    @staticmethod
    async def count_conversations_by_job_ids(db: AsyncSession, job_ids: list[int]) -> dict[int, int]:
        if not job_ids:
            return {}
        result = await db.execute(
            select(Conversation.job_id, func.count(Conversation.id))
            .where(Conversation.job_id.in_(job_ids))
            .group_by(Conversation.job_id)
        )
        return {job_id: int(count) for job_id, count in result.all()}

    @staticmethod
    async def list_visitors_by_job(
        db: AsyncSession,
        *,
        job_id: int,
        recruiter_id: int,
        skip: int = 0,
        limit: int = 20,
        sort: str = "time",
    ):
        filters = [
            JobVisit.job_id == job_id,
            JobVisit.recruiter_id == recruiter_id,
        ]
        total_result = await db.execute(
            select(func.count(distinct(JobVisit.seeker_id))).where(*filters)
        )
        total = int(total_result.scalar_one() or 0)

        view_count = func.count(JobVisit.id).label("view_count")
        first_viewed_at = func.min(JobVisit.viewed_at).label("first_viewed_at")
        last_viewed_at = func.max(JobVisit.viewed_at).label("last_viewed_at")
        query = (
            select(
                JobVisit.seeker_id,
                User.display_name.label("seeker_display_name"),
                User.avatar_url,
                view_count,
                first_viewed_at,
                last_viewed_at,
            )
            .join(User, User.id == JobVisit.seeker_id)
            .where(*filters)
            .group_by(JobVisit.seeker_id, User.display_name, User.avatar_url)
            .offset(skip)
            .limit(limit)
        )
        if sort == "views":
            query = query.order_by(view_count.desc(), last_viewed_at.desc())
        else:
            query = query.order_by(last_viewed_at.desc())

        result = await db.execute(query)
        return list(result.all()), total

    @staticmethod
    async def list_history_by_seeker(
        db: AsyncSession,
        *,
        seeker_id: int,
        skip: int = 0,
        limit: int = 20,
    ):
        filters = [JobVisit.seeker_id == seeker_id]
        total_result = await db.execute(
            select(func.count(distinct(JobVisit.job_id))).where(*filters)
        )
        total = int(total_result.scalar_one() or 0)
        view_count = func.count(JobVisit.id).label("view_count")
        first_viewed_at = func.min(JobVisit.viewed_at).label("first_viewed_at")
        last_viewed_at = func.max(JobVisit.viewed_at).label("last_viewed_at")
        query = (
            select(Job, view_count, first_viewed_at, last_viewed_at)
            .join(JobVisit, JobVisit.job_id == Job.id)
            .options(selectinload(Job.recruiter))
            .where(*filters)
            .group_by(Job.id)
            .order_by(last_viewed_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.all()), total

    @staticmethod
    async def favorite_job_ids(db: AsyncSession, *, seeker_id: int, job_ids: list[int]) -> set[int]:
        if not job_ids:
            return set()
        result = await db.execute(
            select(JobFavorite.job_id).where(
                JobFavorite.seeker_id == seeker_id,
                JobFavorite.job_id.in_(job_ids),
            )
        )
        return {int(job_id) for job_id in result.scalars().all()}

    @staticmethod
    async def create_subscription(db: AsyncSession, subscription: JobSubscription) -> JobSubscription:
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)
        return subscription

    @staticmethod
    async def update_subscription(db: AsyncSession, subscription: JobSubscription) -> JobSubscription:
        await db.commit()
        await db.refresh(subscription)
        return subscription

    @staticmethod
    async def get_subscription(db: AsyncSession, *, seeker_id: int, subscription_id: int) -> Optional[JobSubscription]:
        result = await db.execute(
            select(JobSubscription).where(
                JobSubscription.id == subscription_id,
                JobSubscription.seeker_id == seeker_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_subscription(db: AsyncSession, *, seeker_id: int, subscription_id: int) -> bool:
        result = await db.execute(
            delete(JobSubscription).where(
                JobSubscription.id == subscription_id,
                JobSubscription.seeker_id == seeker_id,
            )
        )
        await db.commit()
        return bool(result.rowcount)

    @staticmethod
    async def list_subscriptions(
        db: AsyncSession,
        *,
        seeker_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[JobSubscription], int]:
        filters = [JobSubscription.seeker_id == seeker_id]
        total_result = await db.execute(select(func.count()).select_from(JobSubscription).where(*filters))
        total = int(total_result.scalar_one() or 0)
        result = await db.execute(
            select(JobSubscription)
            .where(*filters)
            .order_by(JobSubscription.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    @staticmethod
    async def list_active_jobs_for_matching(db: AsyncSession, *, limit: int = 200) -> list[Job]:
        result = await db.execute(
            select(Job)
            .options(selectinload(Job.recruiter))
            .where(Job.status == "active")
            .order_by(Job.published_at.desc().nullslast(), Job.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def conversation_seeker_ids(
        db: AsyncSession,
        *,
        job_id: int,
        seeker_ids: list[int],
    ) -> set[int]:
        if not seeker_ids:
            return set()
        result = await db.execute(
            select(Conversation.seeker_id)
            .where(
                Conversation.job_id == job_id,
                Conversation.seeker_id.in_(seeker_ids),
            )
        )
        return {int(seeker_id) for seeker_id in result.scalars().all()}

    @staticmethod
    async def application_seeker_ids(
        db: AsyncSession,
        *,
        job_id: int,
        seeker_ids: list[int],
    ) -> set[int]:
        if not seeker_ids:
            return set()
        result = await db.execute(
            select(JobApplication.seeker_id)
            .where(
                JobApplication.job_id == job_id,
                JobApplication.seeker_id.in_(seeker_ids),
            )
        )
        return {int(seeker_id) for seeker_id in result.scalars().all()}
