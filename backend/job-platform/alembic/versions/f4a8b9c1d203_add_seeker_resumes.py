"""add seeker resumes

Revision ID: f4a8b9c1d203
Revises: e3a7c2d9f401
Create Date: 2026-06-14 10:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f4a8b9c1d203"
down_revision: Union[str, None] = "e3a7c2d9f401"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "seeker_resumes",
        sa.Column("id", sa.Integer(), nullable=False, comment="Resume ID"),
        sa.Column("seeker_id", sa.Integer(), nullable=False, comment="Seeker user ID"),
        sa.Column("file_url", sa.String(length=500), nullable=False, comment="Uploaded resume URL"),
        sa.Column("file_name", sa.String(length=255), nullable=False, comment="Original file name"),
        sa.Column("content_type", sa.String(length=100), nullable=True, comment="MIME content type"),
        sa.Column("file_size", sa.Integer(), nullable=False, comment="File size in bytes"),
        sa.Column("parsed_snapshot", sa.Text(), nullable=False, comment="Parsed resume snapshot used for applications"),
        sa.Column("created_at", sa.DateTime(), nullable=False, comment="Created at"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, comment="Updated at"),
        sa.ForeignKeyConstraint(["seeker_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("seeker_id"),
    )
    op.create_index(op.f("ix_seeker_resumes_id"), "seeker_resumes", ["id"], unique=False)
    op.create_index("idx_seeker_resumes_seeker_id", "seeker_resumes", ["seeker_id"], unique=False)
    op.create_index("idx_seeker_resumes_updated_at", "seeker_resumes", ["updated_at"], unique=False)
    op.add_column("job_applications", sa.Column("resume_id", sa.Integer(), nullable=True, comment="Resume ID at submission time"))
    op.add_column("job_applications", sa.Column("resume_file_url", sa.String(length=500), nullable=True, comment="Resume file URL at submission time"))
    op.add_column("job_applications", sa.Column("resume_file_name", sa.String(length=255), nullable=True, comment="Resume file name at submission time"))
    op.create_foreign_key("fk_job_applications_resume_id", "job_applications", "seeker_resumes", ["resume_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("fk_job_applications_resume_id", "job_applications", type_="foreignkey")
    op.drop_column("job_applications", "resume_file_name")
    op.drop_column("job_applications", "resume_file_url")
    op.drop_column("job_applications", "resume_id")
    op.drop_index("idx_seeker_resumes_updated_at", table_name="seeker_resumes")
    op.drop_index("idx_seeker_resumes_seeker_id", table_name="seeker_resumes")
    op.drop_index(op.f("ix_seeker_resumes_id"), table_name="seeker_resumes")
    op.drop_table("seeker_resumes")
