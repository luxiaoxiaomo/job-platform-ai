"""add seeker job favorites and subscriptions

Revision ID: p5e7f9a1b304
Revises: o4d6e8f0a203
Create Date: 2026-06-19 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "p5e7f9a1b304"
down_revision: Union[str, None] = "o4d6e8f0a203"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_favorites",
        sa.Column("id", sa.Integer(), nullable=False, comment="Favorite ID"),
        sa.Column("job_id", sa.Integer(), nullable=False, comment="Job ID"),
        sa.Column("seeker_id", sa.Integer(), nullable=False, comment="Seeker user ID"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Created at"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["seeker_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "seeker_id", name="uq_job_favorites_job_seeker"),
    )
    op.create_index("idx_job_favorites_job_id", "job_favorites", ["job_id"])
    op.create_index("idx_job_favorites_seeker_id", "job_favorites", ["seeker_id"])
    op.create_index("idx_job_favorites_created_at", "job_favorites", ["created_at"])

    op.create_table(
        "job_subscriptions",
        sa.Column("id", sa.Integer(), nullable=False, comment="Subscription ID"),
        sa.Column("seeker_id", sa.Integer(), nullable=False, comment="Seeker user ID"),
        sa.Column("name", sa.String(length=100), nullable=False, comment="Subscription name"),
        sa.Column("keywords", sa.JSON(), nullable=False, comment="Keyword list"),
        sa.Column("city", sa.String(length=50), nullable=True, comment="Preferred city"),
        sa.Column("salary_min", sa.Integer(), nullable=True, comment="Minimum expected monthly salary in K"),
        sa.Column("salary_max", sa.Integer(), nullable=True, comment="Maximum expected monthly salary in K"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true(), comment="Whether alert is active"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Created at"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Updated at"),
        sa.ForeignKeyConstraint(["seeker_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_job_subscriptions_seeker_id", "job_subscriptions", ["seeker_id"])
    op.create_index("idx_job_subscriptions_active", "job_subscriptions", ["active"])
    op.create_index("idx_job_subscriptions_created_at", "job_subscriptions", ["created_at"])


def downgrade() -> None:
    op.drop_index("idx_job_subscriptions_created_at", table_name="job_subscriptions")
    op.drop_index("idx_job_subscriptions_active", table_name="job_subscriptions")
    op.drop_index("idx_job_subscriptions_seeker_id", table_name="job_subscriptions")
    op.drop_table("job_subscriptions")

    op.drop_index("idx_job_favorites_created_at", table_name="job_favorites")
    op.drop_index("idx_job_favorites_seeker_id", table_name="job_favorites")
    op.drop_index("idx_job_favorites_job_id", table_name="job_favorites")
    op.drop_table("job_favorites")
