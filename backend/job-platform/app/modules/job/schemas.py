"""
Job posting schemas.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


JobStatus = Literal["draft", "pending", "active", "closed", "rejected"]
JobReviewAction = Literal["approve", "reject"]


class JobCreate(BaseModel):
    """Recruiter job submission."""

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


class JobUpdate(BaseModel):
    """Recruiter job update. Any content change sends the job back to review."""

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

    @field_validator("salary_max")
    @classmethod
    def validate_salary_range(cls, value: Optional[int], info) -> Optional[int]:
        salary_min = info.data.get("salary_min")
        if value is not None and salary_min is not None and value < salary_min:
            raise ValueError("salary_max must be greater than or equal to salary_min")
        return value


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


class JobResponse(BaseModel):
    """Job response."""

    id: int
    recruiter_id: int
    recruiter_display_name: Optional[str] = None
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
    status: JobStatus
    reject_reason: Optional[str] = None
    reviewer_id: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
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
