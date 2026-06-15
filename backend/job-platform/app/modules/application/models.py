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
    resume_id = Column(
        Integer,
        ForeignKey("seeker_resumes.id", ondelete="SET NULL"),
        nullable=True,
        comment="Resume ID at submission time",
    )

    status = Column(
        String(30),
        nullable=False,
        default="submitted",
        comment="submitted/viewed/interview_invited/rejected/hired",
    )
    resume_snapshot = Column(Text, nullable=True, comment="Resume snapshot at submission time")
    resume_file_url = Column(String(500), nullable=True, comment="Resume file URL at submission time")
    resume_file_name = Column(String(255), nullable=True, comment="Resume file name at submission time")
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
    resume = relationship("SeekerResume")

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


class JobApplicationTimeline(Base):
    """Status history for one job application."""

    __tablename__ = "job_application_timelines"

    id = Column(Integer, primary_key=True, index=True, comment="Timeline ID")
    application_id = Column(
        Integer,
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
        comment="Application ID",
    )
    from_status = Column(String(30), nullable=True, comment="Previous application status")
    to_status = Column(String(30), nullable=False, comment="New application status")
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="Actor user ID")
    actor_role = Column(String(30), nullable=False, comment="seeker/recruiter/admin/system")
    note = Column(Text, nullable=True, comment="Timeline note")
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="Created at")

    application = relationship("JobApplication")
    actor = relationship("User")

    __table_args__ = (
        Index("idx_job_application_timelines_application_id", "application_id"),
        Index("idx_job_application_timelines_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<JobApplicationTimeline(id={self.id}, application_id={self.application_id}, to_status={self.to_status})>"
