"""add business tag refs

Revision ID: y4h6i8j0k124
Revises: x3g5h7i9j013
Create Date: 2026-06-20 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "y4h6i8j0k124"
down_revision: Union[str, None] = "x3g5h7i9j013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json_type():
    return sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column("tag_refs", _json_type(), nullable=True, comment="Linked tag library snapshots"),
    )
    op.add_column(
        "seeker_profiles",
        sa.Column("tag_refs", _json_type(), nullable=True, comment="Linked tag library snapshots"),
    )


def downgrade() -> None:
    op.drop_column("seeker_profiles", "tag_refs")
    op.drop_column("jobs", "tag_refs")
