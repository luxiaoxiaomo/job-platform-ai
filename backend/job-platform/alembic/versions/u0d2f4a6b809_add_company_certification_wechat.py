"""add company certification wechat

Revision ID: u0d2f4a6b809
Revises: t9c1e2f3a708
Create Date: 2026-06-19 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "u0d2f4a6b809"
down_revision: Union[str, None] = "t9c1e2f3a708"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "company_certifications",
        sa.Column("applicant_wechat", sa.String(length=80), nullable=True, comment="Applicant WeChat ID"),
    )


def downgrade() -> None:
    op.drop_column("company_certifications", "applicant_wechat")
