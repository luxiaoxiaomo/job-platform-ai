"""add resume parse foundation

Revision ID: h6c2d4e5f601
Revises: g5b1c2d3e401
Create Date: 2026-06-15 14:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "h6c2d4e5f601"
down_revision: Union[str, None] = "g5b1c2d3e401"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json_type():
    return sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade() -> None:
    op.create_table(
        "resume_uploads",
        sa.Column("id", sa.Integer(), nullable=False, comment="Upload ID"),
        sa.Column("seeker_id", sa.Integer(), nullable=False, comment="Seeker user ID"),
        sa.Column("resume_id", sa.Integer(), nullable=True, comment="Current resume ID"),
        sa.Column("file_url", sa.String(length=500), nullable=False, comment="Uploaded file URL"),
        sa.Column("storage_path", sa.String(length=500), nullable=False, comment="Server storage path"),
        sa.Column("original_file_name", sa.String(length=255), nullable=False, comment="Original file name"),
        sa.Column("content_type", sa.String(length=100), nullable=True, comment="MIME content type"),
        sa.Column("file_ext", sa.String(length=20), nullable=False, comment="File extension"),
        sa.Column("file_size", sa.Integer(), nullable=False, comment="File size in bytes"),
        sa.Column("sha256", sa.String(length=64), nullable=False, comment="File SHA-256 hash"),
        sa.Column("upload_source", sa.String(length=30), nullable=False, server_default="seeker_web", comment="seeker_web/admin_import/api"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="uploaded", comment="uploaded/processing/parsed/failed"),
        sa.Column("error_message", sa.Text(), nullable=True, comment="Upload or parse error message"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Created at"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Updated at"),
        sa.ForeignKeyConstraint(["resume_id"], ["seeker_resumes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["seeker_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_resume_uploads_id"), "resume_uploads", ["id"], unique=False)
    op.create_index("idx_resume_uploads_resume_id", "resume_uploads", ["resume_id"], unique=False)
    op.create_index("idx_resume_uploads_seeker_created", "resume_uploads", ["seeker_id", "created_at"], unique=False)
    op.create_index("idx_resume_uploads_sha256", "resume_uploads", ["sha256"], unique=False)
    op.create_index("idx_resume_uploads_status_created", "resume_uploads", ["status", "created_at"], unique=False)

    op.create_table(
        "resume_parse_runs",
        sa.Column("id", sa.Integer(), nullable=False, comment="Parse run ID"),
        sa.Column("upload_id", sa.Integer(), nullable=False, comment="Upload ID"),
        sa.Column("seeker_id", sa.Integer(), nullable=False, comment="Seeker user ID"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending", comment="pending/running/succeeded/completed_with_errors/failed"),
        sa.Column("parser_version", sa.String(length=50), nullable=False, comment="Parser version"),
        sa.Column("prompt_config_id", sa.Integer(), nullable=True),
        sa.Column("prompt_version", sa.Integer(), nullable=True, comment="Prompt version used by parser"),
        sa.Column("extractor", sa.String(length=50), nullable=False, comment="docx/pdf_text/ocr/mock/manual"),
        sa.Column("started_at", sa.DateTime(), nullable=True, comment="Started at"),
        sa.Column("finished_at", sa.DateTime(), nullable=True, comment="Finished at"),
        sa.Column("error_code", sa.String(length=80), nullable=True, comment="Error code"),
        sa.Column("error_message", sa.Text(), nullable=True, comment="Error message"),
        sa.Column("metrics_json", _json_type(), nullable=True, comment="Parser metrics"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Created at"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Updated at"),
        sa.ForeignKeyConstraint(["prompt_config_id"], ["ai_prompt_configs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["seeker_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["upload_id"], ["resume_uploads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_resume_parse_runs_id"), "resume_parse_runs", ["id"], unique=False)
    op.create_index("idx_resume_parse_runs_seeker_created", "resume_parse_runs", ["seeker_id", "created_at"], unique=False)
    op.create_index("idx_resume_parse_runs_status_created", "resume_parse_runs", ["status", "created_at"], unique=False)
    op.create_index("idx_resume_parse_runs_upload_id", "resume_parse_runs", ["upload_id"], unique=False)

    op.create_table(
        "resume_extracted_texts",
        sa.Column("id", sa.Integer(), nullable=False, comment="Extracted text ID"),
        sa.Column("parse_run_id", sa.Integer(), nullable=False, comment="Parse run ID"),
        sa.Column("upload_id", sa.Integer(), nullable=False, comment="Upload ID"),
        sa.Column("text", sa.Text(), nullable=False, comment="Extracted plain text"),
        sa.Column("text_hash", sa.String(length=64), nullable=False, comment="Text SHA-256 hash"),
        sa.Column("language", sa.String(length=20), nullable=False, server_default="unknown", comment="zh/en/mixed/unknown"),
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="0", comment="Extraction quality score 0-1"),
        sa.Column("page_count", sa.Integer(), nullable=True, comment="Page count"),
        sa.Column("char_count", sa.Integer(), nullable=False, server_default="0", comment="Character count"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Created at"),
        sa.ForeignKeyConstraint(["parse_run_id"], ["resume_parse_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["upload_id"], ["resume_uploads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("parse_run_id"),
    )
    op.create_index(op.f("ix_resume_extracted_texts_id"), "resume_extracted_texts", ["id"], unique=False)
    op.create_index("idx_resume_extracted_texts_text_hash", "resume_extracted_texts", ["text_hash"], unique=False)
    op.create_index("idx_resume_extracted_texts_upload_id", "resume_extracted_texts", ["upload_id"], unique=False)

    op.create_table(
        "resume_chunks",
        sa.Column("id", sa.Integer(), nullable=False, comment="Chunk ID"),
        sa.Column("parse_run_id", sa.Integer(), nullable=False, comment="Parse run ID"),
        sa.Column("upload_id", sa.Integer(), nullable=False, comment="Upload ID"),
        sa.Column("seeker_id", sa.Integer(), nullable=False, comment="Seeker user ID"),
        sa.Column("chunk_index", sa.Integer(), nullable=False, comment="Chunk index in parse run"),
        sa.Column("section", sa.String(length=50), nullable=False, server_default="raw", comment="basic/education/work/project/skill/raw"),
        sa.Column("content", sa.Text(), nullable=False, comment="Chunk content"),
        sa.Column("content_hash", sa.String(length=64), nullable=False, comment="Chunk SHA-256 hash"),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0", comment="Estimated token count"),
        sa.Column("embedding_status", sa.String(length=30), nullable=False, server_default="pending", comment="pending/embedded/failed/skipped"),
        sa.Column("embedding_provider", sa.String(length=50), nullable=True, comment="Embedding provider"),
        sa.Column("embedding_model", sa.String(length=100), nullable=True, comment="Embedding model"),
        sa.Column("vector_ref", sa.String(length=255), nullable=True, comment="External vector ID or pgvector reference"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Created at"),
        sa.ForeignKeyConstraint(["parse_run_id"], ["resume_parse_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["seeker_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["upload_id"], ["resume_uploads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("parse_run_id", "chunk_index", name="uq_resume_chunks_parse_run_index"),
    )
    op.create_index(op.f("ix_resume_chunks_id"), "resume_chunks", ["id"], unique=False)
    op.create_index("idx_resume_chunks_embedding_status", "resume_chunks", ["embedding_status"], unique=False)
    op.create_index("idx_resume_chunks_parse_run_id", "resume_chunks", ["parse_run_id"], unique=False)
    op.create_index("idx_resume_chunks_seeker_id", "resume_chunks", ["seeker_id"], unique=False)
    op.create_index("idx_resume_chunks_upload_id", "resume_chunks", ["upload_id"], unique=False)

    op.add_column("seeker_resumes", sa.Column("current_upload_id", sa.Integer(), nullable=True, comment="Current resume upload ID"))
    op.add_column("seeker_resumes", sa.Column("current_parse_run_id", sa.Integer(), nullable=True, comment="Current resume parse run ID"))
    op.create_foreign_key("fk_seeker_resumes_current_upload_id", "seeker_resumes", "resume_uploads", ["current_upload_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_seeker_resumes_current_parse_run_id", "seeker_resumes", "resume_parse_runs", ["current_parse_run_id"], ["id"], ondelete="SET NULL")
    op.create_index("idx_seeker_resumes_current_upload_id", "seeker_resumes", ["current_upload_id"], unique=False)
    op.create_index("idx_seeker_resumes_current_parse_run_id", "seeker_resumes", ["current_parse_run_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_seeker_resumes_current_parse_run_id", table_name="seeker_resumes")
    op.drop_index("idx_seeker_resumes_current_upload_id", table_name="seeker_resumes")
    op.drop_constraint("fk_seeker_resumes_current_parse_run_id", "seeker_resumes", type_="foreignkey")
    op.drop_constraint("fk_seeker_resumes_current_upload_id", "seeker_resumes", type_="foreignkey")
    op.drop_column("seeker_resumes", "current_parse_run_id")
    op.drop_column("seeker_resumes", "current_upload_id")

    op.drop_index("idx_resume_chunks_upload_id", table_name="resume_chunks")
    op.drop_index("idx_resume_chunks_seeker_id", table_name="resume_chunks")
    op.drop_index("idx_resume_chunks_parse_run_id", table_name="resume_chunks")
    op.drop_index("idx_resume_chunks_embedding_status", table_name="resume_chunks")
    op.drop_index(op.f("ix_resume_chunks_id"), table_name="resume_chunks")
    op.drop_table("resume_chunks")

    op.drop_index("idx_resume_extracted_texts_upload_id", table_name="resume_extracted_texts")
    op.drop_index("idx_resume_extracted_texts_text_hash", table_name="resume_extracted_texts")
    op.drop_index(op.f("ix_resume_extracted_texts_id"), table_name="resume_extracted_texts")
    op.drop_table("resume_extracted_texts")

    op.drop_index("idx_resume_parse_runs_upload_id", table_name="resume_parse_runs")
    op.drop_index("idx_resume_parse_runs_status_created", table_name="resume_parse_runs")
    op.drop_index("idx_resume_parse_runs_seeker_created", table_name="resume_parse_runs")
    op.drop_index(op.f("ix_resume_parse_runs_id"), table_name="resume_parse_runs")
    op.drop_table("resume_parse_runs")

    op.drop_index("idx_resume_uploads_status_created", table_name="resume_uploads")
    op.drop_index("idx_resume_uploads_sha256", table_name="resume_uploads")
    op.drop_index("idx_resume_uploads_seeker_created", table_name="resume_uploads")
    op.drop_index("idx_resume_uploads_resume_id", table_name="resume_uploads")
    op.drop_index(op.f("ix_resume_uploads_id"), table_name="resume_uploads")
    op.drop_table("resume_uploads")
