"""Add job application timelines.

Revision ID: i7d3e5f6a701
Revises: h6c2d4e5f601
Create Date: 2026-06-15 17:20:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


revision: str = "i7d3e5f6a701"
down_revision: Union[str, None] = "h6c2d4e5f601"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_application_timelines",
        sa.Column("id", sa.Integer(), nullable=False, comment="Timeline ID"),
        sa.Column("application_id", sa.Integer(), nullable=False, comment="Application ID"),
        sa.Column("from_status", sa.String(length=30), nullable=True, comment="Previous application status"),
        sa.Column("to_status", sa.String(length=30), nullable=False, comment="New application status"),
        sa.Column("actor_id", sa.Integer(), nullable=True, comment="Actor user ID"),
        sa.Column("actor_role", sa.String(length=30), nullable=False, comment="seeker/recruiter/admin/system"),
        sa.Column("note", sa.Text(), nullable=True, comment="Timeline note"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"), comment="Created at"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["application_id"], ["job_applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_job_application_timelines_application_id",
        "job_application_timelines",
        ["application_id"],
        unique=False,
    )
    op.create_index(
        "idx_job_application_timelines_created_at",
        "job_application_timelines",
        ["created_at"],
        unique=False,
    )

    op.execute(
        """
        INSERT INTO job_application_timelines
            (application_id, from_status, to_status, actor_id, actor_role, note, created_at)
        SELECT
            id,
            NULL,
            status,
            CASE WHEN status = 'submitted' THEN seeker_id ELSE NULL END,
            CASE WHEN status = 'submitted' THEN 'seeker' ELSE 'system' END,
            CASE
                WHEN status = 'submitted' THEN 'Application submitted'
                ELSE 'Historical application status imported from existing application'
            END,
            created_at
        FROM job_applications
        """
    )


def downgrade() -> None:
    op.drop_index("idx_job_application_timelines_created_at", table_name="job_application_timelines")
    op.drop_index("idx_job_application_timelines_application_id", table_name="job_application_timelines")
    op.drop_table("job_application_timelines")
