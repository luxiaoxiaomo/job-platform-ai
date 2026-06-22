"""
Match rule configuration models.
"""
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class MatchRuleConfigModel(Base):
    """Versioned match rule config."""

    __tablename__ = "match_rule_configs"

    id = Column(Integer, primary_key=True, index=True, comment="Match rule config ID")
    name = Column(String(120), nullable=False, comment="Display name")
    strategy = Column(String(50), nullable=False, default="rule_v1", comment="Matching strategy")
    scope = Column(String(80), nullable=False, default="global", comment="global/job_category:tech/job_id:123")
    template_key = Column(String(80), nullable=False, default="default", comment="Rule template key")
    template_name = Column(String(120), nullable=False, default="Default template", comment="Rule template name")
    status = Column(String(30), nullable=False, default="draft", comment="draft/active/testing/archived")
    version = Column(Integer, nullable=False, default=1, comment="Version number")
    description = Column(Text, nullable=False, default="", comment="Rule description")
    parent_version_id = Column(
        Integer,
        ForeignKey("match_rule_configs.id", ondelete="SET NULL"),
        nullable=True,
        comment="Parent version ID",
    )
    effective_from = Column(DateTime, nullable=True, comment="Effective from")
    effective_to = Column(DateTime, nullable=True, comment="Effective to")
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="Creator user ID")
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="Updater user ID")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="Created at")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="Updated at")

    dimensions = relationship(
        "MatchRuleDimensionModel",
        back_populates="config",
        cascade="all, delete-orphan",
        order_by="MatchRuleDimensionModel.sort_order",
    )

    __table_args__ = (
        UniqueConstraint("scope", "template_key", "version", name="uq_match_rule_configs_scope_template_version"),
        Index("idx_match_rule_configs_scope_status", "scope", "status"),
        Index("idx_match_rule_configs_template_key", "template_key"),
        Index("idx_match_rule_configs_parent_version_id", "parent_version_id"),
    )

    def __repr__(self) -> str:
        return f"<MatchRuleConfigModel(id={self.id}, scope={self.scope}, version={self.version})>"


class MatchRuleExperimentModel(Base):
    """Gray/AB test entry for match rule configs."""

    __tablename__ = "match_rule_experiments"

    id = Column(Integer, primary_key=True, index=True, comment="Match rule experiment ID")
    name = Column(String(120), nullable=False, comment="Experiment name")
    description = Column(Text, nullable=False, default="", comment="Experiment description")
    scope = Column(String(80), nullable=False, default="global", comment="Experiment scope")
    template_key = Column(String(80), nullable=False, default="default", comment="Rule template key")
    status = Column(String(30), nullable=False, default="draft", comment="draft/running/paused/ended")
    traffic_percent = Column(Integer, nullable=False, default=0, comment="Treatment traffic percentage")
    control_config_id = Column(
        Integer,
        ForeignKey("match_rule_configs.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Control rule config ID",
    )
    treatment_config_id = Column(
        Integer,
        ForeignKey("match_rule_configs.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Treatment rule config ID",
    )
    audience = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True, comment="Audience filter snapshot")
    started_at = Column(DateTime, nullable=True, comment="Started at")
    ended_at = Column(DateTime, nullable=True, comment="Ended at")
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="Creator user ID")
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="Updater user ID")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="Created at")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="Updated at")

    control_config = relationship("MatchRuleConfigModel", foreign_keys=[control_config_id])
    treatment_config = relationship("MatchRuleConfigModel", foreign_keys=[treatment_config_id])

    __table_args__ = (
        Index("idx_match_rule_experiments_scope_template", "scope", "template_key"),
        Index("idx_match_rule_experiments_status", "status"),
    )


