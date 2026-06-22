"""
Seeker resume schemas.
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from app.modules.base_data.schemas import TagReference, normalize_id_list


class ResumeResponse(BaseModel):
    """Uploaded resume response."""

    id: int
    seeker_id: int
    file_url: str
    file_name: str
    content_type: Optional[str] = None
    file_size: int
    parsed_snapshot: str
    current_upload_id: Optional[int] = None
    current_parse_run_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class ResumeUploadResponse(BaseModel):
    """Resume upload history response."""

    id: int
    seeker_id: int
    resume_id: Optional[int] = None
    file_url: str
    original_file_name: str
    content_type: Optional[str] = None
    file_ext: str
    file_size: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ResumeParseRunResponse(BaseModel):
    """Resume parse run response."""

    id: int
    upload_id: int
    seeker_id: int
    status: str
    parser_version: str
    prompt_version: Optional[int] = None
    extractor: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    metrics_json: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


class ResumeStatusResponse(BaseModel):
    """Current seeker resume status."""

    has_resume: bool
    resume: Optional[ResumeResponse] = None
    latest_upload: Optional[ResumeUploadResponse] = None
    latest_parse_run: Optional[ResumeParseRunResponse] = None


class ResumeUploadResultResponse(BaseModel):
    """Upload response with parse status."""

    resume: ResumeResponse
    upload: ResumeUploadResponse
    parse_run: ResumeParseRunResponse


class ResumeUploadHistoryItemResponse(BaseModel):
    """One upload history row with its latest parse run."""

    upload: ResumeUploadResponse
    latest_parse_run: Optional[ResumeParseRunResponse] = None


class ResumeExtractedTextPreviewResponse(BaseModel):
    """Extracted text preview for a parse run."""

    id: int
    parse_run_id: int
    upload_id: int
    text_preview: str
    language: str
    quality_score: float
    page_count: Optional[int] = None
    char_count: int
    created_at: datetime


class ResumeChunkPreviewResponse(BaseModel):
    """Chunk preview for later RAG UI."""

    id: int
    parse_run_id: int
    upload_id: int
    chunk_index: int
    section: str
    content_preview: str
    token_count: int
    embedding_status: str
    created_at: datetime


class ResumeParseRunDetailResponse(BaseModel):
    """Parse run detail used by the preview page."""

    upload: ResumeUploadResponse
    parse_run: ResumeParseRunResponse
    extracted_text: Optional[ResumeExtractedTextPreviewResponse] = None
    chunks: list[ResumeChunkPreviewResponse] = Field(default_factory=list)


class ResumeStructuredProfileCreateRequest(BaseModel):
    """Create or replace structured JSON for one parse run."""

    parse_run_id: int
    schema_version: str = "resume-structured-v1"
    source: str = "manual"
    status: str = "draft"
    confidence_score: Optional[float] = None
    structured_json: dict[str, Any]
    tag_ids: Optional[list[int]] = None
    validation_errors: Optional[Any] = None
    prompt_config_id: Optional[int] = None
    prompt_version: Optional[int] = None

    @field_validator("tag_ids", mode="before")
    @classmethod
    def normalize_tag_ids(cls, value):
        return normalize_id_list(value)


class ResumeStructuredProjectionRequest(BaseModel):
    """Project structured JSON into normalized detail tables."""

    confirm: bool = False
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ResumeStructuredConfirmRequest(BaseModel):
    """Confirm and project structured JSON by parse run."""

    parse_run_id: int
    schema_version: str = "resume-structured-v1"
    structured_json: Optional[dict[str, Any]] = None
    tag_ids: Optional[list[int]] = None
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("tag_ids", mode="before")
    @classmethod
    def normalize_tag_ids(cls, value):
        return normalize_id_list(value)


class ResumeStructuredProfileResponse(BaseModel):
    """Structured resume JSON response."""

    id: int
    seeker_id: int
    upload_id: int
    parse_run_id: int
    schema_version: str
    prompt_config_id: Optional[int] = None
    prompt_version: Optional[int] = None
    source: str
    status: str
    confidence_score: Optional[float] = None
    structured_json: dict[str, Any]
    tag_refs: list[TagReference] = Field(default_factory=list)
    validation_errors: Optional[Any] = None
    confirmed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ResumeBasicInfoResponse(BaseModel):
    """Normalized basic info response."""

    id: int
    real_name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    highest_education: Optional[str] = None
    work_years: Optional[float] = None
    current_city: Optional[str] = None
    target_position: Optional[str] = None
    expected_salary: Optional[str] = None
    source: str
    confidence_score: Optional[float] = None
    created_at: datetime


class ResumeEducationResponse(BaseModel):
    """Normalized education response."""

    id: int
    school_name: Optional[str] = None
    major: Optional[str] = None
    degree: Optional[str] = None
    education_level: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_full_time: Optional[bool] = None
    source: str
    confidence_score: Optional[float] = None
    sort_order: int
    created_at: datetime


class ResumeWorkExperienceResponse(BaseModel):
    """Normalized work experience response."""

    id: int
    company_name: Optional[str] = None
    position: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    source: str
    confidence_score: Optional[float] = None
    sort_order: int
    created_at: datetime


class ResumeProjectResponse(BaseModel):
    """Normalized project response."""

    id: int
    project_name: Optional[str] = None
    role: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    responsibility: Optional[str] = None
    source: str
    confidence_score: Optional[float] = None
    sort_order: int
    created_at: datetime


class ResumeSkillResponse(BaseModel):
    """Normalized skill response."""

    id: int
    skill_name: str
    skill_level: Optional[str] = None
    category: Optional[str] = None
    source: str
    confidence_score: Optional[float] = None
    sort_order: int
    created_at: datetime


class ResumeCertificateResponse(BaseModel):
    """Normalized certificate response."""

    id: int
    certificate_name: str
    certificate_type: Optional[str] = None
    issuer: Optional[str] = None
    issued_at: Optional[str] = None
    source: str
    confidence_score: Optional[float] = None
    sort_order: int
    created_at: datetime


class ResumeStructuredProfileDetailResponse(BaseModel):
    """Structured profile with normalized projection rows."""

    profile: ResumeStructuredProfileResponse
    basic_info: Optional[ResumeBasicInfoResponse] = None
    educations: list[ResumeEducationResponse] = Field(default_factory=list)
    work_experiences: list[ResumeWorkExperienceResponse] = Field(default_factory=list)
    projects: list[ResumeProjectResponse] = Field(default_factory=list)
    skills: list[ResumeSkillResponse] = Field(default_factory=list)
    certificates: list[ResumeCertificateResponse] = Field(default_factory=list)


class ResumeProfileSummaryListsResponse(BaseModel):
    """Grouped resume sections for the seeker portrait page."""

    educations: list[ResumeEducationResponse] = Field(default_factory=list)
    work_experiences: list[ResumeWorkExperienceResponse] = Field(default_factory=list)
    projects: list[ResumeProjectResponse] = Field(default_factory=list)
    skills: list[ResumeSkillResponse] = Field(default_factory=list)
    certificates: list[ResumeCertificateResponse] = Field(default_factory=list)


class ResumeProfileCompletenessGroupResponse(BaseModel):
    """One completeness metric group."""

    score: int = 0
    filled_count: int = 0
    total_count: int = 0
    missing_fields: list[str] = Field(default_factory=list)


class ResumeProfileCompletenessResponse(BaseModel):
    """Profile completeness split by required and optional display needs."""

    score: int = 0
    filled_count: int = 0
    total_count: int = 0
    missing_fields: list[str] = Field(default_factory=list)
    core: ResumeProfileCompletenessGroupResponse = Field(default_factory=ResumeProfileCompletenessGroupResponse)
    recommended: ResumeProfileCompletenessGroupResponse = Field(
        default_factory=ResumeProfileCompletenessGroupResponse
    )


class ResumeProfileReviewResponse(BaseModel):
    """Review state for the latest structured resume profile."""

    needs_review: bool = False
    unconfirmed_count: int = 0
    low_confidence_count: int = 0
    status_label: str = "未上传"


class ResumeProfileSourceLinksResponse(BaseModel):
    """Source ids and API links for drill-down views."""

    parse_run_id: Optional[int] = None
    parse_run_detail_url: Optional[str] = None
    structured_url: Optional[str] = None
    confirm_page_path: Optional[str] = None


class ResumeProfileSummaryResponse(BaseModel):
    """Aggregated current resume profile for the seeker portrait page."""

    resume: Optional[ResumeResponse] = None
    profile: Optional[ResumeStructuredProfileResponse] = None
    basic_info: Optional[ResumeBasicInfoResponse] = None
    summaries: ResumeProfileSummaryListsResponse = Field(default_factory=ResumeProfileSummaryListsResponse)
    completeness: ResumeProfileCompletenessResponse = Field(default_factory=ResumeProfileCompletenessResponse)
    review: ResumeProfileReviewResponse = Field(default_factory=ResumeProfileReviewResponse)
    source_links: ResumeProfileSourceLinksResponse = Field(default_factory=ResumeProfileSourceLinksResponse)


class ResumeStructuredProjectionResponse(BaseModel):
    """Projection result summary."""

    profile: ResumeStructuredProfileResponse
    projected_counts: dict[str, int]
    detail: ResumeStructuredProfileDetailResponse
