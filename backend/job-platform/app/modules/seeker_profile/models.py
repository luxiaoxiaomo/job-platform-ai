"""
Seeker profile data model.
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, JSON, String
from sqlalchemy.dialects.postgresql import JSONB
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
    standard_position_id = Column(
        Integer,
        ForeignKey("standard_positions.id", ondelete="SET NULL"),
        nullable=True,
        comment="Linked standard position ID",
    )
    target_position = Column(String(100), nullable=True, comment="Target position")
    expected_salary = Column(String(50), nullable=True, comment="Expected salary")
    city = Column(String(80), nullable=True, comment="Preferred city")
    tag_refs = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True, comment="Linked tag library snapshots")
    email = Column(String(120), nullable=True, comment="Contact email")
    wechat = Column(String(80), nullable=True, comment="WeChat ID")

    name_public = Column(Boolean, nullable=False, default=True, comment="Name visible to recruiters")
    phone_public = Column(Boolean, nullable=False, default=True, comment="Phone visible to recruiters")
    email_public = Column(Boolean, nullable=False, default=False, comment="Email visible to recruiters")
    wechat_public = Column(Boolean, nullable=False, default=False, comment="WeChat visible to recruiters")
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
    standard_position = relationship("StandardPosition")

    __table_args__ = (
        Index("idx_seeker_profiles_seeker_id", "seeker_id"),
        Index("idx_seeker_profiles_standard_position_id", "standard_position_id"),
        Index("idx_seeker_profiles_updated_at", "updated_at"),
    )

    def __repr__(self) -> str:
        return f"<SeekerProfile(id={self.id}, seeker_id={self.seeker_id})>"
