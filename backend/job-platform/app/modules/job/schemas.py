"""
Job posting schemas.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.modules.base_data.schemas import TagReference, normalize_id_list


JobStatus = Literal["draft", "pending", "active", "closed", "rejected"]
JobCreateStatus = Literal["draft", "pending"]
JobReviewAction = Literal["approve", "reject"]
CompanyDisplayMode = Literal["display_name", "company_name", "anonymous"]


class JobCreate(BaseModel):
    """Recruiter job submission."""

    standard_position_id: Optional[int] = Field(None, gt=0)
    title: str = Field(..., min_length=2, max_length=100)
    city: str = Field(..., min_length=1, max_length=50)
    salary_min: int = Field(..., gt=0, le=1000)
    salary_max: int = Field(..., gt=0, le=1000)
    experience: str = Field("不限", min_length=1, max_length=50)
    education: str = Field("不限", min_length=1, max_length=50)
    description: str = Field(..., min_length=10, max_length=5000)
    requirement: str = Field(..., min_length=10, max_length=5000)
    benefits: Optional[str] = Field(None, max_length=2000)
    tags: Optional[list[str]] = None
    tag_ids: Optional[list[int]] = None
    company_display_mode: CompanyDisplayMode = "display_name"
    contact_phone_public: bool = False
    contact_email_public: bool = False
    contact_wechat_public: bool = False
    status: JobCreateStatus = "pending"

    @field_validator(
        "title",
        "city",
        "experience",
        "education",
        "description",
        "requirement",
        "benefits",
        mode="before",
    )
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("salary_max")
    @classmethod
    def validate_salary_range(cls, value: int, info) -> int:
        if "salary_min" in info.data and value < info.data["salary_min"]:
            raise ValueError("salary_max must be greater than or equal to salary_min")
        return value

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        if value is None:
            return None
        cleaned = []
        for item in value:
            tag = item.strip() if isinstance(item, str) else ""
            if tag and tag not in cleaned:
                cleaned.append(tag[:30])
        return cleaned[:20]

    @field_validator("tag_ids")
    @classmethod
    def normalize_tag_ids(cls, value: Optional[list[int]]) -> Optional[list[int]]:
        return normalize_id_list(value)


class JobUpdate(BaseModel):
    """Recruiter job update. Any content change sends the job back to review."""

    standard_position_id: Optional[int] = Field(None, gt=0)
    title: Optional[str] = Field(None, min_length=2, max_length=100)
    city: Optional[str] = Field(None, min_length=1, max_length=50)
    salary_min: Optional[int] = Field(None, gt=0, le=1000)
    salary_max: Optional[int] = Field(None, gt=0, le=1000)
    experience: Optional[str] = Field(None, min_length=1, max_length=50)
    education: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, min_length=10, max_length=5000)
    requirement: Optional[str] = Field(None, min_length=10, max_length=5000)
    benefits: Optional[str] = Field(None, max_length=2000)
    tags: Optional[list[str]] = None
    tag_ids: Optional[list[int]] = None
    company_display_mode: Optional[CompanyDisplayMode] = None
    contact_phone_public: Optional[bool] = None
    contact_email_public: Optional[bool] = None
    contact_wechat_public: Optional[bool] = None

    @field_validator("salary_max")
    @classmethod
    def validate_salary_range(cls, value: Optional[int], info) -> Optional[int]:
        salary_min = info.data.get("salary_min")
        if value is not None and salary_min is not None and value < salary_min:
            raise ValueError("salary_max must be greater than or equal to salary_min")
        return value

    @field_validator("tag_ids")
    @classmethod
    def normalize_update_tag_ids(cls, value: Optional[list[int]]) -> Optional[list[int]]:
        return normalize_id_list(value)


class JobReview(BaseModel):
    """Admin job review request."""

    action: JobReviewAction
    reject_reason: Optional[str] = Field(None, max_length=500)

    @field_validator("reject_reason")
    @classmethod
    def strip_reason(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if value else value


class JobJdTextParseRequest(BaseModel):
    """Raw JD text parse request."""

    text: str = Field(..., min_length=10, max_length=20000)

    @field_validator("text")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class JobSalarySuggestionRequest(BaseModel):
    """Salary suggestion request."""

    title: str = Field(..., min_length=2, max_length=100)
    city: str = Field(..., min_length=1, max_length=50)
    experience: str = Field("不限", min_length=1, max_length=50)
    education: str = Field("不限", min_length=1, max_length=50)
    tags: list[str] = Field(default_factory=list)

    @field_validator("title", "city", "experience", "education", mode="before")
    @classmethod
    def strip_salary_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class JobSalarySuggestionResponse(BaseModel):
    """Rule-based salary suggestion response."""

    salary_min: int
    salary_max: int
    market_median: int
    benchmark_median: int
    confidence: float
    basis: str
    benchmark_companies: list[str] = Field(default_factory=list)
    factors: list[str] = Field(default_factory=list)


class JobPublicContactResponse(BaseModel):
    """Publicly visible recruiter contact fields for a job."""

    company_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    wechat: Optional[str] = None


class JobResponse(BaseModel):
    """Job response."""

    id: int
    recruiter_id: int
    recruiter_display_name: Optional[str] = None
    company_display_mode: CompanyDisplayMode = "display_name"
    contact_phone_public: bool = False
    contact_email_public: bool = False
    contact_wechat_public: bool = False
    public_contact: JobPublicContactResponse = Field(default_factory=JobPublicContactResponse)
    standard_position_id: Optional[int] = None
    standard_position_name: Optional[str] = None
    title: str
    city: str
    salary_min: int
    salary_max: int
    experience: str
    education: str
    description: str
    requirement: str
    benefits: Optional[str] = None
    tags: Optional[list[str]] = None
    tag_refs: list[TagReference] = Field(default_factory=list)
    status: JobStatus
    reject_reason: Optional[str] = None
    reviewer_id: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    view_count: int = 0
    conversation_count: int = 0
    created_at: datetime
    updated_at: datetime


class JobJdParseResponse(BaseModel):
    """Parsed JD upload response."""

    file_name: str
    source: str
    confidence: float
    raw_text: str
    title: Optional[str] = None
    city: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    description: Optional[str] = None
    requirement: Optional[str] = None
    benefits: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)


class JobListResponse(BaseModel):
    """Paginated job list response."""

    items: list[JobResponse]
    total: int
    skip: int
    limit: int


class JobVisitorResponse(BaseModel):
    """Aggregated visitor row for a recruiter's job."""

    seeker_id: int
    seeker_display_name: str
    avatar_url: Optional[str] = None
    view_count: int
    first_viewed_at: datetime
    last_viewed_at: datetime
    has_conversation: bool = False
    has_application: bool = False
    high_intent: bool = False
    intent_score: int = 0
    tags: list[str] = Field(default_factory=list)