class MatchRuleMatchAuditModel(Base):
    """Persisted audit record for one rule-based match calculation."""

    __tablename__ = "match_rule_match_audits"

    id = Column(Integer, primary_key=True, index=True, comment="Match audit ID")
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, comment="Job ID")
    seeker_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="Seeker user ID")
    application_id = Column(Integer, ForeignKey("job_applications.id", ondelete="SET NULL"), nullable=True, comment="Application ID")
    profile_parse_run_id = Column(Integer, nullable=True, comment="Resume parse run ID")
    rule_config_id = Column(Integer, ForeignKey("match_rule_configs.id", ondelete="SET NULL"), nullable=True, comment="Rule config ID")
    experiment_id = Column(Integer, ForeignKey("match_rule_experiments.id", ondelete="SET NULL"), nullable=True, comment="Experiment ID")
    experiment_bucket = Column(String(20), nullable=True, comment="control/treatment")
    scope = Column(String(80), nullable=False, default="global", comment="Selected rule scope")
    template_key = Column(String(80), nullable=False, default="default", comment="Selected template key")
    source = Column(String(50), nullable=False, default="seeker_job_match", comment="Match source")
    overall_score = Column(Integer, nullable=False, comment="Overall score")
    level = Column(String(20), nullable=False, comment="Match level")
    recommendation = Column(String(80), nullable=False, comment="Recommendation")
    dimension_scores = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True, comment="Dimension score snapshot")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="Created at")

    job = relationship("Job")
    seeker = relationship("User", foreign_keys=[seeker_id])
    application = relationship("JobApplication")
    rule_config = relationship("MatchRuleConfigModel")
    experiment = relationship("MatchRuleExperimentModel")

    __table_args__ = (
        Index("idx_match_rule_match_audits_job_id", "job_id"),
        Index("idx_match_rule_match_audits_seeker_id", "seeker_id"),
        Index("idx_match_rule_match_audits_rule_config_id", "rule_config_id"),
        Index("idx_match_rule_match_audits_experiment_id", "experiment_id"),
        Index("idx_match_rule_match_audits_created_at", "created_at"),
    )


class MatchRuleOperationAuditModel(Base):
    """Admin operation audit for rule release and experiment governance."""

    __tablename__ = "match_rule_operation_audits"

    id = Column(Integer, primary_key=True, index=True, comment="Operation audit ID")
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="Actor user ID")
    action = Column(String(50), nullable=False, comment="publish_rule/block_publish/pause_experiment/resume_experiment/end_experiment")
    resource_type = Column(String(50), nullable=False, comment="rule_config/rule_experiment")
    resource_id = Column(Integer, nullable=False, comment="Resource ID")
    reason = Column(Text, nullable=False, default="", comment="Operation reason")
    before_snapshot = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True, comment="Before snapshot")
    after_snapshot = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True, comment="After snapshot")
    metadata_json = Column("metadata", JSON().with_variant(JSONB, "postgresql"), nullable=True, comment="Operation metadata")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="Created at")

    actor = relationship("User")

    __table_args__ = (
        Index("idx_match_rule_operation_audits_resource", "resource_type", "resource_id"),
        Index("idx_match_rule_operation_audits_actor_id", "actor_id"),
        Index("idx_match_rule_operation_audits_action", "action"),
        Index("idx_match_rule_operation_audits_created_at", "created_at"),
    )


class MatchRuleDimensionModel(Base):
    """One dimension under a match rule config."""

    __tablename__ = "match_rule_dimensions"

    id = Column(Integer, primary_key=True, index=True, comment="Match rule dimension ID")
    config_id = Column(
        Integer,
        ForeignKey("match_rule_configs.id", ondelete="CASCADE"),
        nullable=False,
        comment="Match rule config ID",
    )
    dimension_key = Column(String(50), nullable=False, comment="Dimension key")
    label = Column(String(80), nullable=False, comment="Display label")
    weight = Column(Float, nullable=False, default=0, comment="Configured weight")
    enabled = Column(Boolean, nullable=False, default=True, comment="Whether dimension is enabled")
    description = Column(Text, nullable=False, default="", comment="Dimension description")
    scoring_method = Column(Text, nullable=False, default="", comment="Human-readable scoring method")
    logic_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True, comment="Structured rule logic")
    sort_order = Column(Integer, nullable=False, default=0, comment="Display order")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="Created at")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="Updated at")

    config = relationship("MatchRuleConfigModel", back_populates="dimensions")

    __table_args__ = (
        UniqueConstraint("config_id", "dimension_key", name="uq_match_rule_dimensions_config_key"),
        Index("idx_match_rule_dimensions_config_id", "config_id"),
        Index("idx_match_rule_dimensions_dimension_key", "dimension_key"),
    )

    def __repr__(self) -> str:
        return f"<MatchRuleDimensionModel(id={self.id}, key={self.dimension_key})>"
