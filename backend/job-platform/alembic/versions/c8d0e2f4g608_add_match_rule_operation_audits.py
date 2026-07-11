"""add match rule operation audits

Revision ID: c8d0e2f4g608
Revises: b7c9d1e3f407
Create Date: 2026-06-21 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c8d0e2f4g608"
down_revision: Union[str, None] = "b7c9d1e3f407"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json_type():
    return sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade() -> None:
    op.create_table(
        "match_rule_operation_audits",
        sa.Column("id", sa.Integer(), nullable=False, comment="Operation audit ID"),
        sa.Column("actor_id", sa.Integer(), nullable=True, comment="Actor user ID"),
        sa.Column("action", sa.String(length=50), nullable=False, comment="Operation action"),
        sa.Column("resource_type", sa.String(length=50), nullable=False, comment="rule_config/rule_experiment"),
        sa.Column("resource_id", sa.Integer(), nullable=False, comment="Resource ID"),
        sa.Column("reason", sa.Text(), nullable=False, server_default="", comment="Operation reason"),
        sa.Column("before_snapshot", _json_type(), nullable=True, comment="Before snapshot"),
        sa.Column("after_snapshot", _json_type(), nullable=True, comment="After snapshot"),
        sa.Column("metadata", _json_type(), nullable=True, comment="Operation metadata"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Created at"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_match_rule_operation_audits_id"), "match_rule_operation_audits", ["id"], unique=False)
    op.create_index(
        "idx_match_rule_operation_audits_resource",
        "match_rule_operation_audits",
        ["resource_type", "resource_id"],
        unique=False,
    )
    op.create_index("idx_match_rule_operation_audits_actor_id", "match_rule_operation_audits", ["actor_id"], unique=False)
    op.create_index("idx_match_rule_operation_audits_action", "match_rule_operation_audits", ["action"], unique=False)
    op.create_index("idx_match_rule_operation_audits_created_at", "match_rule_operation_audits", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_match_rule_operation_audits_created_at", table_name="match_rule_operation_audits")
    op.drop_index("idx_match_rule_operation_audits_action", table_name="match_rule_operation_audits")
    op.drop_index("idx_match_rule_operation_audits_actor_id", table_name="match_rule_operation_audits")
    op.drop_index("idx_match_rule_operation_audits_resource", table_name="match_rule_operation_audits")
    op.drop_index(op.f("ix_match_rule_operation_audits_id"), table_name="match_rule_operation_audits")
    op.drop_table("match_rule_operation_audits")
