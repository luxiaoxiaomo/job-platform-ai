"""
Job posting data model.
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
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

    standard_position_id = Column(
        Integer,
        ForeignKey("standard_positions.id", ondelete="SET NULL"),
        nullable=True,
        comment="Linked standard position ID",
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
    tag_refs = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True, comment="Linked tag library snapshots")
    company_display_mode = Column(
        String(20),
        nullable=False,
        default="display_name",
        server_default="display_name",
        comment="display_name/company_name/anonymous",
    )
    contact_phone_public = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
        comment="Whether recruiter phone is visible after contact exchange/public detail",
    )
    contact_email_public = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
        comment="Whether recruiter email is visible after contact exchange/public detail",
    )
    contact_wechat_public = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
        comment="Whether recruiter WeChat is visible after contact exchange/public detail",
    )

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
    view_count = Column(Integer, nullable=False, default=0, server_default="0", comment="Public detail view count")
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
    standard_position = relationship("StandardPosition")

    __table_args__ = (
        Index("idx_jobs_recruiter_id", "recruiter_id"),
        Index("idx_jobs_standard_position_id", "standard_position_id"),
        Index("idx_jobs_status", "status"),
        Index("idx_jobs_city", "city"),
        Index("idx_jobs_published_at", "published_at"),
    )

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, title={self.title}, status={self.status})>"


class JobVisit(Base):
    """One seeker visit event for a public job detail page."""

    __tablename__ = "job_visits"

    id = Column(Integer, primary_key=True, index=True, comment="Visit ID")
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, comment="Job ID")
    recruiter_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="Recruiter user ID")
    seeker_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="Seeker user ID")
    source = Column(String(50), nullable=False, default="public_detail", comment="Visit source")
    viewed_at = Column(DateTime, default=func.now(), nullable=False, comment="Viewed at")

    job = relationship("Job")
    recruiter = relationship("User", foreign_keys=[recruiter_id])
    seeker = relationship("User", foreign_keys=[seeker_id])

    __table_args__ = (
        Index("idx_job_visits_job_id", "job_id"),
        Index("idx_job_visits_recruiter_id", "recruiter_id"),
        Index("idx_job_visits_seeker_id", "seeker_id"),
        Index("idx_job_visits_job_seeker", "job_id", "seeker_id"),
        Index("idx_job_visits_viewed_at", "viewed_at"),
    )

    def __repr__(self) -> str:
        return f"<JobVisit(id={self.id}, job_id={self.job_id}, seeker_id={self.seeker_id})>"


class JobFavorite(Base):
    """A seeker-saved job."""

    __tablename__ = "job_favorites"

    id = Column(Integer, primary_key=True, index=True, comment="Favorite ID")
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, comment="Job ID")
    seeker_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="Seeker user ID")
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="Created at")

    job = relationship("Job")
    seeker = relationship("User", foreign_keys=[seeker_id])

    __table_args__ = (
        UniqueConstraint("job_id", "seeker_id", name="uq_job_favorites_job_seeker"),
        Index("idx_job_favorites_job_id", "job_id"),
        Index("idx_job_favorites_seeker_id", "seeker_id"),
        Index("idx_job_favorites_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<JobFavorite(id={self.id}, job_id={self.job_id}, seeker_id={self.seeker_id})>"


class JobSubscription(Base):
    """A seeker job-alert subscription profile."""

    __tablename__ = "job_subscriptions"

    id = Column(Integer, primary_key=True, index=True, comment="Subscription ID")
    seeker_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="Seeker user ID")
    name = Column(String(100), nullable=False, comment="Subscription name")
    keywords = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, comment="Keyword list")
    city = Column(String(50), nullable=True, comment="Preferred city")
    salary_min = Column(Integer, nullable=True, comment="Minimum expected monthly salary in K")
    salary_max = Column(Integer, nullable=True, comment="Maximum expected monthly salary in K")
    active = Column(Boolean, nullable=False, default=True, server_default="1", comment="Whether alert is active")
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="Created at")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="Updated at")

    seeker = relationship("User", foreign_keys=[seeker_id])

    __table_args__ = (
        Index("idx_job_subscriptions_seeker_id", "seeker_id"),
        Index("idx_job_subscriptions_active", "active"),
        Index("idx_job_subscriptions_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<JobSubscription(id={self.id}, seeker_id={self.seeker_id}, active={self.active})>"
