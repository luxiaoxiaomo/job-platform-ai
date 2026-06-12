"""
Job posting business logic.
"""
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.company_certification.repository import CompanyCertificationRepository
from app.modules.job.jd_parser import ALLOWED_JD_EXTENSIONS, extract_jd_text, parse_jd_fields
from app.modules.job.models import Job
from app.modules.job.repository import JobRepository
from app.modules.job.salary import suggest_salary
from app.modules.job.schemas import (
    JobCreate,
    JobJdParseResponse,
    JobJdTextParseRequest,
    JobListResponse,
    JobResponse,
    JobReview,
    JobSalarySuggestionRequest,
    JobSalarySuggestionResponse,
    JobUpdate,
)
from app.modules.user.models import User


VALID_STATUSES = {"draft", "pending", "active", "closed", "rejected"}


def _to_response(job: Job) -> JobResponse:
    recruiter = job.recruiter
    return JobResponse(
        id=job.id,
        recruiter_id=job.recruiter_id,
        recruiter_display_name=recruiter.display_name if recruiter else None,
        title=job.title,
        city=job.city,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        experience=job.experience,
        education=job.education,
        description=job.description,
        requirement=job.requirement,
        benefits=job.benefits,
        tags=job.tags,
        status=job.status,
        reject_reason=job.reject_reason,
        reviewer_id=job.reviewer_id,
        reviewed_at=job.reviewed_at,
        published_at=job.published_at,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


class JobService:
    """Job posting use cases."""

    allowed_jd_extensions = ALLOWED_JD_EXTENSIONS

    @staticmethod
    async def _ensure_recruiter_can_publish(db: AsyncSession, current_user: User) -> None:
        if current_user.role != "recruiter":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only recruiters can publish jobs",
            )

        certification = await CompanyCertificationRepository.get_by_recruiter_id(db, current_user.id)
        if certification is None or certification.status != "approved":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Enterprise certification must be approved before publishing jobs",
            )

    @staticmethod
    async def create(db: AsyncSession, current_user: User, data: JobCreate) -> JobResponse:
        await JobService._ensure_recruiter_can_publish(db, current_user)

        job = Job(
            recruiter_id=current_user.id,
            title=data.title,
            city=data.city,
            salary_min=data.salary_min,
            salary_max=data.salary_max,
            experience=data.experience,
            education=data.education,
            description=data.description,
            requirement=data.requirement,
            benefits=data.benefits,
            tags=data.tags,
            status="pending",
        )
        created = await JobRepository.create(db, job)
        created.recruiter = current_user
        return _to_response(created)

    @staticmethod
    async def parse_jd_upload(current_user: User, file: UploadFile) -> JobJdParseResponse:
        if current_user.role != "recruiter":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only recruiters can parse JD files",
            )

        original_name = file.filename or "job-description"
        extension = Path(original_name).suffix.lower()
        if extension not in JobService.allowed_jd_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only txt, md, csv, docx, xlsx, pdf, and common image formats are supported",
            )

        content = await file.read()
        if not content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file cannot be empty")
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Uploaded file is too large")

        upload_dir = Path("uploads") / "job_jds"
        upload_dir.mkdir(parents=True, exist_ok=True)
        saved_name = f"{current_user.id}_{uuid4().hex}{extension}"
        saved_path = upload_dir / saved_name
        saved_path.write_bytes(content)

        raw_text, confidence, source = await extract_jd_text(saved_path, original_name, content)
        if not raw_text.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No readable JD text was extracted from the uploaded file",
            )

        parsed = parse_jd_fields(raw_text, source=source, confidence=confidence)
        return JobJdParseResponse(
            file_name=original_name,
            source=parsed.source,
            confidence=parsed.confidence,
            raw_text=parsed.raw_text,
            title=parsed.title,
            city=parsed.city,
            salary_min=parsed.salary_min,
            salary_max=parsed.salary_max,
            experience=parsed.experience,
            education=parsed.education,
            description=parsed.description,
            requirement=parsed.requirement,
            benefits=parsed.benefits,
            tags=parsed.tags,
            missing_fields=parsed.missing_fields,
        )

    @staticmethod
    async def parse_jd_text(current_user: User, data: JobJdTextParseRequest) -> JobJdParseResponse:
        if current_user.role != "recruiter":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only recruiters can parse JD text",
            )

        parsed = parse_jd_fields(data.text, source="pasted_text", confidence=1.0)
        return JobJdParseResponse(
            file_name="pasted-jd.txt",
            source=parsed.source,
            confidence=parsed.confidence,
            raw_text=parsed.raw_text,
            title=parsed.title,
            city=parsed.city,
            salary_min=parsed.salary_min,
            salary_max=parsed.salary_max,
            experience=parsed.experience,
            education=parsed.education,
            description=parsed.description,
            requirement=parsed.requirement,
            benefits=parsed.benefits,
            tags=parsed.tags,
            missing_fields=parsed.missing_fields,
        )

    @staticmethod
    async def suggest_salary(current_user: User, data: JobSalarySuggestionRequest) -> JobSalarySuggestionResponse:
        if current_user.role != "recruiter":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only recruiters can get salary suggestions",
            )
        return suggest_salary(data)

    @staticmethod
    async def list_my_jobs(
        db: AsyncSession,
        current_user: User,
        skip: int = 0,
        limit: int = 20,
        status_filter: Optional[str] = None,
    ) -> JobListResponse:
        if status_filter and status_filter not in VALID_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job status")

        items, total = await JobRepository.list_by_recruiter(
            db,
            recruiter_id=current_user.id,
            skip=skip,
            limit=limit,
            status=status_filter,
        )
        return JobListResponse(
            items=[_to_response(item) for item in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    async def list_public_jobs(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        city: Optional[str] = None,
    ) -> JobListResponse:
        items, total = await JobRepository.list_public_active(db, skip=skip, limit=limit, city=city)
        return JobListResponse(
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
    ) -> JobListResponse:
        if status_filter and status_filter not in VALID_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job status")

        items, total = await JobRepository.list_for_admin(db, skip=skip, limit=limit, status=status_filter)
        return JobListResponse(
            items=[_to_response(item) for item in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    async def get_for_admin(db: AsyncSession, job_id: int) -> JobResponse:
        job = await JobRepository.get_by_id(db, job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        return _to_response(job)

    @staticmethod
    async def update_my_job(db: AsyncSession, current_user: User, job_id: int, data: JobUpdate) -> JobResponse:
        job = await JobRepository.get_by_id(db, job_id)
        if job is None or job.recruiter_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        payload = data.model_dump(exclude_unset=True)
        if "salary_max" in payload and "salary_min" not in payload and payload["salary_max"] < job.salary_min:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid salary range")
        if "salary_min" in payload and "salary_max" not in payload and payload["salary_min"] > job.salary_max:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid salary range")

        for field, value in payload.items():
            setattr(job, field, value)

        if payload:
            job.status = "pending"
            job.reject_reason = None
            job.reviewer_id = None
            job.reviewed_at = None
            job.published_at = None

        updated = await JobRepository.update(db, job)
        return _to_response(updated)

    @staticmethod
    async def review(db: AsyncSession, job_id: int, reviewer: User, data: JobReview) -> JobResponse:
        job = await JobRepository.get_by_id(db, job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        if data.action == "reject" and not data.reject_reason:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reject reason is required")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        job.status = "active" if data.action == "approve" else "rejected"
        job.reject_reason = None if data.action == "approve" else data.reject_reason
        job.reviewer_id = reviewer.id
        job.reviewed_at = now
        job.published_at = now if data.action == "approve" else None

        updated = await JobRepository.update(db, job)
        return _to_response(updated)
