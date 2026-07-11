"""
Conversation and contact exchange API.
"""
from fastapi import APIRouter, Depends, Query, status as http_status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_role
from app.db.session import get_db
from app.modules.message.schemas import (
    ContactExchangeCreate,
    ContactExchangeResponse,
    ContactExchangeReview,
    ContactExchangeStatsResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationOpenRequest,
    MessageCreate,
    ReplySuggestionListResponse,
)
from app.modules.message.service import MessageService
from app.modules.user.models import User

router = APIRouter()


class MessageReply(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        return value.strip()


@router.get("/conversations", response_model=ConversationListResponse)
async def list_my_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role("seeker", "recruiter")),
    db: AsyncSession = Depends(get_db),
):
    """List current user's job conversations."""
    return await MessageService.list_my_conversations(db, current_user, skip=skip, limit=limit)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_my_conversation(
    conversation_id: int,
    current_user: User = Depends(require_role("seeker", "recruiter")),
    db: AsyncSession = Depends(get_db),
):
    """Get one conversation with messages."""
    return await MessageService.get_conversation(db, current_user, conversation_id)


@router.post("/messages", response_model=ConversationDetailResponse, status_code=http_status.HTTP_201_CREATED)
async def send_job_message(
    data: MessageCreate,
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """Seeker starts or continues a job conversation."""
    return await MessageService.send_message(db, current_user, data)


@router.post("/conversations/open", response_model=ConversationDetailResponse, status_code=http_status.HTTP_201_CREATED)
async def open_job_conversation(
    data: ConversationOpenRequest,
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """Seeker opens or reuses a job conversation without sending a message."""
    return await MessageService.open_conversation(db, current_user, data)


@router.post("/conversations/{conversation_id}/messages", response_model=ConversationDetailResponse)
async def reply_conversation(
    conversation_id: int,
    data: MessageReply,
    current_user: User = Depends(require_role("seeker", "recruiter")),
    db: AsyncSession = Depends(get_db),
):
    """Reply to an existing conversation."""
    return await MessageService.reply(db, current_user, conversation_id, data.content)


@router.post("/conversations/{conversation_id}/reply-suggestions", response_model=ReplySuggestionListResponse)
async def get_reply_suggestions(
    conversation_id: int,
    current_user: User = Depends(require_role("seeker", "recruiter")),
    db: AsyncSession = Depends(get_db),
):
    """Generate reply suggestions from the latest conversation context."""
    return await MessageService.get_reply_suggestions(db, current_user, conversation_id)


@router.post("/contact-exchanges", response_model=ContactExchangeResponse, status_code=http_status.HTTP_201_CREATED)
async def request_contact_exchange(
    data: ContactExchangeCreate,
    current_user: User = Depends(require_role("seeker", "recruiter")),
    db: AsyncSession = Depends(get_db),
):
    """Request structured contact exchange for a conversation."""
    return await MessageService.request_contact_exchange(db, current_user, data.conversation_id)


@router.get("/contact-exchanges/stats/summary", response_model=ContactExchangeStatsResponse)
async def get_contact_exchange_stats(
    current_user: User = Depends(require_role("recruiter", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """Summarize contact exchange outcomes for PRD successful connection tracking."""
    return await MessageService.get_contact_exchange_stats(db, current_user)


@router.post("/contact-exchanges/{exchange_id}/review", response_model=ContactExchangeResponse)
async def review_contact_exchange(
    exchange_id: int,
    data: ContactExchangeReview,
    current_user: User = Depends(require_role("seeker", "recruiter")),
    db: AsyncSession = Depends(get_db),
):
    """Accept or decline a contact exchange request."""
    return await MessageService.review_contact_exchange(db, current_user, exchange_id, data)
