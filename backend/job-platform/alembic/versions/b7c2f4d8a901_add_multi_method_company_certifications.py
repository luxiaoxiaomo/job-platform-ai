"""add_multi_method_company_certifications

Revision ID: b7c2f4d8a901
Revises: 9f3d9e82a701
Create Date: 2026-06-10 18:30:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b7c2f4d8a901"
down_revision = "9f3d9e82a701"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "company_certifications",
        sa.Column(
            "verification_method",
            sa.String(length=30),
            nullable=False,
            server_default="business_license",
            comment="认证方式：business_license/enterprise_email/hr_authorization",
        ),
    )
    op.add_column("company_certifications", sa.Column("proof_file_url", sa.String(length=500), nullable=True, comment="辅助证明材料URL"))
    op.add_column("company_certifications", sa.Column("proof_file_name", sa.String(length=200), nullable=True, comment="辅助证明材料文件名"))
    op.add_column("company_certifications", sa.Column("work_email", sa.String(length=120), nullable=True, comment="企业邮箱"))
    op.add_column("company_certifications", sa.Column("applicant_name", sa.String(length=50), nullable=True, comment="申请人姓名"))
    op.add_column("company_certifications", sa.Column("applicant_title", sa.String(length=80), nullable=True, comment="申请人职位"))
    op.add_column("company_certifications", sa.Column("applicant_phone", sa.String(length=30), nullable=True, comment="申请人联系电话"))
    op.add_column("company_certifications", sa.Column("verification_note", sa.Text(), nullable=True, comment="认证补充说明"))

    op.alter_column("company_certifications", "unified_social_credit_code", existing_type=sa.String(length=18), nullable=True)
    op.alter_column("company_certifications", "legal_representative", existing_type=sa.String(length=50), nullable=True)
    op.alter_column("company_certifications", "registered_address", existing_type=sa.String(length=300), nullable=True)
    op.create_index("idx_company_certifications_method", "company_certifications", ["verification_method"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_company_certifications_method", table_name="company_certifications")
    op.alter_column("company_certifications", "registered_address", existing_type=sa.String(length=300), nullable=False)
    op.alter_column("company_certifications", "legal_representative", existing_type=sa.String(length=50), nullable=False)
    op.alter_column("company_certifications", "unified_social_credit_code", existing_type=sa.String(length=18), nullable=False)

    op.drop_column("company_certifications", "verification_note")
    op.drop_column("company_certifications", "applicant_phone")
    op.drop_column("company_certifications", "applicant_title")
    op.drop_column("company_certifications", "applicant_name")
    op.drop_column("company_certifications", "work_email")
    op.drop_column("company_certifications", "proof_file_name")
    op.drop_column("company_certifications", "proof_file_url")
    op.drop_column("company_certifications", "verification_method")
