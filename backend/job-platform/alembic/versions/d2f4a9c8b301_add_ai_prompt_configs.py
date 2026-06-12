"""add_ai_prompt_configs

Revision ID: d2f4a9c8b301
Revises: c8e4b6a2d901
Create Date: 2026-06-11 20:30:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "d2f4a9c8b301"
down_revision = "c8e4b6a2d901"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_prompt_configs",
        sa.Column("id", sa.Integer(), nullable=False, comment="Prompt config ID"),
        sa.Column("scenario_key", sa.String(length=80), nullable=False, comment="Business scenario key"),
        sa.Column("name", sa.String(length=120), nullable=False, comment="Display name"),
        sa.Column("version", sa.Integer(), nullable=False, comment="Version number"),
        sa.Column("system_prompt", sa.Text(), nullable=False, comment="System prompt"),
        sa.Column("user_prompt_template", sa.Text(), nullable=False, comment="User prompt template"),
        sa.Column("output_schema", sa.Text(), nullable=False, comment="Expected JSON output schema"),
        sa.Column("is_active", sa.Boolean(), nullable=False, comment="Whether this version is active"),
        sa.Column("created_by", sa.Integer(), nullable=True, comment="Creator user ID"),
        sa.Column("published_by", sa.Integer(), nullable=True, comment="Publisher user ID"),
        sa.Column("published_at", sa.DateTime(), nullable=True, comment="Published at"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False, comment="Created at"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False, comment="Updated at"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["published_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scenario_key", "version", name="uq_ai_prompt_configs_scenario_version"),
    )
    op.create_index(op.f("ix_ai_prompt_configs_id"), "ai_prompt_configs", ["id"], unique=False)
    op.create_index("idx_ai_prompt_configs_scenario", "ai_prompt_configs", ["scenario_key"], unique=False)
    op.create_index("idx_ai_prompt_configs_active", "ai_prompt_configs", ["scenario_key", "is_active"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_ai_prompt_configs_active", table_name="ai_prompt_configs")
    op.drop_index("idx_ai_prompt_configs_scenario", table_name="ai_prompt_configs")
    op.drop_index(op.f("ix_ai_prompt_configs_id"), table_name="ai_prompt_configs")
    op.drop_table("ai_prompt_configs")
