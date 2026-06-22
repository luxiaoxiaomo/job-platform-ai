"""
Seeker profile business logic.
"""
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.base_data.repository import StandardPositionRepository
from app.modules.base_data.tag_refs import resolve_active_tag_refs
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


def _to_response(profile: SeekerProfile, standard_position_name: str | None = None) -> SeekerProfileResponse:
    return SeekerProfileResponse(
        id=profile.id,
        seeker_id=profile.seeker_id,
        real_name=profile.real_name,
        gender=profile.gender,
        education=profile.education,
        experience_years=profile.experience_years,
        standard_position_id=profile.standard_position_id,
        standard_position_name=standard_position_name,
        target_position=profile.target_position,
        expected_salary=profile.expected_salary,
        city=profile.city,
        tag_refs=profile.tag_refs or [],
        email=profile.email,
        wechat=profile.wechat,
        name_public=profile.name_public,
        phone_public=profile.phone_public,
        email_public=profile.email_public,
        wechat_public=profile.wechat_public,
        education_public=profile.education_public,
        experience_public=profile.experience_public,
        is_complete=_is_complete(profile),
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


async def _to_response_with_standard_position(
    db: AsyncSession,
    profile: SeekerProfile,
) -> SeekerProfileResponse:
    standard_position_name = None
    if profile.standard_position_id is not None:
        position = await StandardPositionRepository.get_by_id(db, profile.standard_position_id)
        standard_position_name = position.name if position is not None else None
    return _to_response(profile, standard_position_name)


class SeekerProfileService:
    """Seeker profile use cases."""

    @staticmethod
    async def _ensure_active_standard_position(db: AsyncSession, standard_position_id: int | None) -> None:
        if standard_position_id is None:
            return
        position = await StandardPositionRepository.get_by_id(db, standard_position_id)
        if position is None or position.status != "active":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Standard position not found")

    @staticmethod
    async def get_my_profile(db: AsyncSession, current_user: User) -> SeekerProfileResponse:
        if current_user.role != "seeker":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only seekers can use seeker profiles")
        profile = await SeekerProfileRepository.get_by_seeker_id(db, current_user.id)
        return await _to_response_with_standard_position(db, profile) if profile else _empty_response(current_user)

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

        await SeekerProfileService._ensure_active_standard_position(db, data.standard_position_id)
        payload = data.model_dump()
        tag_refs = await resolve_active_tag_refs(db, payload.pop("tag_ids", None))
        payload["tag_refs"] = tag_refs
        for key, value in payload.items():
            setattr(profile, key, value)

        saved = await SeekerProfileRepository.save(db, profile)
        return await _to_response_with_standard_position(db, saved)
