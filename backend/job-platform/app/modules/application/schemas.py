"""
Job application schemas.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


ApplicationStatus = Literal["submitted", "viewed", "interview_invited", "rejected", "hired"]


class ApplicationCreate(BaseModel):
    """Seeker application submission."""

    job_id: int = Field(..., gt=0)
    resume_snapshot: Optional[str] = Field(None, max_length=5000)
    cover_message: Optional[str] = Field(None, max_length=1000)

    @field_validator("resume_snapshot", "cover_message")
    @classmethod
    def strip_optional_text(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if value else value


class ApplicationStatusUpdate(BaseModel):
    """Recruiter application status update."""

    status: ApplicationStatus
    reject_reason: Optional[str] = Field(None, max_length=500)

    @field_validator("reject_reason")
    @classmethod
    def strip_reason(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if value else value


class ApplicationResponse(BaseModel):
    """Application response."""

    id: int
    job_id: int
    job_title: Optional[str] = None
    job_city: Optional[str] = None
    seeker_id: int
    seeker_display_name: Optional[str] = None
    recruiter_id: int
    recruiter_display_name: Optional[str] = None
    resume_id: Optional[int] = None
    resume_file_url: Optional[str] = None
    resume_file_name: Optional[str] = None
    status: ApplicationStatus
    resume_snapshot: Optional[str] = None
    cover_message: Optional[str] = None
    reject_reason: Optional[str] = None
    viewed_at: Optional[datetime] = None
    status_updated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ApplicationTimelineResponse(BaseModel):
    """Application status timeline response."""

    id: int
    application_id: int
    from_status: Optional[ApplicationStatus] = None
    to_status: ApplicationStatus
    actor_id: Optional[int] = None
    actor_role: str
    note: Optional[str] = None
    created_at: datetime


class ApplicationDetailResponse(ApplicationResponse):
    """Application detail response."""

    timeline: list[ApplicationTimelineResponse] = Field(default_factory=list)


class ApplicationListResponse(BaseModel):
    """Paginated application list response."""

    items: list[ApplicationResponse]
    total: int
    skip: int
    limit: int