class JobVisitorListResponse(BaseModel):
    """Paginated job visitor list response."""

    job_id: int
    job_title: str
    total_views: int
    unique_visitors: int
    items: list[JobVisitorResponse]
    total: int
    skip: int
    limit: int


class JobHistoryItemResponse(BaseModel):
    """One seeker job browsing-history row."""

    job: JobResponse
    view_count: int
    first_viewed_at: datetime
    last_viewed_at: datetime
    is_favorited: bool = False


class JobHistoryListResponse(BaseModel):
    """Paginated seeker browsing-history response."""

    items: list[JobHistoryItemResponse]
    total: int
    skip: int
    limit: int


class JobFavoriteResponse(BaseModel):
    """One seeker favorite row."""

    id: int
    job: JobResponse
    created_at: datetime


class JobFavoriteListResponse(BaseModel):
    """Paginated seeker favorites response."""

    items: list[JobFavoriteResponse]
    total: int
    skip: int
    limit: int


class JobSubscriptionCreate(BaseModel):
    """Create a seeker job subscription."""

    name: Optional[str] = Field(None, max_length=100)
    keywords: list[str] = Field(default_factory=list, max_length=10)
    city: Optional[str] = Field(None, max_length=50)
    salary_min: Optional[int] = Field(None, ge=0, le=1000)
    salary_max: Optional[int] = Field(None, ge=0, le=1000)
    active: bool = True

    @field_validator("name", "city", mode="before")
    @classmethod
    def strip_optional_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("keywords")
    @classmethod
    def normalize_subscription_keywords(cls, value: list[str]) -> list[str]:
        cleaned = []
        for item in value or []:
            keyword = item.strip() if isinstance(item, str) else ""
            if keyword and keyword not in cleaned:
                cleaned.append(keyword[:30])
        if not cleaned:
            raise ValueError("At least one keyword is required")
        return cleaned[:10]

    @field_validator("salary_max")
    @classmethod
    def validate_subscription_salary_range(cls, value: Optional[int], info) -> Optional[int]:
        salary_min = info.data.get("salary_min")
        if value is not None and salary_min is not None and value < salary_min:
            raise ValueError("salary_max must be greater than or equal to salary_min")
        return value


class JobSubscriptionUpdate(BaseModel):
    """Update a seeker job subscription."""

    name: Optional[str] = Field(None, max_length=100)
    keywords: Optional[list[str]] = Field(None, max_length=10)
    city: Optional[str] = Field(None, max_length=50)
    salary_min: Optional[int] = Field(None, ge=0, le=1000)
    salary_max: Optional[int] = Field(None, ge=0, le=1000)
    active: Optional[bool] = None

    @field_validator("name", "city", mode="before")
    @classmethod
    def strip_update_optional_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("keywords")
    @classmethod
    def normalize_update_subscription_keywords(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        if value is None:
            return None
        cleaned = []
        for item in value or []:
            keyword = item.strip() if isinstance(item, str) else ""
            if keyword and keyword not in cleaned:
                cleaned.append(keyword[:30])
        if not cleaned:
            raise ValueError("At least one keyword is required")
        return cleaned[:10]

    @field_validator("salary_max")
    @classmethod
    def validate_update_subscription_salary_range(cls, value: Optional[int], info) -> Optional[int]:
        salary_min = info.data.get("salary_min")
        if value is not None and salary_min is not None and value < salary_min:
            raise ValueError("salary_max must be greater than or equal to salary_min")
        return value


class JobSubscriptionResponse(BaseModel):
    """One seeker job subscription with matching preview."""

    id: int
    name: str
    keywords: list[str]
    city: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    active: bool
    match_count: int = 0
    matched_jobs: list[JobResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class JobSubscriptionListResponse(BaseModel):
    """Paginated seeker job subscriptions response."""

    items: list[JobSubscriptionResponse]
    total: int
    skip: int
    limit: int


class SeekerNotificationResponse(BaseModel):
    """One computed seeker notification."""

    id: str
    type: Literal["match"]
    title: str
    detail: str
    time: str
    read: bool = False
    subscription_id: int
    subscription_name: str
    matched_job_ids: list[int] = Field(default_factory=list)
    match_count: int = 0


class SeekerNotificationListResponse(BaseModel):
    """Computed seeker notifications response."""

    items: list[SeekerNotificationResponse]
    total: int
