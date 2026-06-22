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


class ApplicationCoverLetterSuggestRequest(BaseModel):
    """Generate a cover message suggestion before application submission."""

    job_id: int = Field(..., gt=0)


class ApplicationCoverLetterSuggestResponse(BaseModel):
    """AI-assisted cover message suggestion with deterministic fallback."""

    job_id: int
    cover_message: str
    source: str = "rule_fallback"
    highlights: list[str] = Field(default_factory=list)
    fallback_used: bool = True


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


class ApplicationStatsResponse(BaseModel):
    """Recruiter application funnel summary."""

    submitted_count: int = 0
    viewed_count: int = 0
    interview_invited_count: int = 0
    rejected_count: int = 0
    hired_count: int = 0
    total_count: int = 0


class BusinessLoopStatsResponse(BaseModel):
    """Unified PRD business loop statistics."""

    job_count: int = 0
    view_count: int = 0
    conversation_count: int = 0
    application_count: int = 0
    submitted_count: int = 0
    processed_count: int = 0
    viewed_count: int = 0
    interview_invited_count: int = 0
    rejected_count: int = 0
    hired_count: int = 0
    contact_exchange_count: int = 0
    successful_connection_count: int = 0
    pending_exchange_count: int = 0
    declined_exchange_count: int = 0
    view_to_conversation_rate: float = 0
    conversation_to_application_rate: float = 0
    application_process_rate: float = 0
    application_to_connection_rate: float = 0
    successful_connection_definition: str = "contact_exchange.status = accepted"


class StatsTrendPointResponse(BaseModel):
    """One day of business-loop trend metrics."""

    date: str
    view_count: int = 0
    conversation_count: int = 0
    application_count: int = 0
    successful_connection_count: int = 0


class JobStatsRankingItemResponse(BaseModel):
    """Per-job ranking metrics for recruiter/admin stats dashboards."""

    job_id: int
    title: str
    status: str
    view_count: int = 0
    conversation_count: int = 0
    application_count: int = 0
    successful_connection_count: int = 0
    application_rate: float = 0
    connection_rate: float = 0


class DeepDiveStatsResponse(BaseModel):
    """Stats dashboard payload with trend, ranking and distribution details."""

    summary: BusinessLoopStatsResponse
    trend_days: int
    trend: list[StatsTrendPointResponse] = Field(default_factory=list)
    top_jobs: list[JobStatsRankingItemResponse] = Field(default_factory=list)
    application_status_distribution: dict[str, int] = Field(default_factory=dict)
    successful_connection_definition: str = "contact_exchange.status = accepted"


class AdminOperationsStatsResponse(BaseModel):
    """Admin platform operations dashboard summary."""

    today_new_user_count: int = 0
    today_new_job_count: int = 0
    today_new_application_count: int = 0
    active_job_count: int = 0
    pending_job_review_count: int = 0
    pending_certification_count: int = 0
    approved_certification_count: int = 0
    rejected_certification_count: int = 0
    certification_total_count: int = 0
    certification_approval_rate: float = 0
    application_process_rate: float = 0
