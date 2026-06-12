"""
AI prompt configuration schemas.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


PromptScenario = Literal["job_content_review"]
ReviewLevel = Literal["pass", "warning", "block"]


class AiPromptConfigCreate(BaseModel):
    scenario_key: PromptScenario = "job_content_review"
    name: str = Field(..., min_length=2, max_length=120)
    system_prompt: str = Field(..., min_length=20, max_length=20000)
    user_prompt_template: str = Field(..., min_length=20, max_length=20000)
    output_schema: str = Field(..., min_length=20, max_length=20000)

    @field_validator("name", "system_prompt", "user_prompt_template", "output_schema")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class AiPromptConfigResponse(BaseModel):
    id: Optional[int] = None
    scenario_key: str
    name: str
    version: int
    system_prompt: str
    user_prompt_template: str
    output_schema: str
    is_active: bool
    created_by: Optional[int] = None
    published_by: Optional[int] = None
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AiPromptConfigListResponse(BaseModel):
    items: list[AiPromptConfigResponse]
    total: int


class PromptTestJobInput(BaseModel):
    title: str = Field("", max_length=100)
    city: str = Field("", max_length=50)
    salary_min: Optional[int] = Field(None, gt=0, le=1000)
    salary_max: Optional[int] = Field(None, gt=0, le=1000)
    experience: str = Field("", max_length=50)
    education: str = Field("", max_length=50)
    description: str = Field("", max_length=5000)
    requirement: str = Field("", max_length=5000)
    benefits: Optional[str] = Field(None, max_length=2000)
    tags: list[str] = Field(default_factory=list)


class PromptTestRequest(BaseModel):
    system_prompt: str = Field(..., min_length=20, max_length=20000)
    user_prompt_template: str = Field(..., min_length=20, max_length=20000)
    output_schema: str = Field(..., min_length=20, max_length=20000)
    job: PromptTestJobInput


class JobPreReviewFinding(BaseModel):
    category: str
    severity: Literal["warning", "block"]
    evidence: Optional[str] = None
    suggestion: str


class JobPreReviewRewriteSuggestions(BaseModel):
    description: Optional[str] = None
    requirement: Optional[str] = None


class JobPreReviewResponse(BaseModel):
    level: ReviewLevel
    summary: str
    findings: list[JobPreReviewFinding] = Field(default_factory=list)
    rewrite_suggestions: JobPreReviewRewriteSuggestions = Field(default_factory=JobPreReviewRewriteSuggestions)
    prompt_version: int
    prompt_source: str


class JobPreReviewRequest(PromptTestJobInput):
    pass
