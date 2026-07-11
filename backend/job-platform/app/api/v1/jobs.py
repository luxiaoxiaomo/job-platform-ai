"""
Job posting API.
"""
from typing import Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_optional_current_user, require_role
from app.db.session import get_db
from app.modules.job.schemas import (
    JobCreate,
    JobFavoriteListResponse,
    JobFavoriteResponse,
    JobHistoryListResponse,
    JobJdParseResponse,
    JobJdTextParseRequest,
    JobListResponse,
    JobResponse,
    JobSubscriptionCreate,
    JobSubscriptionListResponse,
    JobSubscriptionResponse,
    JobSubscriptionUpdate,
    JobVisitorListResponse,
    SeekerNotificationListResponse,
    JobReview,
    JobSalarySuggestionRequest,
    JobSalarySuggestionResponse,
    JobUpdate,
)
from app.modules.job.service import JobService
from app.modules.user.models import User

router = APIRouter()


@router.post("/me", response_model=JobResponse, status_code=http_status.HTTP_201_CREATED)
async def create_my_job(
    data: JobCreate,
    current_user: User = Depends(require_role("recruiter")),
    db: AsyncSession = Depends(get_db),
):
    """Submit a recruiter job. New jobs enter pending review by default."""
    return await JobService.create(db, current_user, data)


@router.get("/me", response_model=JobListResponse)
async def list_my_jobs(
    status: Optional[str] = Query(None, description="draft/pending/active/closed/rejected"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role("recruiter")),
    db: AsyncSession = Depends(get_db),
):
    """List current recruiter's jobs."""
    return await JobService.list_my_jobs(
        db,
        current_user,
        skip=skip,
        limit=limit,
        status_filter=status,
    )


@router.post("/parse-jd", response_model=JobJdParseResponse)
async def parse_jd_file(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("recruiter")),
):
    """Upload a JD document and return extracted text plus parsed job fields."""
    return await JobService.parse_jd_upload(current_user, file)


@router.post("/parse-jd-text", response_model=JobJdParseResponse)
async def parse_jd_text(
    data: JobJdTextParseRequest,
    current_user: User = Depends(require_role("recruiter")),
):
    """Parse a pasted full JD text and return structured job fields."""
    return await JobService.parse_jd_text(current_user, data)


@router.post("/salary-suggestion", response_model=JobSalarySuggestionResponse)
async def suggest_job_salary(
    data: JobSalarySuggestionRequest,
    current_user: User = Depends(require_role("recruiter")),
):
    """Return rule-based salary suggestion for the current job draft."""
    return await JobService.suggest_salary(current_user, data)


@router.put("/me/{job_id}", response_model=JobResponse)
async def update_my_job(
    job_id: int,
    data: JobUpdate,
    current_user: User = Depends(require_role("recruiter")),
    db: AsyncSession = Depends(get_db),
):
    """Update a recruiter's job. Content changes send it back to pending review."""
    return await JobService.update_my_job(db, current_user, job_id, data)


@router.post("/me/{job_id}/submit-review", response_model=JobResponse)
async def submit_my_job_for_review(
    job_id: int,
    current_user: User = Depends(require_role("recruiter")),
    db: AsyncSession = Depends(get_db),
):
    """Submit a draft or rejected recruiter-owned job for review."""
    return await JobService.submit_my_job_for_review(db, current_user, job_id)


@router.get("/me/{job_id}/visitors", response_model=JobVisitorListResponse)
async def list_my_job_visitors(
    job_id: int,
    sort: str = Query("intent", description="intent/views/time"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role("recruiter")),
    db: AsyncSession = Depends(get_db),
):
    """List real seeker visitors for one recruiter-owned job."""
    return await JobService.list_job_visitors(
        db,
        current_user,
        job_id,
        skip=skip,
        limit=limit,
        sort=sort,
    )


@router.get("/public", response_model=JobListResponse)
async def list_public_jobs(
    city: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List jobs visible to seekers. Only approved active jobs are returned."""
    return await JobService.list_public_jobs(db, skip=skip, limit=limit, city=city)


@router.get("/public/{job_id}", response_model=JobResponse)
async def get_public_job(
    job_id: int,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get one job visible to seekers. Only approved active jobs are returned."""
    return await JobService.get_public_job(db, job_id, current_user)


@router.get("/seeker/history", response_model=JobHistoryListResponse)
async def list_my_job_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """List current seeker's real browsing history."""
    return await JobService.list_my_history(db, current_user, skip=skip, limit=limit)


@router.get("/seeker/favorites", response_model=JobFavoriteListResponse)
async def list_my_job_favorites(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """List current seeker's saved jobs."""
    return await JobService.list_my_favorites(db, current_user, skip=skip, limit=limit)


@router.post("/seeker/favorites/{job_id}", response_model=JobFavoriteResponse, status_code=http_status.HTTP_201_CREATED)
async def add_my_job_favorite(
    job_id: int,
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """Save one active job for the current seeker."""
    return await JobService.add_my_favorite(db, current_user, job_id)


@router.delete("/seeker/favorites/{job_id}")
async def remove_my_job_favorite(
    job_id: int,
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """Remove one saved job for the current seeker."""
    return await JobService.remove_my_favorite(db, current_user, job_id)


@router.get("/seeker/subscriptions", response_model=JobSubscriptionListResponse)
async def list_my_job_subscriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """List current seeker's job-alert subscriptions."""
    return await JobService.list_my_subscriptions(db, current_user, skip=skip, limit=limit)


@router.get("/seeker/notifications", response_model=SeekerNotificationListResponse)
async def list_my_seeker_notifications(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """List computed seeker notifications, including subscription match alerts."""
    return await JobService.list_my_notifications(db, current_user, limit=limit)


@router.post("/seeker/subscriptions", response_model=JobSubscriptionResponse, status_code=http_status.HTTP_201_CREATED)
async def create_my_job_subscription(
    data: JobSubscriptionCreate,
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """Create a job-alert subscription for the current seeker."""
    return await JobService.create_my_subscription(db, current_user, data)


@router.put("/seeker/subscriptions/{subscription_id}", response_model=JobSubscriptionResponse)
async def update_my_job_subscription(
    subscription_id: int,
    data: JobSubscriptionUpdate,
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """Update a job-alert subscription for the current seeker."""
    return await JobService.update_my_subscription(db, current_user, subscription_id, data)


@router.delete("/seeker/subscriptions/{subscription_id}")
async def delete_my_job_subscription(
    subscription_id: int,
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a job-alert subscription for the current seeker."""
    return await JobService.delete_my_subscription(db, current_user, subscription_id)


@router.get("/admin", response_model=JobListResponse)
async def list_jobs_for_admin(
    status: Optional[str] = Query(None, description="draft/pending/active/closed/rejected"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """List jobs for admin review."""
    return await JobService.list_for_admin(db, skip=skip, limit=limit, status_filter=status)


@router.get("/admin/{job_id}", response_model=JobResponse)
async def get_job_for_admin(
    job_id: int,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Get one job for admin review."""
    return await JobService.get_for_admin(db, job_id)


@router.post("/admin/{job_id}/review", response_model=JobResponse)
async def review_job(
    job_id: int,
    data: JobReview,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject a pending job."""
    return await JobService.review(db, job_id, current_user, data)
