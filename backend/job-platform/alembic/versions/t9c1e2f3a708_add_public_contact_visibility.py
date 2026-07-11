"""add public contact visibility

Revision ID: t9c1e2f3a708
Revises: s8b0d3e4f607
Create Date: 2026-06-19 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "t9c1e2f3a708"
down_revision: Union[str, None] = "s8b0d3e4f607"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column("company_display_mode", sa.String(length=20), nullable=False, server_default="display_name", comment="display_name/company_name/anonymous"),
    )
    op.add_column(
        "jobs",
        sa.Column("contact_phone_public", sa.Boolean(), nullable=False, server_default=sa.false(), comment="Whether recruiter phone is visible"),
    )
    op.add_column(
        "jobs",
        sa.Column("contact_email_public", sa.Boolean(), nullable=False, server_default=sa.false(), comment="Whether recruiter email is visible"),
    )
    op.add_column(
        "jobs",
        sa.Column("contact_wechat_public", sa.Boolean(), nullable=False, server_default=sa.false(), comment="Whether recruiter WeChat is visible"),
    )

    op.add_column("seeker_profiles", sa.Column("email", sa.String(length=120), nullable=True, comment="Contact email"))
    op.add_column("seeker_profiles", sa.Column("wechat", sa.String(length=80), nullable=True, comment="WeChat ID"))
    op.add_column(
        "seeker_profiles",
        sa.Column("email_public", sa.Boolean(), nullable=False, server_default=sa.false(), comment="Email visible to recruiters"),
    )
    op.add_column(
        "seeker_profiles",
        sa.Column("wechat_public", sa.Boolean(), nullable=False, server_default=sa.false(), comment="WeChat visible to recruiters"),
    )


def downgrade() -> None:
    op.drop_column("seeker_profiles", "wechat_public")
    op.drop_column("seeker_profiles", "email_public")
    op.drop_column("seeker_profiles", "wechat")
    op.drop_column("seeker_profiles", "email")

    op.drop_column("jobs", "contact_wechat_public")
    op.drop_column("jobs", "contact_email_public")
    op.drop_column("jobs", "contact_phone_public")
    op.drop_column("jobs", "company_display_mode")
