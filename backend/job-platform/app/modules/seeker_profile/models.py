"""
Seeker profile data model.
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class SeekerProfile(Base):
    """Structured profile fields for a seeker."""

    __tablename__ = "seeker_profiles"

    id = Column(Integer, primary_key=True, index=True, comment="Profile ID")
    seeker_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        comment="Seeker user ID",
    )
    real_name = Column(String(50), nullable=True, comment="Real or display name")
    gender = Column(String(20), nullable=True, comment="Gender")
    education = Column(String(80), nullable=True, comment="Highest education")
    experience_years = Column(Integer, nullable=True, comment="Years of experience")
    target_position = Column(String(100), nullable=True, comment="Target position")
    expected_salary = Column(String(50), nullable=True, comment="Expected salary")
    city = Column(String(80), nullable=True, comment="Preferred city")

    name_public = Column(Boolean, nullable=False, default=True, comment="Name visible to recruiters")
    phone_public = Column(Boolean, nullable=False, default=True, comment="Phone visible to recruiters")
    education_public = Column(Boolean, nullable=False, default=True, comment="Education visible to recruiters")
    experience_public = Column(Boolean, nullable=False, default=False, comment="Experience visible to recruiters")

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
        Index("idx_seeker_profiles_seeker_id", "seeker_id"),
        Index("idx_seeker_profiles_updated_at", "updated_at"),
    )

    def __repr__(self) -> str:
        return f"<SeekerProfile(id={self.id}, seeker_id={self.seeker_id})>"
