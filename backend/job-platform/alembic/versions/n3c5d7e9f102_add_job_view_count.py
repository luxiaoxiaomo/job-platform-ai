"""add job view count

Revision ID: n3c5d7e9f102
Revises: m2b4c6d8e901
Create Date: 2026-06-18 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "n3c5d7e9f102"
down_revision: Union[str, None] = "m2b4c6d8e901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column(
            "view_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
            comment="Public detail view count",
        ),
    )


def downgrade() -> None:
    op.drop_column("jobs", "view_count")
