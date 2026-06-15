"""
Seeker profile business logic.
"""
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.seeker_profile.models import SeekerProfile
from app.modules.seeker_profile.repository import SeekerProfileRepository
from app.modules.seeker_profile.schemas import SeekerProfileResponse, SeekerProfileUpsert
from app.modules.user.models import User


def _is_complete(profile: SeekerProfile | None) -> bool:
    if profile is None:
        return False
    return all(
        [
            bool(profile.real_name),
            bool(profile.gender),
            bool(profile.education),
            profile.experience_years is not None,
        ]
    )


def _empty_response(current_user: User) -> SeekerProfileResponse:
    return SeekerProfileResponse(seeker_id=current_user.id, is_complete=False)


def _to_response(profile: SeekerProfile) -> SeekerProfileResponse:
    return SeekerProfileResponse(
        id=profile.id,
        seeker_id=profile.seeker_id,
        real_name=profile.real_name,
        gender=profile.gender,
        education=profile.education,
        experience_years=profile.experience_years,
        target_position=profile.target_position,
        expected_salary=profile.expected_salary,
        city=profile.city,
        name_public=profile.name_public,
        phone_public=profile.phone_public,
        education_public=profile.education_public,
        experience_public=profile.experience_public,
        is_complete=_is_complete(profile),
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


class SeekerProfileService:
    """Seeker profile use cases."""

    @staticmethod
    async def get_my_profile(db: AsyncSession, current_user: User) -> SeekerProfileResponse:
        if current_user.role != "seeker":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only seekers can use seeker profiles")
        profile = await SeekerProfileRepository.get_by_seeker_id(db, current_user.id)
        return _to_response(profile) if profile else _empty_response(current_user)

    @staticmethod
    async def upsert_my_profile(
        db: AsyncSession,
        current_user: User,
        data: SeekerProfileUpsert,
    ) -> SeekerProfileResponse:
        if current_user.role != "seeker":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only seekers can use seeker profiles")

        profile = await SeekerProfileRepository.get_by_seeker_id(db, current_user.id)
        if profile is None:
            profile = SeekerProfile(seeker_id=current_user.id)

        payload = data.model_dump()
        for key, value in payload.items():
            setattr(profile, key, value)

        saved = await SeekerProfileRepository.save(db, profile)
        return _to_response(saved)
