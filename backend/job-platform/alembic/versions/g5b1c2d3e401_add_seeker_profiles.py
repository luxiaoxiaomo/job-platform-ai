"""add seeker profiles

Revision ID: g5b1c2d3e401
Revises: f4a8b9c1d203
Create Date: 2026-06-15 09:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "g5b1c2d3e401"
down_revision: Union[str, None] = "f4a8b9c1d203"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "seeker_profiles",
        sa.Column("id", sa.Integer(), nullable=False, comment="Profile ID"),
        sa.Column("seeker_id", sa.Integer(), nullable=False, comment="Seeker user ID"),
        sa.Column("real_name", sa.String(length=50), nullable=True, comment="Real or display name"),
        sa.Column("gender", sa.String(length=20), nullable=True, comment="Gender"),
        sa.Column("education", sa.String(length=80), nullable=True, comment="Highest education"),
        sa.Column("experience_years", sa.Integer(), nullable=True, comment="Years of experience"),
        sa.Column("target_position", sa.String(length=100), nullable=True, comment="Target position"),
        sa.Column("expected_salary", sa.String(length=50), nullable=True, comment="Expected salary"),
        sa.Column("city", sa.String(length=80), nullable=True, comment="Preferred city"),
        sa.Column("name_public", sa.Boolean(), nullable=False, server_default=sa.true(), comment="Name visible to recruiters"),
        sa.Column("phone_public", sa.Boolean(), nullable=False, server_default=sa.true(), comment="Phone visible to recruiters"),
        sa.Column("education_public", sa.Boolean(), nullable=False, server_default=sa.true(), comment="Education visible to recruiters"),
        sa.Column("experience_public", sa.Boolean(), nullable=False, server_default=sa.false(), comment="Experience visible to recruiters"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Created at"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Updated at"),
        sa.ForeignKeyConstraint(["seeker_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("seeker_id"),
    )
    op.create_index(op.f("ix_seeker_profiles_id"), "seeker_profiles", ["id"], unique=False)
    op.create_index("idx_seeker_profiles_seeker_id", "seeker_profiles", ["seeker_id"], unique=False)
    op.create_index("idx_seeker_profiles_updated_at", "seeker_profiles", ["updated_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_seeker_profiles_updated_at", table_name="seeker_profiles")
    op.drop_index("idx_seeker_profiles_seeker_id", table_name="seeker_profiles")
    op.drop_index(op.f("ix_seeker_profiles_id"), table_name="seeker_profiles")
    op.drop_table("seeker_profiles")
