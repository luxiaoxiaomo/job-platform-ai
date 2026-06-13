"""add job applications

Revision ID: e3a7c2d9f401
Revises: d2f4a9c8b301
Create Date: 2026-06-12 22:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e3a7c2d9f401"
down_revision: Union[str, None] = "d2f4a9c8b301"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_applications",
        sa.Column("id", sa.Integer(), nullable=False, comment="Application ID"),
        sa.Column("job_id", sa.Integer(), nullable=False, comment="Job ID"),
        sa.Column("seeker_id", sa.Integer(), nullable=False, comment="Seeker user ID"),
        sa.Column("recruiter_id", sa.Integer(), nullable=False, comment="Recruiter user ID"),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            comment="submitted/viewed/interview_invited/rejected/hired",
        ),
        sa.Column("resume_snapshot", sa.Text(), nullable=True, comment="Resume snapshot at submission time"),
        sa.Column("cover_message", sa.Text(), nullable=True, comment="Seeker cover message"),
        sa.Column("reject_reason", sa.Text(), nullable=True, comment="Recruiter reject reason"),
        sa.Column("viewed_at", sa.DateTime(), nullable=True, comment="First viewed at"),
        sa.Column("status_updated_at", sa.DateTime(), nullable=True, comment="Status updated at"),
        sa.Column("created_at", sa.DateTime(), nullable=False, comment="Created at"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, comment="Updated at"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recruiter_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["seeker_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "seeker_id", name="uq_job_applications_job_seeker"),
    )
    op.create_index(op.f("ix_job_applications_id"), "job_applications", ["id"], unique=False)
    op.create_index("idx_job_applications_job_id", "job_applications", ["job_id"], unique=False)
    op.create_index("idx_job_applications_seeker_id", "job_applications", ["seeker_id"], unique=False)
    op.create_index("idx_job_applications_recruiter_id", "job_applications", ["recruiter_id"], unique=False)
    op.create_index("idx_job_applications_status", "job_applications", ["status"], unique=False)
    op.create_index("idx_job_applications_created_at", "job_applications", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_job_applications_created_at", table_name="job_applications")
    op.drop_index("idx_job_applications_status", table_name="job_applications")
    op.drop_index("idx_job_applications_recruiter_id", table_name="job_applications")
    op.drop_index("idx_job_applications_seeker_id", table_name="job_applications")
    op.drop_index("idx_job_applications_job_id", table_name="job_applications")
    op.drop_index(op.f("ix_job_applications_id"), table_name="job_applications")
    op.drop_table("job_applications")
