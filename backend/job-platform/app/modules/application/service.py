"""
Job application business logic.
"""
from datetime import datetime, timezone
import mimetypes
from pathlib import Path, PurePosixPath
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.application.models import JobApplication, JobApplicationTimeline
from app.modules.application.repository import ApplicationRepository
from app.modules.application.schemas import (
    AdminOperationsStatsResponse,
    ApplicationCreate,
    ApplicationCoverLetterSuggestResponse,
    ApplicationDetailResponse,
    ApplicationListResponse,
    ApplicationResponse,
    ApplicationStatsResponse,
    ApplicationStatusUpdate,
    ApplicationTimelineResponse,
    BusinessLoopStatsResponse,
    DeepDiveStatsResponse,
)
from app.modules.job.repository import JobRepository
from app.modules.notification.service import NotificationService
from app.modules.resume.repository import ResumeRepository
from app.modules.user.models import User


VALID_APPLICATION_STATUSES = {"submitted", "viewed", "interview_invited", "rejected", "hired"}
RECRUITER_TARGET_STATUSES = {"viewed", "interview_invited", "rejected", "hired"}


def _to_response(application: JobApplication) -> ApplicationResponse:
    job = application.job
    seeker = application.seeker
    recruiter = application.recruiter
    return ApplicationResponse(
        id=application.id,
        job_id=application.job_id,
        job_title=job.title if job else None,
        job_city=job.city if job else None,
        seeker_id=application.seeker_id,
        seeker_display_name=seeker.display_name if seeker else None,
        recruiter_id=application.recruiter_id,
        recruiter_display_name=recruiter.display_name if recruiter else None,
        resume_id=application.resume_id,
        resume_file_url=application.resume_file_url,
        resume_file_name=application.resume_file_name,
        status=application.status,
        resume_snapshot=application.resume_snapshot,
        cover_message=application.cover_message,
        reject_reason=application.reject_reason,
        viewed_at=application.viewed_at,
        status_updated_at=application.status_updated_at,
        created_at=application.created_at,
        updated_at=application.updated_at,
    )


def _to_timeline_response(timeline: JobApplicationTimeline) -> ApplicationTimelineResponse:
    return ApplicationTimelineResponse(
        id=timeline.id,
        application_id=timeline.application_id,
        from_status=timeline.from_status,
        to_status=timeline.to_status,
        actor_id=timeline.actor_id,
        actor_role=timeline.actor_role,
        note=timeline.note,
        created_at=timeline.created_at,
    )


def _to_detail_response(
    application: JobApplication,
    timeline: list[JobApplicationTimeline],
) -> ApplicationDetailResponse:
    base = _to_response(application).model_dump()
    return ApplicationDetailResponse(
        **base,
        timeline=[_to_timeline_response(item) for item in timeline],
    )


def _resume_file_path(file_url: Optional[str]) -> Path:
    if not file_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume file not found")
    if not file_url.startswith("/uploads/"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume file not found")

    uploads_root = Path("uploads").resolve()
    relative_parts = PurePosixPath(file_url.removeprefix("/uploads/")).parts
    target = uploads_root.joinpath(*relative_parts).resolve()
    if uploads_root != target and uploads_root not in target.parents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume file not found")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume file not found")
    return target


