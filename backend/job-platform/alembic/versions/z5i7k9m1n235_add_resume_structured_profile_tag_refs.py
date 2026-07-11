"""add resume structured profile tag refs

Revision ID: z5i7k9m1n235
Revises: y4h6i8j0k124
Create Date: 2026-06-20 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "z5i7k9m1n235"
down_revision: Union[str, None] = "y4h6i8j0k124"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json_type():
    return sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.add_column(
        "resume_structured_profiles",
        sa.Column("tag_refs", _json_type(), nullable=True, comment="Linked tag library snapshots"),
    )


def downgrade() -> None:
    op.drop_column("resume_structured_profiles", "tag_refs")
