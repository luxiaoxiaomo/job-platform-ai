"""add intelligent matching strategy tables

Revision ID: d9e1f2a3b409
Revises: c8d0e2f4g608
Create Date: 2026-06-23 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d9e1f2a3b409"
down_revision: Union[str, None] = "c8d0e2f4g608"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json_type():
    return sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade() -> None:
    op.create_table(
        "intelligent_matching_strategies",
        sa.Column("id", sa.Integer(), nullable=False, comment="Intelligent strategy ID"),
        sa.Column("name", sa.String(length=120), nullable=False, comment="Strategy display name"),
        sa.Column("description", sa.Text(), nullable=False, server_default="", comment="Strategy description"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft", comment="draft/evaluating/testing/active/archived"),
        sa.Column("base_rule_config_id", sa.Integer(), nullable=False, comment="Baseline rule config ID"),
        sa.Column("vector_recall", _json_type(), nullable=False, comment="Vector recall configuration"),
        sa.Column("hybrid_weights", _json_type(), nullable=False, comment="Hybrid scoring weights"),
        sa.Column("fallback_policy", sa.String(length=50), nullable=False, server_default="rule_baseline", comment="Fallback policy"),
        sa.Column("created_by", sa.Integer(), nullable=True, comment="Creator user ID"),
        sa.Column("updated_by", sa.Integer(), nullable=True, comment="Updater user ID"),
        sa.Column("archived_at", sa.DateTime(), nullable=True, comment="Archived at"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Created at"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Updated at"),
        sa.ForeignKeyConstraint(["base_rule_config_id"], ["match_rule_configs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_intelligent_matching_strategies_name"),
    )
    op.create_index(op.f("ix_intelligent_matching_strategies_id"), "intelligent_matching_strategies", ["id"], unique=False)
    op.create_index("idx_intelligent_matching_strategies_status", "intelligent_matching_strategies", ["status"], unique=False)
    op.create_index("idx_intelligent_matching_strategies_base_rule", "intelligent_matching_strategies", ["base_rule_config_id"], unique=False)
    op.create_index("idx_intelligent_matching_strategies_created_at", "intelligent_matching_strategies", ["created_at"], unique=False)

    op.create_table(
        "intelligent_matching_evaluations",
        sa.Column("id", sa.Integer(), nullable=False, comment="Intelligent evaluation ID"),
        sa.Column("strategy_id", sa.Integer(), nullable=False, comment="Intelligent strategy ID"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending", comment="pending/running/completed/failed"),
        sa.Column("sample_count", sa.Integer(), nullable=False, server_default="0", comment="Evaluation sample count"),
        sa.Column("sample_source_distribution", _json_type(), nullable=False, comment="Sample source distribution"),
        sa.Column("baseline_metrics", _json_type(), nullable=False, comment="Baseline metrics summary"),
        sa.Column("hybrid_metrics", _json_type(), nullable=False, comment="Hybrid metrics summary"),
        sa.Column("decision_status", sa.String(length=40), nullable=False, server_default="insufficient_sample", comment="Evaluation decision"),
        sa.Column("risk_notes", _json_type(), nullable=False, comment="Evaluation risk notes"),
        sa.Column("created_by", sa.Integer(), nullable=True, comment="Creator user ID"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Created at"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Updated at"),
        sa.Column("completed_at", sa.DateTime(), nullable=True, comment="Completed at"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["strategy_id"], ["intelligent_matching_strategies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_intelligent_matching_evaluations_id"), "intelligent_matching_evaluations", ["id"], unique=False)
    op.create_index("idx_intelligent_matching_evaluations_strategy", "intelligent_matching_evaluations", ["strategy_id"], unique=False)
    op.create_index("idx_intelligent_matching_evaluations_status", "intelligent_matching_evaluations", ["status"], unique=False)
    op.create_index("idx_intelligent_matching_evaluations_decision", "intelligent_matching_evaluations", ["decision_status"], unique=False)
    op.create_index("idx_intelligent_matching_evaluations_created_at", "intelligent_matching_evaluations", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_intelligent_matching_evaluations_created_at", table_name="intelligent_matching_evaluations")
    op.drop_index("idx_intelligent_matching_evaluations_decision", table_name="intelligent_matching_evaluations")
    op.drop_index("idx_intelligent_matching_evaluations_status", table_name="intelligent_matching_evaluations")
    op.drop_index("idx_intelligent_matching_evaluations_strategy", table_name="intelligent_matching_evaluations")
    op.drop_index(op.f("ix_intelligent_matching_evaluations_id"), table_name="intelligent_matching_evaluations")
    op.drop_table("intelligent_matching_evaluations")

    op.drop_index("idx_intelligent_matching_strategies_created_at", table_name="intelligent_matching_strategies")
    op.drop_index("idx_intelligent_matching_strategies_base_rule", table_name="intelligent_matching_strategies")
    op.drop_index("idx_intelligent_matching_strategies_status", table_name="intelligent_matching_strategies")
    op.drop_index(op.f("ix_intelligent_matching_strategies_id"), table_name="intelligent_matching_strategies")
    op.drop_table("intelligent_matching_strategies")
