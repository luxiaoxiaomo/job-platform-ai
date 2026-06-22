"""
Message and contact exchange schemas.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


ContactExchangeStatus = Literal["pending", "accepted", "declined"]
ContactExchangeAction = Literal["accept", "decline"]


class MessageCreate(BaseModel):
    """Text message submission."""

    job_id: int = Field(..., gt=0)
    content: str = Field(..., min_length=1, max_length=1000)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        return value.strip()


class ConversationOpenRequest(BaseModel):
    """Create or reuse a conversation without sending a default message."""

    job_id: int = Field(..., gt=0)


class ConversationMessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    sender_role: str
    content: str
    original_content: Optional[str] = None
    moderation_status: str
    created_at: datetime


class ContactInfoResponse(BaseModel):
    user_id: int
    display_name: str
    role: str
    phone: Optional[str] = None
    email: Optional[str] = None
    wechat: Optional[str] = None
    company_name: Optional[str] = None


class ContactExchangeResponse(BaseModel):
    id: int
    conversation_id: int
    requester_id: int
    requester_role: str
    status: ContactExchangeStatus
    responder_id: Optional[int] = None
    responded_at: Optional[datetime] = None
    created_at: datetime
    contacts: Optional[list[ContactInfoResponse]] = None


class ConversationResponse(BaseModel):
    id: int
    job_id: int
    job_title: Optional[str] = None
    seeker_id: int
    seeker_display_name: Optional[str] = None
    recruiter_id: int
    recruiter_display_name: Optional[str] = None
    last_message_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    latest_message: Optional[ConversationMessageResponse] = None
    contact_exchange: Optional[ContactExchangeResponse] = None
    lead_status: str = "opened"
    lead_status_label: str = "已打开会话"
    application_id: Optional[int] = None
    application_status: Optional[str] = None


class ConversationDetailResponse(ConversationResponse):
    messages: list[ConversationMessageResponse] = Field(default_factory=list)


class ConversationListResponse(BaseModel):
    items: list[ConversationResponse]
    total: int
    skip: int
    limit: int


class ReplySuggestionResponse(BaseModel):
    style: str
    text: str = Field(..., min_length=1, max_length=500)
    source: str = "template_fallback"


class ReplySuggestionListResponse(BaseModel):
    conversation_id: int
    scenario_key: str = "message_reply_suggestion"
    source: str = "template_fallback"
    suggestions: list[ReplySuggestionResponse]


class ContactExchangeStatsResponse(BaseModel):
    accepted_count: int
    pending_count: int
    declined_count: int
    total_count: int


class ContactExchangeCreate(BaseModel):
    conversation_id: int = Field(..., gt=0)


class ContactExchangeReview(BaseModel):
    action: ContactExchangeAction
