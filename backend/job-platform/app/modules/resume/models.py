"""
Seeker resume data model.
"""
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
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


class ResumeStructuredProfile(Base):
    """Structured JSON result generated from one parse run."""

    __tablename__ = "resume_structured_profiles"

    id = Column(Integer, primary_key=True, index=True, comment="Structured profile ID")
    seeker_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="Seeker user ID")
    upload_id = Column(
        Integer,
        ForeignKey("resume_uploads.id", ondelete="CASCADE"),
        nullable=False,
        comment="Upload ID",
    )
    parse_run_id = Column(
        Integer,
        ForeignKey("resume_parse_runs.id", ondelete="CASCADE"),
        nullable=False,
        comment="Parse run ID",
    )
    schema_version = Column(String(50), nullable=False, default="resume-structured-v1", comment="Structured schema")
    prompt_config_id = Column(Integer, ForeignKey("ai_prompt_configs.id", ondelete="SET NULL"), nullable=True)
    prompt_version = Column(Integer, nullable=True, comment="Prompt version")
    source = Column(String(30), nullable=False, default="manual", comment="manual/rule/llm/import")
    status = Column(String(30), nullable=False, default="draft", comment="draft/validated/needs_review/confirmed/rejected")
    confidence_score = Column(Float, nullable=True, comment="Overall confidence 0-1")
    structured_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, comment="Structured resume JSON")
    tag_refs = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True, comment="Linked tag library snapshots")
    validation_errors = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True, comment="Validation errors")
    confirmed_at = Column(DateTime, nullable=True, comment="Confirmed at")
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="Created at")
    updated_at = Column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Updated at",
    )

    seeker = relationship("User")
    upload = relationship("ResumeUpload")
    parse_run = relationship("ResumeParseRun")

    __table_args__ = (
        UniqueConstraint("parse_run_id", "schema_version", name="uq_resume_structured_parse_schema"),
        Index("idx_resume_structured_profiles_seeker_created", "seeker_id", "created_at"),
        Index("idx_resume_structured_profiles_parse_run_id", "parse_run_id"),
        Index("idx_resume_structured_profiles_upload_id", "upload_id"),
        Index("idx_resume_structured_profiles_status", "status"),
    )


class ResumeBasicInfo(Base):
    """Normalized basic resume fields used for filtering."""

    __tablename__ = "resume_basic_infos"

    id = Column(Integer, primary_key=True, index=True, comment="Basic info ID")
    seeker_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="Seeker user ID")
    upload_id = Column(Integer, ForeignKey("resume_uploads.id", ondelete="CASCADE"), nullable=False)
    parse_run_id = Column(Integer, ForeignKey("resume_parse_runs.id", ondelete="CASCADE"), nullable=False)
    structured_profile_id = Column(
        Integer,
        ForeignKey("resume_structured_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    real_name = Column(String(100), nullable=True)
    gender = Column(String(20), nullable=True)
    age = Column(Integer, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    highest_education = Column(String(100), nullable=True)
    work_years = Column(Float, nullable=True)
    current_city = Column(String(100), nullable=True)
    target_position = Column(String(120), nullable=True)
    expected_salary = Column(String(100), nullable=True)
    source = Column(String(30), nullable=False, default="parser")
    confidence_score = Column(Float, nullable=True)
    raw_text = Column(Text, nullable=True)
    source_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("structured_profile_id", name="uq_resume_basic_infos_profile"),
        Index("idx_resume_basic_infos_seeker_id", "seeker_id"),
        Index("idx_resume_basic_infos_profile_id", "structured_profile_id"),
        Index("idx_resume_basic_infos_highest_education", "highest_education"),
        Index("idx_resume_basic_infos_work_years", "work_years"),
    )


class ResumeEducation(Base):
    """Normalized education experience."""

    __tablename__ = "resume_educations"

    id = Column(Integer, primary_key=True, index=True, comment="Education ID")
    seeker_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    upload_id = Column(Integer, ForeignKey("resume_uploads.id", ondelete="CASCADE"), nullable=False)
    parse_run_id = Column(Integer, ForeignKey("resume_parse_runs.id", ondelete="CASCADE"), nullable=False)
    structured_profile_id = Column(Integer, ForeignKey("resume_structured_profiles.id", ondelete="CASCADE"), nullable=False)
    school_name = Column(String(200), nullable=True)
    major = Column(String(200), nullable=True)
    degree = Column(String(100), nullable=True)
    education_level = Column(String(100), nullable=True)
    start_date = Column(String(30), nullable=True)
    end_date = Column(String(30), nullable=True)
    is_full_time = Column(Boolean, nullable=True)
    source = Column(String(30), nullable=False, default="parser")
    confidence_score = Column(Float, nullable=True)
    raw_text = Column(Text, nullable=True)
    source_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_resume_educations_seeker_id", "seeker_id"),
        Index("idx_resume_educations_profile_id", "structured_profile_id"),
        Index("idx_resume_educations_school_name", "school_name"),
    )


class ResumeWorkExperience(Base):
    """Normalized work experience."""

    __tablename__ = "resume_work_experiences"

    id = Column(Integer, primary_key=True, index=True, comment="Work experience ID")
    seeker_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    upload_id = Column(Integer, ForeignKey("resume_uploads.id", ondelete="CASCADE"), nullable=False)
    parse_run_id = Column(Integer, ForeignKey("resume_parse_runs.id", ondelete="CASCADE"), nullable=False)
    structured_profile_id = Column(Integer, ForeignKey("resume_structured_profiles.id", ondelete="CASCADE"), nullable=False)
    company_name = Column(String(200), nullable=True)
    position = Column(String(200), nullable=True)
    start_date = Column(String(30), nullable=True)
    end_date = Column(String(30), nullable=True)
    description = Column(Text, nullable=True)
    source = Column(String(30), nullable=False, default="parser")
    confidence_score = Column(Float, nullable=True)
    raw_text = Column(Text, nullable=True)
    source_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_resume_work_experiences_seeker_id", "seeker_id"),
        Index("idx_resume_work_experiences_profile_id", "structured_profile_id"),
        Index("idx_resume_work_experiences_company_name", "company_name"),
        Index("idx_resume_work_experiences_position", "position"),
    )


