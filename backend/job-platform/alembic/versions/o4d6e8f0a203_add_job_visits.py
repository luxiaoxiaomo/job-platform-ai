"""add job visits

Revision ID: o4d6e8f0a203
Revises: n3c5d7e9f102
Create Date: 2026-06-19 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "o4d6e8f0a203"
down_revision: Union[str, None] = "n3c5d7e9f102"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_visits",
        sa.Column("id", sa.Integer(), nullable=False, comment="Visit ID"),
        sa.Column("job_id", sa.Integer(), nullable=False, comment="Job ID"),
        sa.Column("recruiter_id", sa.Integer(), nullable=False, comment="Recruiter user ID"),
        sa.Column("seeker_id", sa.Integer(), nullable=False, comment="Seeker user ID"),
        sa.Column("source", sa.String(length=50), nullable=False, server_default="public_detail", comment="Visit source"),
        sa.Column("viewed_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Viewed at"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recruiter_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["seeker_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_job_visits_job_id", "job_visits", ["job_id"])
    op.create_index("idx_job_visits_recruiter_id", "job_visits", ["recruiter_id"])
    op.create_index("idx_job_visits_seeker_id", "job_visits", ["seeker_id"])
    op.create_index("idx_job_visits_job_seeker", "job_visits", ["job_id", "seeker_id"])
    op.create_index("idx_job_visits_viewed_at", "job_visits", ["viewed_at"])


def downgrade() -> None:
    op.drop_index("idx_job_visits_viewed_at", table_name="job_visits")
    op.drop_index("idx_job_visits_job_seeker", table_name="job_visits")
    op.drop_index("idx_job_visits_seeker_id", table_name="job_visits")
    op.drop_index("idx_job_visits_recruiter_id", table_name="job_visits")
    op.drop_index("idx_job_visits_job_id", table_name="job_visits")
    op.drop_table("job_visits")
