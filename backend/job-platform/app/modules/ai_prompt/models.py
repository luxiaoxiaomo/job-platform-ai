"""
AI prompt configuration models.
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from app.db.base import Base


class AiPromptConfig(Base):
    """Versioned prompt template for one AI business scenario."""

    __tablename__ = "ai_prompt_configs"

    id = Column(Integer, primary_key=True, index=True, comment="Prompt config ID")
    scenario_key = Column(String(80), nullable=False, comment="Business scenario key")
    name = Column(String(120), nullable=False, comment="Display name")
    version = Column(Integer, nullable=False, default=1, comment="Version number")
    system_prompt = Column(Text, nullable=False, comment="System prompt")
    user_prompt_template = Column(Text, nullable=False, comment="User prompt template")
    output_schema = Column(Text, nullable=False, comment="Expected JSON output schema")
    is_active = Column(Boolean, nullable=False, default=False, comment="Whether this version is active")
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="Creator user ID")
    published_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="Publisher user ID")
    published_at = Column(DateTime, nullable=True, comment="Published at")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="Created at")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="Updated at")

    __table_args__ = (
        UniqueConstraint("scenario_key", "version", name="uq_ai_prompt_configs_scenario_version"),
    )
