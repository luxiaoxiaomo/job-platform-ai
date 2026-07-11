"""
Message and contact exchange data models.
"""
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Conversation(Base):
    """A job-specific conversation between one seeker and one recruiter."""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True, comment="Conversation ID")
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, comment="Job ID")
    seeker_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="Seeker user ID")
    recruiter_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="Recruiter user ID")
    last_message_at = Column(DateTime, nullable=True, comment="Last message time")
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="Created at")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="Updated at")

    job = relationship("Job")
    seeker = relationship("User", foreign_keys=[seeker_id])
    recruiter = relationship("User", foreign_keys=[recruiter_id])

    __table_args__ = (
        UniqueConstraint("job_id", "seeker_id", name="uq_conversations_job_seeker"),
        Index("idx_conversations_job_id", "job_id"),
        Index("idx_conversations_seeker_id", "seeker_id"),
        Index("idx_conversations_recruiter_id", "recruiter_id"),
        Index("idx_conversations_last_message_at", "last_message_at"),
    )


class ConversationMessage(Base):
    """One text message inside a conversation."""

    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, index=True, comment="Message ID")
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, comment="Conversation ID")
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="Sender user ID")
    sender_role = Column(String(30), nullable=False, comment="seeker/recruiter")
    content = Column(Text, nullable=False, comment="Sanitized message content")
    original_content = Column(Text, nullable=True, comment="Original message content when sanitized")
    moderation_status = Column(String(30), nullable=False, default="pass", comment="pass/masked")
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="Created at")

    conversation = relationship("Conversation")
    sender = relationship("User")

    __table_args__ = (
        Index("idx_conversation_messages_conversation_id", "conversation_id"),
        Index("idx_conversation_messages_sender_id", "sender_id"),
        Index("idx_conversation_messages_created_at", "created_at"),
    )


class ContactExchange(Base):
    """Mutual confirmation for exchanging structured contact fields."""

    __tablename__ = "contact_exchanges"

    id = Column(Integer, primary_key=True, index=True, comment="Contact exchange ID")
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, comment="Conversation ID")
    requester_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="Requester user ID")
    requester_role = Column(String(30), nullable=False, comment="seeker/recruiter")
    status = Column(String(30), nullable=False, default="pending", comment="pending/accepted/declined")
    responder_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="Responder user ID")
    responded_at = Column(DateTime, nullable=True, comment="Responded at")
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="Created at")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="Updated at")

    conversation = relationship("Conversation")
    requester = relationship("User", foreign_keys=[requester_id])
    responder = relationship("User", foreign_keys=[responder_id])

    __table_args__ = (
        Index("idx_contact_exchanges_conversation_id", "conversation_id"),
        Index("idx_contact_exchanges_status", "status"),
        Index("idx_contact_exchanges_requester_id", "requester_id"),
    )
