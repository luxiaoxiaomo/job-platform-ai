"""
Job application API.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, status as http_status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.modules.application.schemas import (
    AdminOperationsStatsResponse,
    ApplicationCreate,
    ApplicationCoverLetterSuggestRequest,
    ApplicationCoverLetterSuggestResponse,
    ApplicationDetailResponse,
    ApplicationListResponse,
    ApplicationResponse,
    ApplicationStatsResponse,
    ApplicationStatusUpdate,
    BusinessLoopStatsResponse,
    DeepDiveStatsResponse,
)
from app.modules.application.service import ApplicationService
from app.modules.user.models import User

router = APIRouter()


@router.post("", response_model=ApplicationResponse, status_code=http_status.HTTP_201_CREATED)
async def create_application(
    data: ApplicationCreate,
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """Apply to an active public job."""
    return await ApplicationService.create(db, current_user, data)


@router.post("/cover-letter/suggest", response_model=ApplicationCoverLetterSuggestResponse)
async def suggest_application_cover_letter(
    data: ApplicationCoverLetterSuggestRequest,
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """Generate a cover message suggestion before applying."""
    return await ApplicationService.suggest_cover_letter(db, current_user, data.job_id)


@router.get("/me", response_model=ApplicationListResponse)
async def list_my_applications(
    status: Optional[str] = Query(None, description="submitted/viewed/interview_invited/rejected/hired"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """List current seeker's applications."""
    return await ApplicationService.list_my_applications(
        db,
        current_user,
        skip=skip,
        limit=limit,
        status_filter=status,
    )


@router.get("/me/{application_id}", response_model=ApplicationDetailResponse)
async def get_my_application(
    application_id: int,
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """Get current seeker's application detail with status timeline."""
    return await ApplicationService.get_for_seeker(db, current_user, application_id)


@router.get("/recruiter", response_model=ApplicationListResponse)
async def list_recruiter_applications(
    status: Optional[str] = Query(None, description="submitted/viewed/interview_invited/rejected/hired"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role("recruiter")),
    db: AsyncSession = Depends(get_db),
):
    """List applications received by current recruiter's jobs."""
    return await ApplicationService.list_for_recruiter(
        db,
        current_user,
        skip=skip,
        limit=limit,
        status_filter=status,
    )


@router.get("/recruiter/stats/summary", response_model=ApplicationStatsResponse)
async def get_recruiter_application_stats(
    current_user: User = Depends(require_role("recruiter")),
    db: AsyncSession = Depends(get_db),
):
    """Summarize current recruiter's application statuses."""
    return await ApplicationService.get_recruiter_stats(db, current_user)


@router.get("/recruiter/stats/business-loop", response_model=BusinessLoopStatsResponse)
async def get_recruiter_business_loop_stats(
    current_user: User = Depends(require_role("recruiter")),
    db: AsyncSession = Depends(get_db),
):
    """Summarize current recruiter's full PRD business loop."""
    return await ApplicationService.get_recruiter_business_loop_stats(db, current_user)


@router.get("/recruiter/stats/deep-dive", response_model=DeepDiveStatsResponse)
async def get_recruiter_deep_dive_stats(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(require_role("recruiter")),
    db: AsyncSession = Depends(get_db),
):
    """Summarize recruiter stats with trend and per-job ranking details."""
    return await ApplicationService.get_recruiter_deep_dive_stats(
        db,
        current_user,
        days=days,
        limit=limit,
    )


@router.get("/admin/stats/summary", response_model=ApplicationStatsResponse)
async def get_admin_application_stats(
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Summarize platform-wide application statuses for admin."""
    return await ApplicationService.get_admin_stats(db)


@router.get("/admin/stats/business-loop", response_model=BusinessLoopStatsResponse)
async def get_admin_business_loop_stats(
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Summarize platform-wide PRD business loop."""
    return await ApplicationService.get_admin_business_loop_stats(db)


@router.get("/admin/stats/deep-dive", response_model=DeepDiveStatsResponse)
async def get_admin_deep_dive_stats(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Summarize platform stats with trend and per-job ranking details."""
    return await ApplicationService.get_admin_deep_dive_stats(db, days=days, limit=limit)


@router.get("/admin/stats/operations", response_model=AdminOperationsStatsResponse)
async def get_admin_operations_stats(
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Summarize platform operations metrics for admin dashboard."""
    return await ApplicationService.get_admin_operations_stats(db)


@router.get("/recruiter/{application_id}", response_model=ApplicationDetailResponse)
async def get_recruiter_application(
    application_id: int,
    current_user: User = Depends(require_role("recruiter")),
    db: AsyncSession = Depends(get_db),
):
    """Get one application received by current recruiter's jobs."""
    return await ApplicationService.get_for_recruiter(db, current_user, application_id)


@router.get("/recruiter/{application_id}/resume-file")
async def download_recruiter_application_resume(
    application_id: int,
    current_user: User = Depends(require_role("recruiter")),
    db: AsyncSession = Depends(get_db),
):
    """Download resume file for one application owned by current recruiter."""
    path, filename, media_type = await ApplicationService.get_resume_file_for_recruiter(
        db,
        current_user,
        application_id,
    )
    return FileResponse(path, filename=filename, media_type=media_type)


@router.post("/{application_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    application_id: int,
    data: ApplicationStatusUpdate,
    current_user: User = Depends(require_role("recruiter")),
    db: AsyncSession = Depends(get_db),
):
    """Recruiter updates one application status."""
    return await ApplicationService.update_status(db, application_id, current_user, data)


@router.get("/admin", response_model=ApplicationListResponse)
async def list_applications_for_admin(
    status: Optional[str] = Query(None, description="submitted/viewed/interview_invited/rejected/hired"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Admin read-only application list."""
    return await ApplicationService.list_for_admin(db, skip=skip, limit=limit, status_filter=status)
