"""add resume basic info age

Revision ID: k9f1a2b3c401
Revises: j8e4f6a7b801
Create Date: 2026-06-16 14:35:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "k9f1a2b3c401"
down_revision: Union[str, None] = "j8e4f6a7b801"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("resume_basic_infos", sa.Column("age", sa.Integer(), nullable=True))
    op.create_index("idx_resume_basic_infos_age", "resume_basic_infos", ["age"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_resume_basic_infos_age", table_name="resume_basic_infos")
    op.drop_column("resume_basic_infos", "age")
