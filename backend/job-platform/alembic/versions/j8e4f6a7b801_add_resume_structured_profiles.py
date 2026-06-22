"""add resume structured profiles

Revision ID: j8e4f6a7b801
Revises: i7d3e5f6a701
Create Date: 2026-06-15 20:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "j8e4f6a7b801"
down_revision: Union[str, None] = "i7d3e5f6a701"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json_type():
    return sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def _common_columns() -> list[sa.Column]:
    return [
        sa.Column("seeker_id", sa.Integer(), nullable=False),
        sa.Column("upload_id", sa.Integer(), nullable=False),
        sa.Column("parse_run_id", sa.Integer(), nullable=False),
        sa.Column("structured_profile_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=30), nullable=False, server_default="parser"),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("source_json", _json_type(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    ]


def _common_fks() -> list[sa.ForeignKeyConstraint]:
    return [
        sa.ForeignKeyConstraint(["parse_run_id"], ["resume_parse_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["seeker_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["structured_profile_id"], ["resume_structured_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["upload_id"], ["resume_uploads.id"], ondelete="CASCADE"),
    ]


def upgrade() -> None:
    op.create_table(
        "resume_structured_profiles",
        sa.Column("id", sa.Integer(), nullable=False, comment="Structured profile ID"),
        sa.Column("seeker_id", sa.Integer(), nullable=False, comment="Seeker user ID"),
        sa.Column("upload_id", sa.Integer(), nullable=False, comment="Upload ID"),
        sa.Column("parse_run_id", sa.Integer(), nullable=False, comment="Parse run ID"),
        sa.Column("schema_version", sa.String(length=50), nullable=False, server_default="resume-structured-v1", comment="Structured schema"),
        sa.Column("prompt_config_id", sa.Integer(), nullable=True),
        sa.Column("prompt_version", sa.Integer(), nullable=True, comment="Prompt version"),
        sa.Column("source", sa.String(length=30), nullable=False, server_default="manual", comment="manual/rule/llm/import"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft", comment="draft/validated/needs_review/confirmed/rejected"),
        sa.Column("confidence_score", sa.Float(), nullable=True, comment="Overall confidence 0-1"),
        sa.Column("structured_json", _json_type(), nullable=False, comment="Structured resume JSON"),
        sa.Column("validation_errors", _json_type(), nullable=True, comment="Validation errors"),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True, comment="Confirmed at"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Created at"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Updated at"),
        sa.ForeignKeyConstraint(["parse_run_id"], ["resume_parse_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["prompt_config_id"], ["ai_prompt_configs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["seeker_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["upload_id"], ["resume_uploads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("parse_run_id", "schema_version", name="uq_resume_structured_parse_schema"),
    )
    op.create_index(op.f("ix_resume_structured_profiles_id"), "resume_structured_profiles", ["id"], unique=False)
    op.create_index("idx_resume_structured_profiles_parse_run_id", "resume_structured_profiles", ["parse_run_id"], unique=False)
    op.create_index("idx_resume_structured_profiles_seeker_created", "resume_structured_profiles", ["seeker_id", "created_at"], unique=False)
    op.create_index("idx_resume_structured_profiles_status", "resume_structured_profiles", ["status"], unique=False)
    op.create_index("idx_resume_structured_profiles_upload_id", "resume_structured_profiles", ["upload_id"], unique=False)

    op.create_table(
        "resume_basic_infos",
        sa.Column("id", sa.Integer(), nullable=False, comment="Basic info ID"),
        sa.Column("seeker_id", sa.Integer(), nullable=False, comment="Seeker user ID"),
        sa.Column("upload_id", sa.Integer(), nullable=False),
        sa.Column("parse_run_id", sa.Integer(), nullable=False),
        sa.Column("structured_profile_id", sa.Integer(), nullable=False),
        sa.Column("real_name", sa.String(length=100), nullable=True),
        sa.Column("gender", sa.String(length=20), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("highest_education", sa.String(length=100), nullable=True),
        sa.Column("work_years", sa.Float(), nullable=True),
        sa.Column("current_city", sa.String(length=100), nullable=True),
        sa.Column("target_position", sa.String(length=120), nullable=True),
        sa.Column("expected_salary", sa.String(length=100), nullable=True),
        sa.Column("source", sa.String(length=30), nullable=False, server_default="parser"),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("source_json", _json_type(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["parse_run_id"], ["resume_parse_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["seeker_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["structured_profile_id"], ["resume_structured_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["upload_id"], ["resume_uploads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("structured_profile_id", name="uq_resume_basic_infos_profile"),
    )
    op.create_index(op.f("ix_resume_basic_infos_id"), "resume_basic_infos", ["id"], unique=False)
    op.create_index("idx_resume_basic_infos_highest_education", "resume_basic_infos", ["highest_education"], unique=False)
    op.create_index("idx_resume_basic_infos_profile_id", "resume_basic_infos", ["structured_profile_id"], unique=False)
    op.create_index("idx_resume_basic_infos_seeker_id", "resume_basic_infos", ["seeker_id"], unique=False)
    op.create_index("idx_resume_basic_infos_work_years", "resume_basic_infos", ["work_years"], unique=False)

    op.create_table(
        "resume_educations",
        sa.Column("id", sa.Integer(), nullable=False, comment="Education ID"),
        *_common_columns(),
        sa.Column("school_name", sa.String(length=200), nullable=True),
        sa.Column("major", sa.String(length=200), nullable=True),
        sa.Column("degree", sa.String(length=100), nullable=True),
        sa.Column("education_level", sa.String(length=100), nullable=True),
        sa.Column("start_date", sa.String(length=30), nullable=True),
        sa.Column("end_date", sa.String(length=30), nullable=True),
        sa.Column("is_full_time", sa.Boolean(), nullable=True),
        *_common_fks(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_resume_educations_id"), "resume_educations", ["id"], unique=False)
    op.create_index("idx_resume_educations_profile_id", "resume_educations", ["structured_profile_id"], unique=False)
    op.create_index("idx_resume_educations_school_name", "resume_educations", ["school_name"], unique=False)
    op.create_index("idx_resume_educations_seeker_id", "resume_educations", ["seeker_id"], unique=False)

    op.create_table(
        "resume_work_experiences",
        sa.Column("id", sa.Integer(), nullable=False, comment="Work experience ID"),
        *_common_columns(),
        sa.Column("company_name", sa.String(length=200), nullable=True),
        sa.Column("position", sa.String(length=200), nullable=True),
        sa.Column("start_date", sa.String(length=30), nullable=True),
        sa.Column("end_date", sa.String(length=30), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        *_common_fks(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_resume_work_experiences_id"), "resume_work_experiences", ["id"], unique=False)
    op.create_index("idx_resume_work_experiences_company_name", "resume_work_experiences", ["company_name"], unique=False)
    op.create_index("idx_resume_work_experiences_position", "resume_work_experiences", ["position"], unique=False)
    op.create_index("idx_resume_work_experiences_profile_id", "resume_work_experiences", ["structured_profile_id"], unique=False)
    op.create_index("idx_resume_work_experiences_seeker_id", "resume_work_experiences", ["seeker_id"], unique=False)

    op.create_table(
        "resume_projects",
        sa.Column("id", sa.Integer(), nullable=False, comment="Project ID"),
        *_common_columns(),
        sa.Column("project_name", sa.String(length=200), nullable=True),
        sa.Column("role", sa.String(length=200), nullable=True),
        sa.Column("start_date", sa.String(length=30), nullable=True),
        sa.Column("end_date", sa.String(length=30), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("responsibility", sa.Text(), nullable=True),
        *_common_fks(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_resume_projects_id"), "resume_projects", ["id"], unique=False)
    op.create_index("idx_resume_projects_profile_id", "resume_projects", ["structured_profile_id"], unique=False)
    op.create_index("idx_resume_projects_project_name", "resume_projects", ["project_name"], unique=False)
    op.create_index("idx_resume_projects_seeker_id", "resume_projects", ["seeker_id"], unique=False)

    op.create_table(
        "resume_skills",
        sa.Column("id", sa.Integer(), nullable=False, comment="Skill ID"),
        *_common_columns(),
        sa.Column("skill_name", sa.String(length=150), nullable=False),
        sa.Column("skill_level", sa.String(length=80), nullable=True),
        sa.Column("category", sa.String(length=80), nullable=True),
        *_common_fks(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_resume_skills_id"), "resume_skills", ["id"], unique=False)
    op.create_index("idx_resume_skills_category", "resume_skills", ["category"], unique=False)
    op.create_index("idx_resume_skills_profile_id", "resume_skills", ["structured_profile_id"], unique=False)
    op.create_index("idx_resume_skills_seeker_id", "resume_skills", ["seeker_id"], unique=False)
    op.create_index("idx_resume_skills_skill_name", "resume_skills", ["skill_name"], unique=False)

    op.create_table(
        "resume_certificates",
        sa.Column("id", sa.Integer(), nullable=False, comment="Certificate ID"),
        *_common_columns(),
        sa.Column("certificate_name", sa.String(length=200), nullable=False),
        sa.Column("certificate_type", sa.String(length=100), nullable=True),
        sa.Column("issuer", sa.String(length=200), nullable=True),
        sa.Column("issued_at", sa.String(length=30), nullable=True),
        *_common_fks(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_resume_certificates_id"), "resume_certificates", ["id"], unique=False)
    op.create_index("idx_resume_certificates_name", "resume_certificates", ["certificate_name"], unique=False)
    op.create_index("idx_resume_certificates_profile_id", "resume_certificates", ["structured_profile_id"], unique=False)
    op.create_index("idx_resume_certificates_seeker_id", "resume_certificates", ["seeker_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_resume_certificates_seeker_id", table_name="resume_certificates")
    op.drop_index("idx_resume_certificates_profile_id", table_name="resume_certificates")
    op.drop_index("idx_resume_certificates_name", table_name="resume_certificates")
    op.drop_index(op.f("ix_resume_certificates_id"), table_name="resume_certificates")
    op.drop_table("resume_certificates")

    op.drop_index("idx_resume_skills_skill_name", table_name="resume_skills")
    op.drop_index("idx_resume_skills_seeker_id", table_name="resume_skills")
    op.drop_index("idx_resume_skills_profile_id", table_name="resume_skills")
    op.drop_index("idx_resume_skills_category", table_name="resume_skills")
    op.drop_index(op.f("ix_resume_skills_id"), table_name="resume_skills")
    op.drop_table("resume_skills")

    op.drop_index("idx_resume_projects_seeker_id", table_name="resume_projects")
    op.drop_index("idx_resume_projects_project_name", table_name="resume_projects")
    op.drop_index("idx_resume_projects_profile_id", table_name="resume_projects")
    op.drop_index(op.f("ix_resume_projects_id"), table_name="resume_projects")
    op.drop_table("resume_projects")

    op.drop_index("idx_resume_work_experiences_seeker_id", table_name="resume_work_experiences")
    op.drop_index("idx_resume_work_experiences_profile_id", table_name="resume_work_experiences")
    op.drop_index("idx_resume_work_experiences_position", table_name="resume_work_experiences")
    op.drop_index("idx_resume_work_experiences_company_name", table_name="resume_work_experiences")
    op.drop_index(op.f("ix_resume_work_experiences_id"), table_name="resume_work_experiences")
    op.drop_table("resume_work_experiences")

    op.drop_index("idx_resume_educations_seeker_id", table_name="resume_educations")
    op.drop_index("idx_resume_educations_school_name", table_name="resume_educations")
    op.drop_index("idx_resume_educations_profile_id", table_name="resume_educations")
    op.drop_index(op.f("ix_resume_educations_id"), table_name="resume_educations")
    op.drop_table("resume_educations")

    op.drop_index("idx_resume_basic_infos_work_years", table_name="resume_basic_infos")
    op.drop_index("idx_resume_basic_infos_seeker_id", table_name="resume_basic_infos")
    op.drop_index("idx_resume_basic_infos_profile_id", table_name="resume_basic_infos")
    op.drop_index("idx_resume_basic_infos_highest_education", table_name="resume_basic_infos")
    op.drop_index(op.f("ix_resume_basic_infos_id"), table_name="resume_basic_infos")
    op.drop_table("resume_basic_infos")

    op.drop_index("idx_resume_structured_profiles_upload_id", table_name="resume_structured_profiles")
    op.drop_index("idx_resume_structured_profiles_status", table_name="resume_structured_profiles")
    op.drop_index("idx_resume_structured_profiles_seeker_created", table_name="resume_structured_profiles")
    op.drop_index("idx_resume_structured_profiles_parse_run_id", table_name="resume_structured_profiles")
    op.drop_index(op.f("ix_resume_structured_profiles_id"), table_name="resume_structured_profiles")
    op.drop_table("resume_structured_profiles")
