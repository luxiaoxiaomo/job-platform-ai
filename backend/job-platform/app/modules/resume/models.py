"""
Seeker resume data model.
"""
from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.modules.ai_prompt.models import AiPromptConfig  # noqa: F401
from app.modules.user.models import User  # noqa: F401


class SeekerResume(Base):
    """Latest uploaded resume for a seeker."""

    __tablename__ = "seeker_resumes"

    id = Column(Integer, primary_key=True, index=True, comment="Resume ID")
    seeker_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        comment="Seeker user ID",
    )
    file_url = Column(String(500), nullable=False, comment="Uploaded resume URL")
    file_name = Column(String(255), nullable=False, comment="Original file name")
    content_type = Column(String(100), nullable=True, comment="MIME content type")
    file_size = Column(Integer, nullable=False, comment="File size in bytes")
    parsed_snapshot = Column(Text, nullable=False, comment="Parsed resume snapshot used for applications")
    current_upload_id = Column(
        Integer,
        ForeignKey(
            "resume_uploads.id",
            name="fk_seeker_resumes_current_upload_id",
            ondelete="SET NULL",
            use_alter=True,
        ),
        nullable=True,
        comment="Current resume upload ID",
    )
    current_parse_run_id = Column(
        Integer,
        ForeignKey(
            "resume_parse_runs.id",
            name="fk_seeker_resumes_current_parse_run_id",
            ondelete="SET NULL",
            use_alter=True,
        ),
        nullable=True,
        comment="Current resume parse run ID",
    )
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="Created at")
    updated_at = Column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Updated at",
    )

    seeker = relationship("User")

    __table_args__ = (
        Index("idx_seeker_resumes_seeker_id", "seeker_id"),
        Index("idx_seeker_resumes_current_upload_id", "current_upload_id"),
        Index("idx_seeker_resumes_current_parse_run_id", "current_parse_run_id"),
        Index("idx_seeker_resumes_updated_at", "updated_at"),
    )

    def __repr__(self) -> str:
        return f"<SeekerResume(id={self.id}, seeker_id={self.seeker_id})>"


class ResumeUpload(Base):
    """Immutable history for every resume upload."""

    __tablename__ = "resume_uploads"

    id = Column(Integer, primary_key=True, index=True, comment="Upload ID")
    seeker_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="Seeker user ID")
    resume_id = Column(
        Integer,
        ForeignKey("seeker_resumes.id", ondelete="SET NULL"),
        nullable=True,
        comment="Current resume ID",
    )
    file_url = Column(String(500), nullable=False, comment="Uploaded file URL")
    storage_path = Column(String(500), nullable=False, comment="Server storage path")
    original_file_name = Column(String(255), nullable=False, comment="Original file name")
    content_type = Column(String(100), nullable=True, comment="MIME content type")
    file_ext = Column(String(20), nullable=False, comment="File extension")
    file_size = Column(Integer, nullable=False, comment="File size in bytes")
    sha256 = Column(String(64), nullable=False, comment="File SHA-256 hash")
    upload_source = Column(String(30), nullable=False, default="seeker_web", comment="seeker_web/admin_import/api")
    status = Column(String(30), nullable=False, default="uploaded", comment="uploaded/processing/parsed/failed")
    error_message = Column(Text, nullable=True, comment="Upload or parse error message")
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="Created at")
    updated_at = Column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Updated at",
    )

    seeker = relationship("User")
    resume = relationship("SeekerResume", foreign_keys=[resume_id])

    __table_args__ = (
        Index("idx_resume_uploads_seeker_created", "seeker_id", "created_at"),
        Index("idx_resume_uploads_resume_id", "resume_id"),
        Index("idx_resume_uploads_sha256", "sha256"),
        Index("idx_resume_uploads_status_created", "status", "created_at"),
    )


