"""add_company_certifications

Revision ID: 9f3d9e82a701
Revises: 421bc078883c
Create Date: 2026-06-07 11:45:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9f3d9e82a701"
down_revision = "421bc078883c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "company_certifications",
        sa.Column("id", sa.Integer(), nullable=False, comment="认证ID"),
        sa.Column("recruiter_id", sa.Integer(), nullable=False, comment="招聘者用户ID"),
        sa.Column("company_name", sa.String(length=100), nullable=False, comment="企业名称"),
        sa.Column("unified_social_credit_code", sa.String(length=18), nullable=False, comment="统一社会信用代码"),
        sa.Column("legal_representative", sa.String(length=50), nullable=False, comment="法定代表人"),
        sa.Column("registered_address", sa.String(length=300), nullable=False, comment="注册地址"),
        sa.Column("license_file_url", sa.String(length=500), nullable=True, comment="营业执照文件URL"),
        sa.Column("license_file_name", sa.String(length=200), nullable=True, comment="营业执照文件名"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending", comment="状态：pending/approved/rejected"),
        sa.Column("reject_reason", sa.Text(), nullable=True, comment="驳回原因"),
        sa.Column("reviewer_id", sa.Integer(), nullable=True, comment="审核人ID"),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True, comment="审核时间"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.ForeignKeyConstraint(["recruiter_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("recruiter_id", name="uq_company_certifications_recruiter_id"),
    )
    op.create_index("idx_company_certifications_recruiter_id", "company_certifications", ["recruiter_id"], unique=False)
    op.create_index("idx_company_certifications_status", "company_certifications", ["status"], unique=False)
    op.create_index("idx_company_certifications_credit_code", "company_certifications", ["unified_social_credit_code"], unique=False)
    op.create_index(op.f("ix_company_certifications_id"), "company_certifications", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_company_certifications_id"), table_name="company_certifications")
    op.drop_index("idx_company_certifications_credit_code", table_name="company_certifications")
    op.drop_index("idx_company_certifications_status", table_name="company_certifications")
    op.drop_index("idx_company_certifications_recruiter_id", table_name="company_certifications")
    op.drop_table("company_certifications")
