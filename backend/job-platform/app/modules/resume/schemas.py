"""
Seeker resume schemas.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


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
