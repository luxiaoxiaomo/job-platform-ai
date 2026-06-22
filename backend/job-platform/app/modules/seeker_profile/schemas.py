"""
Seeker profile schemas.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.modules.base_data.schemas import TagReference, normalize_id_list


class SeekerProfileUpsert(BaseModel):
    """Create or update current seeker's profile."""

    real_name: Optional[str] = Field(None, max_length=50)
    gender: Optional[str] = Field(None, max_length=20)
    education: Optional[str] = Field(None, max_length=80)
    experience_years: Optional[int] = Field(None, ge=0, le=80)
    standard_position_id: Optional[int] = Field(None, gt=0)
    target_position: Optional[str] = Field(None, max_length=100)
    expected_salary: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=80)
    tag_ids: Optional[list[int]] = None
    email: Optional[str] = Field(None, max_length=120)
    wechat: Optional[str] = Field(None, max_length=80)
    name_public: bool = True
    phone_public: bool = True
    email_public: bool = False
    wechat_public: bool = False
    education_public: bool = True
    experience_public: bool = False

    @field_validator("real_name", "gender", "education", "target_position", "expected_salary", "city", "email", "wechat")
    @classmethod
    def strip_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("tag_ids")
    @classmethod
    def normalize_tag_ids(cls, value: Optional[list[int]]) -> Optional[list[int]]:
        return normalize_id_list(value)


class SeekerProfileResponse(BaseModel):
    """Current seeker's profile."""

    id: Optional[int] = None
    seeker_id: int
    real_name: Optional[str] = None
    gender: Optional[str] = None
    education: Optional[str] = None
    experience_years: Optional[int] = None
    standard_position_id: Optional[int] = None
    standard_position_name: Optional[str] = None
    target_position: Optional[str] = None
    expected_salary: Optional[str] = None
    city: Optional[str] = None
    tag_refs: list[TagReference] = Field(default_factory=list)
    email: Optional[str] = None
    wechat: Optional[str] = None
    name_public: bool = True
    phone_public: bool = True
    email_public: bool = False
    wechat_public: bool = False
    education_public: bool = True
    experience_public: bool = False
    is_complete: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
