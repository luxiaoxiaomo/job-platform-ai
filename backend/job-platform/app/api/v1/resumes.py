"""
Seeker resume API.
"""
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_role
from app.db.session import get_db
from app.modules.resume.schemas import ResumeResponse, ResumeStatusResponse
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


@router.post("/me/upload", response_model=ResumeResponse)
async def upload_my_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """Upload or replace current seeker's resume."""
    return await ResumeService.upload(db, current_user, file)
