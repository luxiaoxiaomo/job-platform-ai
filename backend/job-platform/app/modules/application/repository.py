"""
Job application repository.
"""
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.application.models import JobApplication, JobApplicationTimeline
from app.modules.job.models import Job
from app.modules.message.models import ContactExchange, Conversation


def _utc_day_start() -> datetime:
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)


class ApplicationRepository:
    """Database access for job applications."""

    @staticmethod
    async def create(db: AsyncSession, application: JobApplication, *, commit: bool = True) -> JobApplication:
        db.add(application)
        if commit:
            await db.commit()
            await db.refresh(application)
        else:
            await db.flush()
        return application

    @staticmethod
    async def update(db: AsyncSession, application: JobApplication, *, commit: bool = True) -> JobApplication:
        if commit:
            await db.commit()
            await db.refresh(application)
        else:
            await db.flush()
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
    async def count_by_status(
        db: AsyncSession,
        *,
        recruiter_id: Optional[int] = None,
    ) -> dict[str, int]:
        query = select(JobApplication.status, func.count(JobApplication.id)).group_by(JobApplication.status)
        if recruiter_id is not None:
            query = query.where(JobApplication.recruiter_id == recruiter_id)

        result = await db.execute(query)
        counts = {
            "submitted": 0,
            "viewed": 0,
            "interview_invited": 0,
            "rejected": 0,
            "hired": 0,
        }
        for status, count in result.all():
            counts[status] = int(count)
        return counts

    @staticmethod
    async def business_loop_stats(
        db: AsyncSession,
        *,
        recruiter_id: Optional[int] = None,
    ) -> dict[str, int]:
        job_filters = []
        application_filters = []
        conversation_filters = []
        exchange_filters = []

        if recruiter_id is not None:
            job_filters.append(Job.recruiter_id == recruiter_id)
            application_filters.append(JobApplication.recruiter_id == recruiter_id)
            conversation_filters.append(Conversation.recruiter_id == recruiter_id)
            exchange_filters.append(Conversation.recruiter_id == recruiter_id)

        job_count_query = select(func.count()).select_from(Job)
        view_count_query = select(func.coalesce(func.sum(Job.view_count), 0)).select_from(Job)
        if job_filters:
            job_count_query = job_count_query.where(*job_filters)
            view_count_query = view_count_query.where(*job_filters)

        conversation_count_query = select(func.count()).select_from(Conversation)
        if conversation_filters:
            conversation_count_query = conversation_count_query.where(*conversation_filters)

        application_status_query = select(JobApplication.status, func.count(JobApplication.id)).group_by(JobApplication.status)
        if application_filters:
            application_status_query = application_status_query.where(*application_filters)

        exchange_status_query = (
            select(ContactExchange.status, func.count(ContactExchange.id))
            .select_from(ContactExchange)
            .join(Conversation, Conversation.id == ContactExchange.conversation_id)
            .group_by(ContactExchange.status)
        )
        if exchange_filters:
            exchange_status_query = exchange_status_query.where(*exchange_filters)

        job_count = int((await db.execute(job_count_query)).scalar_one() or 0)
        view_count = int((await db.execute(view_count_query)).scalar_one() or 0)
        conversation_count = int((await db.execute(conversation_count_query)).scalar_one() or 0)

        application_counts = {
            "submitted": 0,
            "viewed": 0,
            "interview_invited": 0,
            "rejected": 0,
            "hired": 0,
        }
        application_result = await db.execute(application_status_query)
        for status, count in application_result.all():
            application_counts[status] = int(count)

        exchange_counts = {"pending": 0, "accepted": 0, "declined": 0}
        exchange_result = await db.execute(exchange_status_query)
        for status, count in exchange_result.all():
            exchange_counts[status] = int(count)

        processed_count = (
            application_counts["viewed"]
            + application_counts["interview_invited"]
            + application_counts["rejected"]
            + application_counts["hired"]
        )
        application_total = sum(application_counts.values())
        exchange_total = sum(exchange_counts.values())

        return {
            "job_count": job_count,
            "view_count": view_count,
            "conversation_count": conversation_count,
            "application_count": application_total,
            "submitted_count": application_counts["submitted"],
            "processed_count": processed_count,
            "viewed_count": application_counts["viewed"],
            "interview_invited_count": application_counts["interview_invited"],
            "rejected_count": application_counts["rejected"],
            "hired_count": application_counts["hired"],
            "contact_exchange_count": exchange_total,
            "successful_connection_count": exchange_counts["accepted"],
            "pending_exchange_count": exchange_counts["pending"],
            "declined_exchange_count": exchange_counts["declined"],
        }

    @staticmethod
    async def deep_dive_stats(
        db: AsyncSession,
        *,
        recruiter_id: Optional[int] = None,
        days: int = 7,
        limit: int = 5,
    ) -> dict:
        days = max(1, min(days, 30))
        limit = max(1, min(limit, 20))
        today = date.today()
        start_date = today - timedelta(days=days - 1)
        start_at = datetime.combine(start_date, datetime.min.time())

        job_filters = []
        conversation_filters = []
        application_filters = []
        exchange_filters = []
        if recruiter_id is not None:
            job_filters.append(Job.recruiter_id == recruiter_id)
            conversation_filters.append(Conversation.recruiter_id == recruiter_id)
            application_filters.append(JobApplication.recruiter_id == recruiter_id)
            exchange_filters.append(Conversation.recruiter_id == recruiter_id)

        trend = {
            (start_date + timedelta(days=offset)).isoformat(): {
                "date": (start_date + timedelta(days=offset)).isoformat(),
                "view_count": 0,
                "conversation_count": 0,
                "application_count": 0,
                "successful_connection_count": 0,
            }
            for offset in range(days)
        }

        # Job.view_count is cumulative, so trend uses daily visit rows rather than the job aggregate column.
        from app.modules.job.models import JobVisit

        visit_query = (
            select(func.date(JobVisit.viewed_at), func.count(JobVisit.id))
            .where(JobVisit.viewed_at >= start_at)
            .group_by(func.date(JobVisit.viewed_at))
        )
        if recruiter_id is not None:
            visit_query = visit_query.where(JobVisit.recruiter_id == recruiter_id)
        for day, count in (await db.execute(visit_query)).all():
            key = str(day)
            if key in trend:
                trend[key]["view_count"] = int(count or 0)

        conversation_query = (
            select(func.date(Conversation.created_at), func.count(Conversation.id))
            .where(Conversation.created_at >= start_at)
            .group_by(func.date(Conversation.created_at))
        )
        if conversation_filters:
            conversation_query = conversation_query.where(*conversation_filters)
        for day, count in (await db.execute(conversation_query)).all():
            key = str(day)
            if key in trend:
                trend[key]["conversation_count"] = int(count or 0)

        application_query = (
            select(func.date(JobApplication.created_at), func.count(JobApplication.id))
            .where(JobApplication.created_at >= start_at)
            .group_by(func.date(JobApplication.created_at))
        )
        if application_filters:
            application_query = application_query.where(*application_filters)
        for day, count in (await db.execute(application_query)).all():
            key = str(day)
            if key in trend:
                trend[key]["application_count"] = int(count or 0)

        exchange_query = (
            select(func.date(ContactExchange.responded_at), func.count(ContactExchange.id))
            .select_from(ContactExchange)
            .join(Conversation, Conversation.id == ContactExchange.conversation_id)
            .where(
                ContactExchange.status == "accepted",
                ContactExchange.responded_at >= start_at,
            )
            .group_by(func.date(ContactExchange.responded_at))
        )
        if exchange_filters:
            exchange_query = exchange_query.where(*exchange_filters)
        for day, count in (await db.execute(exchange_query)).all():
            key = str(day)
            if key in trend:
                trend[key]["successful_connection_count"] = int(count or 0)

        applications_by_job = (
            select(JobApplication.job_id.label("job_id"), func.count(JobApplication.id).label("application_count"))
            .group_by(JobApplication.job_id)
            .subquery()
        )
        conversations_by_job = (
            select(Conversation.job_id.label("job_id"), func.count(Conversation.id).label("conversation_count"))
            .group_by(Conversation.job_id)
            .subquery()
        )
        accepted_by_job = (
            select(Conversation.job_id.label("job_id"), func.count(ContactExchange.id).label("accepted_count"))
            .select_from(ContactExchange)
            .join(Conversation, Conversation.id == ContactExchange.conversation_id)
            .where(ContactExchange.status == "accepted")
            .group_by(Conversation.job_id)
            .subquery()
        )
        ranking_query = (
            select(
                Job.id,
                Job.title,
                Job.status,
                func.coalesce(Job.view_count, 0),
                func.coalesce(conversations_by_job.c.conversation_count, 0),
                func.coalesce(applications_by_job.c.application_count, 0),
                func.coalesce(accepted_by_job.c.accepted_count, 0),
            )
            .outerjoin(conversations_by_job, conversations_by_job.c.job_id == Job.id)
            .outerjoin(applications_by_job, applications_by_job.c.job_id == Job.id)
            .outerjoin(accepted_by_job, accepted_by_job.c.job_id == Job.id)
            .order_by(
                func.coalesce(Job.view_count, 0).desc(),
                func.coalesce(applications_by_job.c.application_count, 0).desc(),
                Job.id.desc(),
            )
            .limit(limit)
        )
        if recruiter_id is not None:
            ranking_query = ranking_query.where(Job.recruiter_id == recruiter_id)

        top_jobs = []
        for job_id, title, job_status, views, conversations, applications, accepted in (await db.execute(ranking_query)).all():
            views = int(views or 0)
            applications = int(applications or 0)
            accepted = int(accepted or 0)
            top_jobs.append(
                {
                    "job_id": int(job_id),
                    "title": title,
                    "status": job_status,
                    "view_count": views,
                    "conversation_count": int(conversations or 0),
                    "application_count": applications,
                    "successful_connection_count": accepted,
                    "application_rate": round((applications / views) * 100, 1) if views > 0 else 0,
                    "connection_rate": round((accepted / applications) * 100, 1) if applications > 0 else 0,
                }
            )

        return {
            "summary": await ApplicationRepository.business_loop_stats(db, recruiter_id=recruiter_id),
            "trend_days": days,
            "trend": list(trend.values()),
            "top_jobs": top_jobs,
            "application_status_distribution": await ApplicationRepository.count_by_status(db, recruiter_id=recruiter_id),
        }

    @staticmethod
    async def admin_operations_stats(db: AsyncSession) -> dict[str, int]:
        from app.modules.company_certification.models import CompanyCertification
        from app.modules.user.models import User

        today_start = _utc_day_start()

        today_new_user_count = int(
            (await db.execute(select(func.count()).select_from(User).where(User.created_at >= today_start))).scalar_one() or 0
        )
        today_new_job_count = int(
            (await db.execute(select(func.count()).select_from(Job).where(Job.created_at >= today_start))).scalar_one() or 0
        )
        today_new_application_count = int(
            (
                await db.execute(
                    select(func.count()).select_from(JobApplication).where(JobApplication.created_at >= today_start)
                )
            ).scalar_one()
            or 0
        )
        active_job_count = int(
            (await db.execute(select(func.count()).select_from(Job).where(Job.status == "active"))).scalar_one() or 0
        )
        pending_job_review_count = int(
            (await db.execute(select(func.count()).select_from(Job).where(Job.status == "pending"))).scalar_one() or 0
        )

        cert_result = await db.execute(
            select(CompanyCertification.status, func.count(CompanyCertification.id)).group_by(CompanyCertification.status)
        )
        cert_counts = {"pending": 0, "approved": 0, "rejected": 0}
        for status, count in cert_result.all():
            cert_counts[status] = int(count)

        application_counts = await ApplicationRepository.count_by_status(db)
        processed_count = (
            application_counts["viewed"]
            + application_counts["interview_invited"]
            + application_counts["rejected"]
            + application_counts["hired"]
        )
        application_total = sum(application_counts.values())
        certification_total = sum(cert_counts.values())

        return {
            "today_new_user_count": today_new_user_count,
            "today_new_job_count": today_new_job_count,
            "today_new_application_count": today_new_application_count,
            "active_job_count": active_job_count,
            "pending_job_review_count": pending_job_review_count,
            "pending_certification_count": cert_counts["pending"],
            "approved_certification_count": cert_counts["approved"],
            "rejected_certification_count": cert_counts["rejected"],
            "certification_total_count": certification_total,
            "processed_application_count": processed_count,
            "application_total_count": application_total,
        }

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
