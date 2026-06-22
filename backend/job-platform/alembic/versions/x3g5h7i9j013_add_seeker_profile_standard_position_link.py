"""add seeker profile standard position link

Revision ID: x3g5h7i9j013
Revises: w2f4g6h8i902
Create Date: 2026-06-20 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "x3g5h7i9j013"
down_revision: Union[str, None] = "w2f4g6h8i902"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "seeker_profiles",
        sa.Column("standard_position_id", sa.Integer(), nullable=True, comment="Linked standard position ID"),
    )
    op.create_foreign_key(
        "fk_seeker_profiles_standard_position_id_standard_positions",
        "seeker_profiles",
        "standard_positions",
        ["standard_position_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("idx_seeker_profiles_standard_position_id", "seeker_profiles", ["standard_position_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_seeker_profiles_standard_position_id", table_name="seeker_profiles")
    op.drop_constraint(
        "fk_seeker_profiles_standard_position_id_standard_positions",
        "seeker_profiles",
        type_="foreignkey",
    )
    op.drop_column("seeker_profiles", "standard_position_id")
