"""
Seeker resume repository.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.resume.models import SeekerResume


class ResumeRepository:
    """Database operations for seeker resumes."""

    @staticmethod
    async def get_by_seeker_id(db: AsyncSession, seeker_id: int) -> Optional[SeekerResume]:
        result = await db.execute(select(SeekerResume).where(SeekerResume.seeker_id == seeker_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def save(db: AsyncSession, resume: SeekerResume) -> SeekerResume:
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        return resume
