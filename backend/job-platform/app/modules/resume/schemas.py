"""
Seeker resume schemas.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ResumeResponse(BaseModel):
    """Uploaded resume response."""

    id: int
    seeker_id: int
    file_url: str
    file_name: str
    content_type: Optional[str] = None
    file_size: int
    parsed_snapshot: str
    created_at: datetime
    updated_at: datetime


class ResumeStatusResponse(BaseModel):
    """Current seeker resume status."""

    has_resume: bool
    resume: Optional[ResumeResponse] = None
