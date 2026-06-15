"""
Seeker profile repository.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.seeker_profile.models import SeekerProfile


class SeekerProfileRepository:
    """Database operations for seeker profiles."""

    @staticmethod
    async def get_by_seeker_id(db: AsyncSession, seeker_id: int) -> Optional[SeekerProfile]:
        result = await db.execute(select(SeekerProfile).where(SeekerProfile.seeker_id == seeker_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def save(db: AsyncSession, profile: SeekerProfile) -> SeekerProfile:
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        return profile
