"""add match rule match audits

Revision ID: b7c9d1e3f407
Revises: a6b8c0d2e306
Create Date: 2026-06-21 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b7c9d1e3f407"
down_revision: Union[str, None] = "a6b8c0d2e306"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json_type():
    return sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade() -> None:
    op.create_table(
        "match_rule_match_audits",
        sa.Column("id", sa.Integer(), nullable=False, comment="Match audit ID"),
        sa.Column("job_id", sa.Integer(), nullable=False, comment="Job ID"),
        sa.Column("seeker_id", sa.Integer(), nullable=False, comment="Seeker user ID"),
        sa.Column("application_id", sa.Integer(), nullable=True, comment="Application ID"),
        sa.Column("profile_parse_run_id", sa.Integer(), nullable=True, comment="Resume parse run ID"),
        sa.Column("rule_config_id", sa.Integer(), nullable=True, comment="Rule config ID"),
        sa.Column("experiment_id", sa.Integer(), nullable=True, comment="Experiment ID"),
        sa.Column("experiment_bucket", sa.String(length=20), nullable=True, comment="control/treatment"),
        sa.Column("scope", sa.String(length=80), nullable=False, server_default="global", comment="Selected rule scope"),
        sa.Column("template_key", sa.String(length=80), nullable=False, server_default="default", comment="Selected template key"),
        sa.Column("source", sa.String(length=50), nullable=False, server_default="seeker_job_match", comment="Match source"),
        sa.Column("overall_score", sa.Integer(), nullable=False, comment="Overall score"),
        sa.Column("level", sa.String(length=20), nullable=False, comment="Match level"),
        sa.Column("recommendation", sa.String(length=80), nullable=False, comment="Recommendation"),
        sa.Column("dimension_scores", _json_type(), nullable=True, comment="Dimension score snapshot"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Created at"),
        sa.ForeignKeyConstraint(["application_id"], ["job_applications.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["experiment_id"], ["match_rule_experiments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rule_config_id"], ["match_rule_configs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["seeker_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_match_rule_match_audits_id"), "match_rule_match_audits", ["id"], unique=False)
    op.create_index("idx_match_rule_match_audits_job_id", "match_rule_match_audits", ["job_id"], unique=False)
    op.create_index("idx_match_rule_match_audits_seeker_id", "match_rule_match_audits", ["seeker_id"], unique=False)
    op.create_index("idx_match_rule_match_audits_rule_config_id", "match_rule_match_audits", ["rule_config_id"], unique=False)
    op.create_index("idx_match_rule_match_audits_experiment_id", "match_rule_match_audits", ["experiment_id"], unique=False)
    op.create_index("idx_match_rule_match_audits_created_at", "match_rule_match_audits", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_match_rule_match_audits_created_at", table_name="match_rule_match_audits")
    op.drop_index("idx_match_rule_match_audits_experiment_id", table_name="match_rule_match_audits")
    op.drop_index("idx_match_rule_match_audits_rule_config_id", table_name="match_rule_match_audits")
    op.drop_index("idx_match_rule_match_audits_seeker_id", table_name="match_rule_match_audits")
    op.drop_index("idx_match_rule_match_audits_job_id", table_name="match_rule_match_audits")
    op.drop_index(op.f("ix_match_rule_match_audits_id"), table_name="match_rule_match_audits")
    op.drop_table("match_rule_match_audits")
