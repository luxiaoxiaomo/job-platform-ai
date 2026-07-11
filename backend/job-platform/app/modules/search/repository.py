"""Search database access."""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.job.models import Job
from app.modules.resume.models import ResumeBasicInfo, ResumeChunk, ResumeSkill, ResumeStructuredProfile, SeekerResume
from app.modules.seeker_profile.models import SeekerProfile
from app.modules.user.models import User


class SearchRepository:
    """Queries used by search services."""

    @staticmethod
    async def list_active_jobs(db: AsyncSession, *, limit: int = 500) -> list[Job]:
        result = await db.execute(
            select(Job)
            .options(selectinload(Job.recruiter))
            .where(Job.status == "active")
            .order_by(Job.published_at.desc().nullslast(), Job.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_resume_candidates(db: AsyncSession, *, limit: int = 500):
        latest_profile_ids = (
            select(func.max(ResumeStructuredProfile.id).label("profile_id"))
            .group_by(ResumeStructuredProfile.seeker_id)
            .subquery()
        )
        result = await db.execute(
            select(ResumeStructuredProfile, ResumeBasicInfo, SeekerResume, User, SeekerProfile)
            .join(latest_profile_ids, latest_profile_ids.c.profile_id == ResumeStructuredProfile.id)
            .outerjoin(ResumeBasicInfo, ResumeBasicInfo.structured_profile_id == ResumeStructuredProfile.id)
            .outerjoin(SeekerResume, SeekerResume.seeker_id == ResumeStructuredProfile.seeker_id)
            .outerjoin(SeekerProfile, SeekerProfile.seeker_id == ResumeStructuredProfile.seeker_id)
            .join(User, User.id == ResumeStructuredProfile.seeker_id)
            .order_by(ResumeStructuredProfile.updated_at.desc())
            .limit(limit)
        )
        return list(result.all())

    @staticmethod
    async def skills_by_profile_ids(db: AsyncSession, profile_ids: list[int]) -> dict[int, list[str]]:
        if not profile_ids:
            return {}
        result = await db.execute(
            select(ResumeSkill.structured_profile_id, ResumeSkill.skill_name)
            .where(ResumeSkill.structured_profile_id.in_(profile_ids))
            .order_by(ResumeSkill.sort_order.asc(), ResumeSkill.id.asc())
        )
        mapped: dict[int, list[str]] = {}
        for profile_id, skill_name in result.all():
            if skill_name:
                mapped.setdefault(profile_id, []).append(skill_name)
        return mapped

    @staticmethod
    async def chunks_by_seeker_ids(db: AsyncSession, seeker_ids: list[int]) -> dict[int, list[str]]:
        if not seeker_ids:
            return {}
        result = await db.execute(
            select(ResumeChunk.seeker_id, ResumeChunk.content)
            .where(ResumeChunk.seeker_id.in_(seeker_ids))
            .order_by(ResumeChunk.chunk_index.asc(), ResumeChunk.id.asc())
        )
        mapped: dict[int, list[str]] = {}
        for seeker_id, content in result.all():
            if content:
                mapped.setdefault(seeker_id, []).append(content)
        return mapped
