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
    ApplicationCreate,
    ApplicationDetailResponse,
    ApplicationListResponse,
    ApplicationResponse,
    ApplicationStatusUpdate,
    ApplicationTimelineResponse,
)
from app.modules.job.repository import JobRepository
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
        created = await ApplicationRepository.create(db, application)
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
        await db.commit()
        created.job = job
        created.seeker = current_user
        created.recruiter = job.recruiter
        return _to_response(created)

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

        updated = await ApplicationRepository.update(db, application)
        return _to_response(updated)