class ResumeProject(Base):
    """Normalized project experience."""

    __tablename__ = "resume_projects"

    id = Column(Integer, primary_key=True, index=True, comment="Project ID")
    seeker_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    upload_id = Column(Integer, ForeignKey("resume_uploads.id", ondelete="CASCADE"), nullable=False)
    parse_run_id = Column(Integer, ForeignKey("resume_parse_runs.id", ondelete="CASCADE"), nullable=False)
    structured_profile_id = Column(Integer, ForeignKey("resume_structured_profiles.id", ondelete="CASCADE"), nullable=False)
    project_name = Column(String(200), nullable=True)
    role = Column(String(200), nullable=True)
    start_date = Column(String(30), nullable=True)
    end_date = Column(String(30), nullable=True)
    description = Column(Text, nullable=True)
    responsibility = Column(Text, nullable=True)
    source = Column(String(30), nullable=False, default="parser")
    confidence_score = Column(Float, nullable=True)
    raw_text = Column(Text, nullable=True)
    source_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_resume_projects_seeker_id", "seeker_id"),
        Index("idx_resume_projects_profile_id", "structured_profile_id"),
        Index("idx_resume_projects_project_name", "project_name"),
    )


class ResumeSkill(Base):
    """Normalized resume skill."""

    __tablename__ = "resume_skills"

    id = Column(Integer, primary_key=True, index=True, comment="Skill ID")
    seeker_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    upload_id = Column(Integer, ForeignKey("resume_uploads.id", ondelete="CASCADE"), nullable=False)
    parse_run_id = Column(Integer, ForeignKey("resume_parse_runs.id", ondelete="CASCADE"), nullable=False)
    structured_profile_id = Column(Integer, ForeignKey("resume_structured_profiles.id", ondelete="CASCADE"), nullable=False)
    skill_name = Column(String(150), nullable=False)
    skill_level = Column(String(80), nullable=True)
    category = Column(String(80), nullable=True)
    source = Column(String(30), nullable=False, default="parser")
    confidence_score = Column(Float, nullable=True)
    raw_text = Column(Text, nullable=True)
    source_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_resume_skills_seeker_id", "seeker_id"),
        Index("idx_resume_skills_profile_id", "structured_profile_id"),
        Index("idx_resume_skills_skill_name", "skill_name"),
        Index("idx_resume_skills_category", "category"),
    )


class ResumeCertificate(Base):
    """Normalized resume certificate."""

    __tablename__ = "resume_certificates"

    id = Column(Integer, primary_key=True, index=True, comment="Certificate ID")
    seeker_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    upload_id = Column(Integer, ForeignKey("resume_uploads.id", ondelete="CASCADE"), nullable=False)
    parse_run_id = Column(Integer, ForeignKey("resume_parse_runs.id", ondelete="CASCADE"), nullable=False)
    structured_profile_id = Column(Integer, ForeignKey("resume_structured_profiles.id", ondelete="CASCADE"), nullable=False)
    certificate_name = Column(String(200), nullable=False)
    certificate_type = Column(String(100), nullable=True)
    issuer = Column(String(200), nullable=True)
    issued_at = Column(String(30), nullable=True)
    source = Column(String(30), nullable=False, default="parser")
    confidence_score = Column(Float, nullable=True)
    raw_text = Column(Text, nullable=True)
    source_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_resume_certificates_seeker_id", "seeker_id"),
        Index("idx_resume_certificates_profile_id", "structured_profile_id"),
        Index("idx_resume_certificates_name", "certificate_name"),
    )
