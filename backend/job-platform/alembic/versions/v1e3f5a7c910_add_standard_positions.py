"""add standard positions

Revision ID: v1e3f5a7c910
Revises: u0d2f4a6b809
Create Date: 2026-06-19 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "v1e3f5a7c910"
down_revision: Union[str, None] = "u0d2f4a6b809"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    json_type = postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")

    op.create_table(
        "standard_positions",
        sa.Column("id", sa.Integer(), nullable=False, comment="Standard position ID"),
        sa.Column("name", sa.String(length=100), nullable=False, comment="Standard position name"),
        sa.Column("category", sa.String(length=80), nullable=False, comment="Position category"),
        sa.Column("aliases", json_type, nullable=True, comment="Alternative titles"),
        sa.Column("description", sa.Text(), nullable=True, comment="Position description"),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False, comment="active/inactive"),
        sa.Column("created_by", sa.Integer(), nullable=True, comment="Creator user ID"),
        sa.Column("updated_by", sa.Integer(), nullable=True, comment="Updater user ID"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False, comment="Created at"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False, comment="Updated at"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_standard_positions_name"),
    )
    op.create_index(op.f("ix_standard_positions_id"), "standard_positions", ["id"], unique=False)
    op.create_index("idx_standard_positions_category_status", "standard_positions", ["category", "status"], unique=False)
    op.create_index("idx_standard_positions_status", "standard_positions", ["status"], unique=False)

    op.create_table(
        "base_data_operation_logs",
        sa.Column("id", sa.Integer(), nullable=False, comment="Operation log ID"),
        sa.Column("resource_type", sa.String(length=50), nullable=False, comment="Resource type"),
        sa.Column("resource_id", sa.Integer(), nullable=False, comment="Resource ID"),
        sa.Column("action", sa.String(length=30), nullable=False, comment="create/update/deactivate"),
        sa.Column("actor_id", sa.Integer(), nullable=True, comment="Actor user ID"),
        sa.Column("before", json_type, nullable=True, comment="Snapshot before operation"),
        sa.Column("after", json_type, nullable=True, comment="Snapshot after operation"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False, comment="Created at"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_base_data_operation_logs_id"), "base_data_operation_logs", ["id"], unique=False)
    op.create_index("idx_base_data_logs_actor_created", "base_data_operation_logs", ["actor_id", "created_at"], unique=False)
    op.create_index("idx_base_data_logs_created", "base_data_operation_logs", ["created_at"], unique=False)
    op.create_index("idx_base_data_logs_resource", "base_data_operation_logs", ["resource_type", "resource_id"], unique=False)

    op.create_table(
        "tag_library_items",
        sa.Column("id", sa.Integer(), nullable=False, comment="Tag ID"),
        sa.Column("name", sa.String(length=80), nullable=False, comment="Tag name"),
        sa.Column("category", sa.String(length=80), nullable=False, comment="Tag category"),
        sa.Column("parent_id", sa.Integer(), nullable=True, comment="Parent tag ID"),
        sa.Column("color", sa.String(length=20), nullable=True, comment="Display color"),
        sa.Column("description", sa.Text(), nullable=True, comment="Tag description"),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False, comment="Sort order"),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False, comment="active/inactive"),
        sa.Column("created_by", sa.Integer(), nullable=True, comment="Creator user ID"),
        sa.Column("updated_by", sa.Integer(), nullable=True, comment="Updater user ID"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False, comment="Created at"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False, comment="Updated at"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["parent_id"], ["tag_library_items.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category", "name", name="uq_tag_library_items_category_name"),
    )
    op.create_index(op.f("ix_tag_library_items_id"), "tag_library_items", ["id"], unique=False)
    op.create_index("idx_tag_library_items_category_status", "tag_library_items", ["category", "status"], unique=False)
    op.create_index("idx_tag_library_items_parent", "tag_library_items", ["parent_id"], unique=False)
    op.create_index("idx_tag_library_items_status", "tag_library_items", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_tag_library_items_status", table_name="tag_library_items")
    op.drop_index("idx_tag_library_items_parent", table_name="tag_library_items")
    op.drop_index("idx_tag_library_items_category_status", table_name="tag_library_items")
    op.drop_index(op.f("ix_tag_library_items_id"), table_name="tag_library_items")
    op.drop_table("tag_library_items")

    op.drop_index("idx_base_data_logs_resource", table_name="base_data_operation_logs")
    op.drop_index("idx_base_data_logs_created", table_name="base_data_operation_logs")
    op.drop_index("idx_base_data_logs_actor_created", table_name="base_data_operation_logs")
    op.drop_index(op.f("ix_base_data_operation_logs_id"), table_name="base_data_operation_logs")
    op.drop_table("base_data_operation_logs")

    op.drop_index("idx_standard_positions_status", table_name="standard_positions")
    op.drop_index("idx_standard_positions_category_status", table_name="standard_positions")
    op.drop_index(op.f("ix_standard_positions_id"), table_name="standard_positions")
    op.drop_table("standard_positions")