class ResumeParseRun(Base):
    """One parsing execution for one uploaded resume file."""

    __tablename__ = "resume_parse_runs"

    id = Column(Integer, primary_key=True, index=True, comment="Parse run ID")
    upload_id = Column(
        Integer,
        ForeignKey("resume_uploads.id", ondelete="CASCADE"),
        nullable=False,
        comment="Upload ID",
    )
    seeker_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="Seeker user ID")
    status = Column(
        String(30),
        nullable=False,
        default="pending",
        comment="pending/running/succeeded/completed_with_errors/failed",
    )
    parser_version = Column(String(50), nullable=False, comment="Parser version")
    prompt_config_id = Column(Integer, ForeignKey("ai_prompt_configs.id", ondelete="SET NULL"), nullable=True)
    prompt_version = Column(Integer, nullable=True, comment="Prompt version used by parser")
    extractor = Column(String(50), nullable=False, comment="docx/pdf_text/ocr/mock/manual")
    started_at = Column(DateTime, nullable=True, comment="Started at")
    finished_at = Column(DateTime, nullable=True, comment="Finished at")
    error_code = Column(String(80), nullable=True, comment="Error code")
    error_message = Column(Text, nullable=True, comment="Error message")
    metrics_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True, comment="Parser metrics")
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="Created at")
    updated_at = Column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Updated at",
    )

    upload = relationship("ResumeUpload")
    seeker = relationship("User")

    __table_args__ = (
        Index("idx_resume_parse_runs_upload_id", "upload_id"),
        Index("idx_resume_parse_runs_seeker_created", "seeker_id", "created_at"),
        Index("idx_resume_parse_runs_status_created", "status", "created_at"),
    )


class ResumeExtractedText(Base):
    """Extracted raw text for one parse run."""

    __tablename__ = "resume_extracted_texts"

    id = Column(Integer, primary_key=True, index=True, comment="Extracted text ID")
    parse_run_id = Column(
        Integer,
        ForeignKey("resume_parse_runs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="Parse run ID",
    )
    upload_id = Column(
        Integer,
        ForeignKey("resume_uploads.id", ondelete="CASCADE"),
        nullable=False,
        comment="Upload ID",
    )
    text = Column(Text, nullable=False, comment="Extracted plain text")
    text_hash = Column(String(64), nullable=False, comment="Text SHA-256 hash")
    language = Column(String(20), nullable=False, default="unknown", comment="zh/en/mixed/unknown")
    quality_score = Column(Float, nullable=False, default=0.0, comment="Extraction quality score 0-1")
    page_count = Column(Integer, nullable=True, comment="Page count")
    char_count = Column(Integer, nullable=False, default=0, comment="Character count")
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="Created at")

    parse_run = relationship("ResumeParseRun")
    upload = relationship("ResumeUpload")

    __table_args__ = (
        Index("idx_resume_extracted_texts_upload_id", "upload_id"),
        Index("idx_resume_extracted_texts_text_hash", "text_hash"),
    )


class ResumeChunk(Base):
    """Chunked resume text prepared for later RAG/embedding."""

    __tablename__ = "resume_chunks"

    id = Column(Integer, primary_key=True, index=True, comment="Chunk ID")
    parse_run_id = Column(
        Integer,
        ForeignKey("resume_parse_runs.id", ondelete="CASCADE"),
        nullable=False,
        comment="Parse run ID",
    )
    upload_id = Column(
        Integer,
        ForeignKey("resume_uploads.id", ondelete="CASCADE"),
        nullable=False,
        comment="Upload ID",
    )
    seeker_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="Seeker user ID")
    chunk_index = Column(Integer, nullable=False, comment="Chunk index in parse run")
    section = Column(String(50), nullable=False, default="raw", comment="basic/education/work/project/skill/raw")
    content = Column(Text, nullable=False, comment="Chunk content")
    content_hash = Column(String(64), nullable=False, comment="Chunk SHA-256 hash")
    token_count = Column(Integer, nullable=False, default=0, comment="Estimated token count")
    embedding_status = Column(String(30), nullable=False, default="pending", comment="pending/embedded/failed/skipped")
    embedding_provider = Column(String(50), nullable=True, comment="Embedding provider")
    embedding_model = Column(String(100), nullable=True, comment="Embedding model")
    vector_ref = Column(String(255), nullable=True, comment="External vector ID or pgvector reference")
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="Created at")

    parse_run = relationship("ResumeParseRun")
    upload = relationship("ResumeUpload")
    seeker = relationship("User")

    __table_args__ = (
        UniqueConstraint("parse_run_id", "chunk_index", name="uq_resume_chunks_parse_run_index"),
        Index("idx_resume_chunks_parse_run_id", "parse_run_id"),
        Index("idx_resume_chunks_upload_id", "upload_id"),
        Index("idx_resume_chunks_seeker_id", "seeker_id"),
        Index("idx_resume_chunks_embedding_status", "embedding_status"),
    )
