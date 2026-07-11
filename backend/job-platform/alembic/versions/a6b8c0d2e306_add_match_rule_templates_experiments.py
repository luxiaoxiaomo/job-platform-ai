"""add match rule templates and experiments

Revision ID: a6b8c0d2e306
Revises: z5i7k9m1n235
Create Date: 2026-06-20 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "a6b8c0d2e306"
down_revision: Union[str, None] = "z5i7k9m1n235"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json_type():
    return sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade() -> None:
    op.add_column(
        "match_rule_configs",
        sa.Column("template_key", sa.String(length=80), nullable=False, server_default="default", comment="Rule template key"),
    )
    op.add_column(
        "match_rule_configs",
        sa.Column(
            "template_name",
            sa.String(length=120),
            nullable=False,
            server_default="Default template",
            comment="Rule template name",
        ),
    )
    op.create_index("idx_match_rule_configs_template_key", "match_rule_configs", ["template_key"], unique=False)

    op.drop_constraint("uq_match_rule_configs_scope_version", "match_rule_configs", type_="unique")
    op.create_unique_constraint(
        "uq_match_rule_configs_scope_template_version",
        "match_rule_configs",
        ["scope", "template_key", "version"],
    )

    op.create_table(
        "match_rule_experiments",
        sa.Column("id", sa.Integer(), nullable=False, comment="Match rule experiment ID"),
        sa.Column("name", sa.String(length=120), nullable=False, comment="Experiment name"),
        sa.Column("description", sa.Text(), nullable=False, server_default="", comment="Experiment description"),
        sa.Column("scope", sa.String(length=80), nullable=False, server_default="global", comment="Experiment scope"),
        sa.Column("template_key", sa.String(length=80), nullable=False, server_default="default", comment="Rule template key"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft", comment="draft/running/paused/ended"),
        sa.Column("traffic_percent", sa.Integer(), nullable=False, server_default="0", comment="Treatment traffic percentage"),
        sa.Column("control_config_id", sa.Integer(), nullable=False, comment="Control rule config ID"),
        sa.Column("treatment_config_id", sa.Integer(), nullable=False, comment="Treatment rule config ID"),
        sa.Column("audience", _json_type(), nullable=True, comment="Audience filter snapshot"),
        sa.Column("started_at", sa.DateTime(), nullable=True, comment="Started at"),
        sa.Column("ended_at", sa.DateTime(), nullable=True, comment="Ended at"),
        sa.Column("created_by", sa.Integer(), nullable=True, comment="Creator user ID"),
        sa.Column("updated_by", sa.Integer(), nullable=True, comment="Updater user ID"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Created at"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Updated at"),
        sa.ForeignKeyConstraint(["control_config_id"], ["match_rule_configs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["treatment_config_id"], ["match_rule_configs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_match_rule_experiments_id"), "match_rule_experiments", ["id"], unique=False)
    op.create_index("idx_match_rule_experiments_scope_template", "match_rule_experiments", ["scope", "template_key"], unique=False)
    op.create_index("idx_match_rule_experiments_status", "match_rule_experiments", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_match_rule_experiments_status", table_name="match_rule_experiments")
    op.drop_index("idx_match_rule_experiments_scope_template", table_name="match_rule_experiments")
    op.drop_index(op.f("ix_match_rule_experiments_id"), table_name="match_rule_experiments")
    op.drop_table("match_rule_experiments")

    op.drop_constraint("uq_match_rule_configs_scope_template_version", "match_rule_configs", type_="unique")
    op.create_unique_constraint("uq_match_rule_configs_scope_version", "match_rule_configs", ["scope", "version"])
    op.drop_index("idx_match_rule_configs_template_key", table_name="match_rule_configs")
    op.drop_column("match_rule_configs", "template_name")
    op.drop_column("match_rule_configs", "template_key")
