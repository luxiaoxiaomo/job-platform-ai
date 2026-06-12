"""
Job posting data model.
"""
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Job(Base):
    """Recruiter job posting."""

    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True, comment="Job ID")
    recruiter_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Recruiter user ID",
    )

    title = Column(String(100), nullable=False, comment="Job title")
    city = Column(String(50), nullable=False, comment="Work city")
    salary_min = Column(Integer, nullable=False, comment="Minimum monthly salary in K")
    salary_max = Column(Integer, nullable=False, comment="Maximum monthly salary in K")
    experience = Column(String(50), nullable=False, comment="Experience requirement")
    education = Column(String(50), nullable=False, comment="Education requirement")

    description = Column(Text, nullable=False, comment="Job responsibilities")
    requirement = Column(Text, nullable=False, comment="Job requirements")
    benefits = Column(Text, nullable=True, comment="Benefits")
    tags = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True, comment="Job tags")

    status = Column(
        String(20),
        nullable=False,
        default="pending",
        comment="draft/pending/active/closed/rejected",
    )
    reject_reason = Column(Text, nullable=True, comment="Reject reason")

    reviewer_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Reviewer user ID",
    )
    reviewed_at = Column(DateTime, nullable=True, comment="Reviewed at")

    published_at = Column(DateTime, nullable=True, comment="Published at")
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="Created at")
    updated_at = Column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Updated at",
    )

    recruiter = relationship("User", foreign_keys=[recruiter_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])

    __table_args__ = (
        Index("idx_jobs_recruiter_id", "recruiter_id"),
        Index("idx_jobs_status", "status"),
        Index("idx_jobs_city", "city"),
        Index("idx_jobs_published_at", "published_at"),
    )

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, title={self.title}, status={self.status})>"
