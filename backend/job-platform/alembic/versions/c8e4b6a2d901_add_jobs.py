"""add_jobs

Revision ID: c8e4b6a2d901
Revises: b7c2f4d8a901
Create Date: 2026-06-11 10:30:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "c8e4b6a2d901"
down_revision = "b7c2f4d8a901"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), nullable=False, comment="Job ID"),
        sa.Column("recruiter_id", sa.Integer(), nullable=False, comment="Recruiter user ID"),
        sa.Column("title", sa.String(length=100), nullable=False, comment="Job title"),
        sa.Column("city", sa.String(length=50), nullable=False, comment="Work city"),
        sa.Column("salary_min", sa.Integer(), nullable=False, comment="Minimum monthly salary in K"),
        sa.Column("salary_max", sa.Integer(), nullable=False, comment="Maximum monthly salary in K"),
        sa.Column("experience", sa.String(length=50), nullable=False, comment="Experience requirement"),
        sa.Column("education", sa.String(length=50), nullable=False, comment="Education requirement"),
        sa.Column("description", sa.Text(), nullable=False, comment="Job responsibilities"),
        sa.Column("requirement", sa.Text(), nullable=False, comment="Job requirements"),
        sa.Column("benefits", sa.Text(), nullable=True, comment="Benefits"),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment="Job tags"),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False, comment="draft/pending/active/closed/rejected"),
        sa.Column("reject_reason", sa.Text(), nullable=True, comment="Reject reason"),
        sa.Column("reviewer_id", sa.Integer(), nullable=True, comment="Reviewer user ID"),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True, comment="Reviewed at"),
        sa.Column("published_at", sa.DateTime(), nullable=True, comment="Published at"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False, comment="Created at"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False, comment="Updated at"),
        sa.ForeignKeyConstraint(["recruiter_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_jobs_id"), "jobs", ["id"], unique=False)
    op.create_index("idx_jobs_recruiter_id", "jobs", ["recruiter_id"], unique=False)
    op.create_index("idx_jobs_status", "jobs", ["status"], unique=False)
    op.create_index("idx_jobs_city", "jobs", ["city"], unique=False)
    op.create_index("idx_jobs_published_at", "jobs", ["published_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_jobs_published_at", table_name="jobs")
    op.drop_index("idx_jobs_city", table_name="jobs")
    op.drop_index("idx_jobs_status", table_name="jobs")
    op.drop_index("idx_jobs_recruiter_id", table_name="jobs")
    op.drop_index(op.f("ix_jobs_id"), table_name="jobs")
    op.drop_table("jobs")
