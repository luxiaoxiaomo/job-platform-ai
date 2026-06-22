"""
Base data models for admin-managed dictionaries.
"""
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class StandardPosition(Base):
    """Admin-managed standard position library item."""

    __tablename__ = "standard_positions"

    id = Column(Integer, primary_key=True, index=True, comment="Standard position ID")
    name = Column(String(100), nullable=False, comment="Standard position name")
    category = Column(String(80), nullable=False, comment="Position category")
    aliases = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True, comment="Alternative titles")
    description = Column(Text, nullable=True, comment="Position description")
    status = Column(String(20), nullable=False, default="active", server_default="active", comment="active/inactive")
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="Creator user ID")
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="Updater user ID")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="Created at")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="Updated at")

    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

    __table_args__ = (
        UniqueConstraint("name", name="uq_standard_positions_name"),
        Index("idx_standard_positions_category_status", "category", "status"),
        Index("idx_standard_positions_status", "status"),
    )


class TagLibraryItem(Base):
    """Admin-managed tag library item with optional hierarchy."""

    __tablename__ = "tag_library_items"

    id = Column(Integer, primary_key=True, index=True, comment="Tag ID")
    name = Column(String(80), nullable=False, comment="Tag name")
    category = Column(String(80), nullable=False, comment="Tag category")
    parent_id = Column(Integer, ForeignKey("tag_library_items.id", ondelete="SET NULL"), nullable=True, comment="Parent tag ID")
    color = Column(String(20), nullable=True, comment="Display color")
    description = Column(Text, nullable=True, comment="Tag description")
    sort_order = Column(Integer, nullable=False, default=0, server_default="0", comment="Sort order")
    status = Column(String(20), nullable=False, default="active", server_default="active", comment="active/inactive")
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="Creator user ID")
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="Updater user ID")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="Created at")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="Updated at")

    parent = relationship("TagLibraryItem", remote_side=[id])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

    __table_args__ = (
        UniqueConstraint("category", "name", name="uq_tag_library_items_category_name"),
        Index("idx_tag_library_items_category_status", "category", "status"),
        Index("idx_tag_library_items_parent", "parent_id"),
        Index("idx_tag_library_items_status", "status"),
    )


class BaseDataOperationLog(Base):
    """Audit log for base data changes."""

    __tablename__ = "base_data_operation_logs"

    id = Column(Integer, primary_key=True, index=True, comment="Operation log ID")
    resource_type = Column(String(50), nullable=False, comment="Resource type")
    resource_id = Column(Integer, nullable=False, comment="Resource ID")
    action = Column(String(30), nullable=False, comment="create/update/deactivate")
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="Actor user ID")
    before = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True, comment="Snapshot before operation")
    after = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True, comment="Snapshot after operation")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="Created at")

    actor = relationship("User")

    __table_args__ = (
        Index("idx_base_data_logs_resource", "resource_type", "resource_id"),
        Index("idx_base_data_logs_actor_created", "actor_id", "created_at"),
        Index("idx_base_data_logs_created", "created_at"),
    )
