"""
Seeker resume data model.
"""
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class SeekerResume(Base):
    """Latest uploaded resume for a seeker."""

    __tablename__ = "seeker_resumes"

    id = Column(Integer, primary_key=True, index=True, comment="Resume ID")
    seeker_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        comment="Seeker user ID",
    )
    file_url = Column(String(500), nullable=False, comment="Uploaded resume URL")
    file_name = Column(String(255), nullable=False, comment="Original file name")
    content_type = Column(String(100), nullable=True, comment="MIME content type")
    file_size = Column(Integer, nullable=False, comment="File size in bytes")
    parsed_snapshot = Column(Text, nullable=False, comment="Parsed resume snapshot used for applications")
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="Created at")
    updated_at = Column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Updated at",
    )

    seeker = relationship("User")

    __table_args__ = (
        Index("idx_seeker_resumes_seeker_id", "seeker_id"),
        Index("idx_seeker_resumes_updated_at", "updated_at"),
    )

    def __repr__(self) -> str:
        return f"<SeekerResume(id={self.id}, seeker_id={self.seeker_id})>"
