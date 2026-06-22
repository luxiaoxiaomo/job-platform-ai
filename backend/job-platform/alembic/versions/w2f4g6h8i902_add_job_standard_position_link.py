"""add job standard position link

Revision ID: w2f4g6h8i902
Revises: v1e3f5a7c910
Create Date: 2026-06-20 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "w2f4g6h8i902"
down_revision: Union[str, None] = "v1e3f5a7c910"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column("standard_position_id", sa.Integer(), nullable=True, comment="Linked standard position ID"),
    )
    op.create_foreign_key(
        "fk_jobs_standard_position_id_standard_positions",
        "jobs",
        "standard_positions",
        ["standard_position_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("idx_jobs_standard_position_id", "jobs", ["standard_position_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_jobs_standard_position_id", table_name="jobs")
    op.drop_constraint("fk_jobs_standard_position_id_standard_positions", "jobs", type_="foreignkey")
    op.drop_column("jobs", "standard_position_id")