class ApplicationService:
    """Job application use cases."""

    @staticmethod
    def _rate(numerator: int, denominator: int) -> float:
        if denominator <= 0:
            return 0
        return round((numerator / denominator) * 100, 1)

    @staticmethod
    async def create(db: AsyncSession, current_user: User, data: ApplicationCreate) -> ApplicationResponse:
        if current_user.role != "seeker":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only seekers can apply to jobs")

        job = await JobRepository.get_by_id(db, data.job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        if job.status != "active":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only active jobs can receive applications")

        existing = await ApplicationRepository.get_by_job_and_seeker(db, data.job_id, current_user.id)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You have already applied to this job")
        resume = await ResumeRepository.get_by_seeker_id(db, current_user.id)
        if resume is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please upload a resume before applying")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        application = JobApplication(
            job_id=job.id,
            seeker_id=current_user.id,
            recruiter_id=job.recruiter_id,
            resume_id=resume.id,
            status="submitted",
            resume_snapshot=resume.parsed_snapshot,
            resume_file_url=resume.file_url,
            resume_file_name=resume.file_name,
            cover_message=data.cover_message,
            status_updated_at=now,
        )
        created = await ApplicationRepository.create(db, application, commit=False)
        await ApplicationRepository.add_timeline(
            db,
            JobApplicationTimeline(
                application_id=created.id,
                from_status=None,
                to_status="submitted",
                actor_id=current_user.id,
                actor_role="seeker",
                note="Application submitted",
                created_at=created.created_at,
            ),
        )
        created.job = job
        created.seeker = current_user
        created.recruiter = job.recruiter
        await NotificationService.notify_application_submitted(db, application=created, commit=False)
        await db.commit()
        await db.refresh(created)
        return _to_response(created)

    @staticmethod
    async def suggest_cover_letter(
        db: AsyncSession,
        current_user: User,
        job_id: int,
    ) -> ApplicationCoverLetterSuggestResponse:
        if current_user.role != "seeker":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only seekers can generate cover letters")

        job = await JobRepository.get_by_id(db, job_id)
        if job is None or job.status != "active":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        profile = await ResumeRepository.get_latest_structured_profile(db, current_user.id)
        basic = await ResumeRepository.get_basic_info_by_profile_id(db, profile.id) if profile else None
        skills = await ResumeRepository.list_skills_by_profile_id(db, profile.id) if profile else []
        skill_names = [item.skill_name for item in skills if item.skill_name]
        job_terms = [item for item in [job.title, *(job.tags or [])] if item]
        matched_skills = [
            skill for skill in skill_names
            if any(skill.lower() in term.lower() or term.lower() in skill.lower() for term in job_terms)
        ][:4]

        display_name = (basic.real_name if basic and basic.real_name else current_user.display_name) or "您好"
        target = basic.target_position if basic and basic.target_position else job.title
        work_years = f"{basic.work_years:g}年经验" if basic and basic.work_years else None
        education = basic.highest_education if basic and basic.highest_education else None
        highlights = [item for item in [work_years, education, *matched_skills] if item][:5]

        if highlights:
            highlight_text = "、".join(highlights)
            cover_message = (
                f"您好，我是{display_name}，希望投递「{job.title}」。"
                f"我的目标方向是{target}，与岗位要求较匹配；相关亮点包括：{highlight_text}。"
                "如有机会，我希望进一步沟通岗位职责和团队需求，谢谢。"
            )
        else:
            cover_message = (
                f"您好，我希望投递「{job.title}」。我已上传简历，"
                "对该岗位职责和发展方向比较感兴趣，期待有机会进一步沟通，谢谢。"
            )

        return ApplicationCoverLetterSuggestResponse(
            job_id=job.id,
            cover_message=cover_message[:1000],
            source="rule_fallback",
            highlights=highlights,
            fallback_used=True,
        )

    @staticmethod
    async def list_my_applications(
        db: AsyncSession,
        current_user: User,
        skip: int = 0,
        limit: int = 20,
        status_filter: Optional[str] = None,
    ) -> ApplicationListResponse:
        if status_filter and status_filter not in VALID_APPLICATION_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid application status")
        items, total = await ApplicationRepository.list_by_seeker(
            db,
            seeker_id=current_user.id,
            skip=skip,
            limit=limit,
            status=status_filter,
        )
        return ApplicationListResponse(
            items=[_to_response(item) for item in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    async def get_recruiter_stats(
        db: AsyncSession,
        current_user: User,
    ) -> ApplicationStatsResponse:
        counts = await ApplicationRepository.count_by_status(db, recruiter_id=current_user.id)
        return ApplicationStatsResponse(
            submitted_count=counts["submitted"],
            viewed_count=counts["viewed"],
            interview_invited_count=counts["interview_invited"],
            rejected_count=counts["rejected"],
            hired_count=counts["hired"],
            total_count=sum(counts.values()),
        )

    @staticmethod
    async def get_admin_stats(db: AsyncSession) -> ApplicationStatsResponse:
        counts = await ApplicationRepository.count_by_status(db)
        return ApplicationStatsResponse(
            submitted_count=counts["submitted"],
            viewed_count=counts["viewed"],
            interview_invited_count=counts["interview_invited"],
            rejected_count=counts["rejected"],
            hired_count=counts["hired"],
            total_count=sum(counts.values()),
        )

    @staticmethod
    async def get_recruiter_business_loop_stats(
        db: AsyncSession,
        current_user: User,
    ) -> BusinessLoopStatsResponse:
        return ApplicationService._business_loop_response(
            await ApplicationRepository.business_loop_stats(db, recruiter_id=current_user.id)
        )

    @staticmethod
    async def get_admin_business_loop_stats(db: AsyncSession) -> BusinessLoopStatsResponse:
        return ApplicationService._business_loop_response(
            await ApplicationRepository.business_loop_stats(db)
        )

    @staticmethod
    async def get_recruiter_deep_dive_stats(
        db: AsyncSession,
        current_user: User,
        days: int = 7,
        limit: int = 5,
    ) -> DeepDiveStatsResponse:
        stats = await ApplicationRepository.deep_dive_stats(
            db,
            recruiter_id=current_user.id,
            days=days,
            limit=limit,
        )
        return DeepDiveStatsResponse(
            summary=ApplicationService._business_loop_response(stats["summary"]),
            trend_days=stats["trend_days"],
            trend=stats["trend"],
            top_jobs=stats["top_jobs"],
            application_status_distribution=stats["application_status_distribution"],
        )

    @staticmethod
    async def get_admin_deep_dive_stats(
        db: AsyncSession,
        days: int = 7,
        limit: int = 5,
    ) -> DeepDiveStatsResponse:
        stats = await ApplicationRepository.deep_dive_stats(db, days=days, limit=limit)
        return DeepDiveStatsResponse(
            summary=ApplicationService._business_loop_response(stats["summary"]),
            trend_days=stats["trend_days"],
            trend=stats["trend"],
            top_jobs=stats["top_jobs"],
            application_status_distribution=stats["application_status_distribution"],
        )

    @staticmethod
    async def get_admin_operations_stats(db: AsyncSession) -> AdminOperationsStatsResponse:
        stats = await ApplicationRepository.admin_operations_stats(db)
        return AdminOperationsStatsResponse(
            today_new_user_count=stats["today_new_user_count"],
            today_new_job_count=stats["today_new_job_count"],
            today_new_application_count=stats["today_new_application_count"],
            active_job_count=stats["active_job_count"],
            pending_job_review_count=stats["pending_job_review_count"],
            pending_certification_count=stats["pending_certification_count"],
            approved_certification_count=stats["approved_certification_count"],
            rejected_certification_count=stats["rejected_certification_count"],
            certification_total_count=stats["certification_total_count"],
            certification_approval_rate=ApplicationService._rate(
                stats["approved_certification_count"],
                stats["certification_total_count"],
            ),
            application_process_rate=ApplicationService._rate(
                stats["processed_application_count"],
                stats["application_total_count"],
            ),
        )

    @staticmethod
    def _business_loop_response(stats: dict[str, int]) -> BusinessLoopStatsResponse:
        return BusinessLoopStatsResponse(
            **stats,
            view_to_conversation_rate=ApplicationService._rate(
                stats["conversation_count"],
                stats["view_count"],
            ),
            conversation_to_application_rate=ApplicationService._rate(
                stats["application_count"],
                stats["conversation_count"],
            ),
            application_process_rate=ApplicationService._rate(
                stats["processed_count"],
                stats["application_count"],
            ),
            application_to_connection_rate=ApplicationService._rate(
                stats["successful_connection_count"],
                stats["application_count"],
            ),
        )

    @staticmethod
    async def get_for_recruiter(
        db: AsyncSession,
        current_user: User,
        application_id: int,
    ) -> ApplicationDetailResponse:
        application = await ApplicationRepository.get_by_id(db, application_id)
        if application is None or application.recruiter_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        timeline = await ApplicationRepository.list_timelines(db, application.id)
        return _to_detail_response(application, timeline)

    @staticmethod
    async def get_for_seeker(
        db: AsyncSession,
        current_user: User,
        application_id: int,
    ) -> ApplicationDetailResponse:
        application = await ApplicationRepository.get_by_id(db, application_id)
        if application is None or application.seeker_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        timeline = await ApplicationRepository.list_timelines(db, application.id)
        return _to_detail_response(application, timeline)

    @staticmethod
    async def get_resume_file_for_recruiter(
        db: AsyncSession,
        current_user: User,
        application_id: int,
    ) -> tuple[Path, str, Optional[str]]:
        application = await ApplicationRepository.get_by_id(db, application_id)
        if application is None or application.recruiter_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        path = _resume_file_path(application.resume_file_url)
        media_type = mimetypes.guess_type(application.resume_file_name or path.name)[0] or "application/octet-stream"
        return path, application.resume_file_name or path.name, media_type

    @staticmethod
    async def list_for_recruiter(
        db: AsyncSession,
        current_user: User,
        skip: int = 0,
        limit: int = 20,
        status_filter: Optional[str] = None,
    ) -> ApplicationListResponse:
        if status_filter and status_filter not in VALID_APPLICATION_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid application status")
        items, total = await ApplicationRepository.list_by_recruiter(
            db,
            recruiter_id=current_user.id,
            skip=skip,
            limit=limit,
            status=status_filter,
        )
        return ApplicationListResponse(
            items=[_to_response(item) for item in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    async def list_for_admin(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        status_filter: Optional[str] = None,
    ) -> ApplicationListResponse:
        if status_filter and status_filter not in VALID_APPLICATION_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid application status")
        items, total = await ApplicationRepository.list_for_admin(db, skip=skip, limit=limit, status=status_filter)
        return ApplicationListResponse(
            items=[_to_response(item) for item in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    async def update_status(
        db: AsyncSession,
        application_id: int,
        current_user: User,
        data: ApplicationStatusUpdate,
    ) -> ApplicationResponse:
        if data.status not in RECRUITER_TARGET_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid target status")

        application = await ApplicationRepository.get_by_id(db, application_id)
        if application is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        if application.recruiter_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        if data.status == "rejected" and not data.reject_reason:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reject reason is required")

        old_status = application.status
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        application.status = data.status
        application.status_updated_at = now
        application.reject_reason = data.reject_reason if data.status == "rejected" else None
        if data.status in {"viewed", "interview_invited", "rejected", "hired"} and application.viewed_at is None:
            application.viewed_at = now
        await ApplicationRepository.add_timeline(
            db,
            JobApplicationTimeline(
                application_id=application.id,
                from_status=old_status,
                to_status=data.status,
                actor_id=current_user.id,
                actor_role="recruiter",
                note=data.reject_reason if data.status == "rejected" else None,
                created_at=now,
            ),
        )

        updated = await ApplicationRepository.update(db, application, commit=False)
        await NotificationService.notify_application_status_changed(
            db,
            application=updated,
            old_status=old_status,
            new_status=data.status,
            reject_reason=data.reject_reason,
            commit=False,
        )
        await db.commit()
        await db.refresh(updated)
        return _to_response(updated)
