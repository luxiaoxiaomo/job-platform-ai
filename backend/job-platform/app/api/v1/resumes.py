"""
Seeker resume API.
"""
from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_role
from app.db.session import get_db
from app.modules.resume.schemas import (
    ResumeParseRunDetailResponse,
    ResumeProfileSummaryResponse,
    ResumeStatusResponse,
    ResumeStructuredConfirmRequest,
    ResumeStructuredProfileCreateRequest,
    ResumeStructuredProfileDetailResponse,
    ResumeStructuredProfileResponse,
    ResumeStructuredProjectionRequest,
    ResumeStructuredProjectionResponse,
    ResumeUploadHistoryItemResponse,
    ResumeUploadResultResponse,
)
from app.modules.resume.service import ResumeService
from app.modules.user.models import User

router = APIRouter()


@router.get("/me", response_model=ResumeStatusResponse)
async def get_my_resume(
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """Get current seeker's latest uploaded resume."""
    return await ResumeService.get_my_status(db, current_user)


@router.get("/me/profile-summary", response_model=ResumeProfileSummaryResponse)
async def get_my_resume_profile_summary(
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """Get current seeker's aggregated resume profile for portrait UI."""
    return await ResumeService.get_my_profile_summary(db, current_user)


@router.get("/me/uploads", response_model=list[ResumeUploadHistoryItemResponse])
async def list_my_resume_uploads(
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """List current seeker's resume upload history."""
    return await ResumeService.list_my_uploads(db, current_user, limit=limit)


@router.get("/me/parse-runs/{parse_run_id}", response_model=ResumeParseRunDetailResponse)
async def get_my_parse_run_detail(
    parse_run_id: int,
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """Get parse run detail for current seeker's resume preview."""
    return await ResumeService.get_my_parse_run_detail(db, current_user, parse_run_id)


@router.get("/me/parse-runs/{parse_run_id}/structured", response_model=ResumeStructuredProfileDetailResponse)
async def get_my_parse_run_structured_profile(
    parse_run_id: int,
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """Get structured profile for one parse run."""
    return await ResumeService.get_my_structured_profile_by_parse_run(db, current_user, parse_run_id)


@router.put("/me/structured/confirm", response_model=ResumeStructuredProjectionResponse)
async def confirm_my_structured_profile(
    payload: ResumeStructuredConfirmRequest,
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """Confirm structured JSON by parse run and project it to detail tables."""
    return await ResumeService.confirm_structured_profile_by_parse_run(db, current_user, payload)


@router.post("/me/structured/confirm", response_model=ResumeStructuredProjectionResponse)
async def confirm_my_structured_profile_compat(
    payload: ResumeStructuredConfirmRequest,
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """Backward-compatible confirm endpoint for older clients that still POST."""
    return await ResumeService.confirm_structured_profile_by_parse_run(db, current_user, payload)


@router.get("/me/structured-profiles/latest", response_model=ResumeStructuredProfileDetailResponse)
async def get_my_latest_structured_profile(
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """Get current seeker's latest structured resume profile."""
    return await ResumeService.get_my_latest_structured_profile(db, current_user)


@router.get("/recruiter/applications/{application_id}/structured-profile", response_model=ResumeStructuredProfileDetailResponse)
async def get_recruiter_application_structured_profile(
    application_id: int,
    current_user: User = Depends(require_role("recruiter")),
    db: AsyncSession = Depends(get_db),
):
    """Get structured resume profile for one application owned by current recruiter."""
    return await ResumeService.get_recruiter_application_structured_profile(db, current_user, application_id)


@router.get("/me/structured-profiles/{profile_id}", response_model=ResumeStructuredProfileDetailResponse)
async def get_my_structured_profile(
    profile_id: int,
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """Get one structured profile and normalized projection rows."""
    return await ResumeService.get_my_structured_profile_detail(db, current_user, profile_id)


@router.post("/me/structured-profiles", response_model=ResumeStructuredProfileResponse)
async def create_my_structured_profile(
    payload: ResumeStructuredProfileCreateRequest,
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """Create or replace structured JSON for one parse run."""
    return await ResumeService.create_structured_profile(db, current_user, payload)


@router.post(
    "/me/structured-profiles/{profile_id}/project",
    response_model=ResumeStructuredProjectionResponse,
)
async def project_my_structured_profile(
    profile_id: int,
    payload: ResumeStructuredProjectionRequest,
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """Project structured JSON into normalized resume detail tables."""
    return await ResumeService.project_structured_profile(db, current_user, profile_id, payload)


@router.post("/me/upload", response_model=ResumeUploadResultResponse)
async def upload_my_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """Upload or replace current seeker's resume."""
    return await ResumeService.upload(db, current_user, file)
