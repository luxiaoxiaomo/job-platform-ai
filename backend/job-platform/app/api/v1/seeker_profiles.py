"""
Seeker profile API.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_role
from app.db.session import get_db
from app.modules.seeker_profile.schemas import SeekerProfileResponse, SeekerProfileUpsert
from app.modules.seeker_profile.service import SeekerProfileService
from app.modules.user.models import User

router = APIRouter()


@router.get("/me", response_model=SeekerProfileResponse)
async def get_my_seeker_profile(
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """Get current seeker's structured profile."""
    return await SeekerProfileService.get_my_profile(db, current_user)


@router.put("/me", response_model=SeekerProfileResponse)
async def upsert_my_seeker_profile(
    data: SeekerProfileUpsert,
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """Create or update current seeker's structured profile."""
    return await SeekerProfileService.upsert_my_profile(db, current_user, data)
