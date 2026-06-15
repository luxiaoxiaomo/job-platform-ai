"""
Seeker resume API.
"""
from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_role
from app.db.session import get_db
from app.modules.resume.schemas import (
    ResumeParseRunDetailResponse,
    ResumeStatusResponse,
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


@router.post("/me/upload", response_model=ResumeUploadResultResponse)
async def upload_my_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """Upload or replace current seeker's resume."""
    return await ResumeService.upload(db, current_user, file)
