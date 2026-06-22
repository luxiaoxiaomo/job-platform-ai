"""Search API schemas."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.modules.base_data.schemas import TagReference

SearchMethod = Literal["keyword_semantic_fallback"]


class SearchJobItemResponse(BaseModel):
    id: int
    title: str
    city: str
    salary_min: int
    salary_max: int
    experience: str
    education: str
    recruiter_display_name: str | None = None
    tags: list[str] = Field(default_factory=list)
    tag_refs: list[TagReference] = Field(default_factory=list)
    score: float
    reason: str
    method: SearchMethod
    published_at: datetime | None = None


class SearchJobResponse(BaseModel):
    query: str
    method: SearchMethod
    items: list[SearchJobItemResponse]
    total: int
    skip: int
    limit: int


class SearchResumeItemResponse(BaseModel):
    seeker_id: int
    seeker_display_name: str | None = None
    structured_profile_id: int | None = None
    real_name: str | None = None
    target_position: str | None = None
    current_city: str | None = None
    highest_education: str | None = None
    work_years: float | None = None
    skills: list[str] = Field(default_factory=list)
    tag_refs: list[TagReference] = Field(default_factory=list)
    score: float
    reason: str
    method: SearchMethod
    updated_at: datetime | None = None


class SearchResumeResponse(BaseModel):
    query: str
    method: SearchMethod
    items: list[SearchResumeItemResponse]
    total: int
    skip: int
    limit: int


class SearchQueryParams(BaseModel):
    q: str = Field(..., min_length=1, max_length=120)
    skip: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=50)

    @field_validator("q")
    @classmethod
    def strip_query(cls, value: str) -> str:
        return value.strip()
