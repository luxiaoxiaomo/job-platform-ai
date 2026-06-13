"""
Job application API.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.modules.application.schemas import (
    ApplicationCreate,
    ApplicationListResponse,
    ApplicationResponse,
    ApplicationStatusUpdate,
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
