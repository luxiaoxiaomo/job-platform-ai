"""
Job application data model.
"""
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class JobApplication(Base):
    """A seeker's application to a job."""

    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True, comment="Application ID")
    job_id = Column(
        Integer,
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        comment="Job ID",
    )
    seeker_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Seeker user ID",
    )
    recruiter_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Recruiter user ID",
    )

    status = Column(
        String(30),
        nullable=False,
        default="submitted",
        comment="submitted/viewed/interview_invited/rejected/hired",
    )
    resume_snapshot = Column(Text, nullable=True, comment="Resume snapshot at submission time")
    cover_message = Column(Text, nullable=True, comment="Seeker cover message")
    reject_reason = Column(Text, nullable=True, comment="Recruiter reject reason")

    viewed_at = Column(DateTime, nullable=True, comment="First viewed at")
    status_updated_at = Column(DateTime, nullable=True, comment="Status updated at")
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="Created at")
    updated_at = Column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Updated at",
    )

    job = relationship("Job")
    seeker = relationship("User", foreign_keys=[seeker_id])
    recruiter = relationship("User", foreign_keys=[recruiter_id])

    __table_args__ = (
        UniqueConstraint("job_id", "seeker_id", name="uq_job_applications_job_seeker"),
        Index("idx_job_applications_job_id", "job_id"),
        Index("idx_job_applications_seeker_id", "seeker_id"),
        Index("idx_job_applications_recruiter_id", "recruiter_id"),
        Index("idx_job_applications_status", "status"),
        Index("idx_job_applications_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<JobApplication(id={self.id}, job_id={self.job_id}, status={self.status})>"
