"""
Schemas for admin-managed base data.
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


PositionStatus = Literal["active", "inactive"]
TagStatus = Literal["active", "inactive"]


def normalize_aliases(value: list[str] | None) -> list[str]:
    if not value:
        return []
    cleaned: list[str] = []
    for item in value:
        alias = item.strip() if isinstance(item, str) else ""
        if alias and alias not in cleaned:
            cleaned.append(alias[:50])
    return cleaned[:20]


def normalize_id_list(value: list[int] | None) -> list[int]:
    """Normalize optional ID list while preserving user order."""
    if not value:
        return []
    cleaned: list[int] = []
    for item in value:
        if item and item not in cleaned:
            cleaned.append(int(item))
    return cleaned[:20]


class TagReference(BaseModel):
    """Stable snapshot for a linked tag library item."""

    id: int
    name: str
    category: str
    color: str | None = None


class StandardPositionCreate(BaseModel):
    """Create one standard position."""

    name: str = Field(..., min_length=2, max_length=100)
    category: str = Field(..., min_length=1, max_length=80)
    aliases: list[str] = Field(default_factory=list)
    description: str | None = Field(None, max_length=2000)
    status: PositionStatus = "active"

    @field_validator("name", "category", "description", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("aliases")
    @classmethod
    def clean_aliases(cls, value: list[str] | None) -> list[str]:
        return normalize_aliases(value)


class StandardPositionUpdate(BaseModel):
    """Update one standard position."""

    name: str | None = Field(None, min_length=2, max_length=100)
    category: str | None = Field(None, min_length=1, max_length=80)
    aliases: list[str] | None = None
    description: str | None = Field(None, max_length=2000)
    status: PositionStatus | None = None

    @field_validator("name", "category", "description", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("aliases")
    @classmethod
    def clean_aliases(cls, value: list[str] | None) -> list[str] | None:
        return None if value is None else normalize_aliases(value)


class StandardPositionResponse(BaseModel):
    """Standard position response."""

    id: int
    name: str
    category: str
    aliases: list[str] = Field(default_factory=list)
    description: str | None = None
    status: PositionStatus
    created_by: int | None = None
    updated_by: int | None = None
    created_at: datetime
    updated_at: datetime


class StandardPositionListResponse(BaseModel):
    """Paginated standard position list."""

    items: list[StandardPositionResponse] = Field(default_factory=list)
    total: int
    skip: int = 0
    limit: int = 20


class TagLibraryItemCreate(BaseModel):
    """Create one tag library item."""

    name: str = Field(..., min_length=1, max_length=80)
    category: str = Field(..., min_length=1, max_length=80)
    parent_id: int | None = Field(None, ge=1)
    color: str | None = Field(None, max_length=20)
    description: str | None = Field(None, max_length=1000)
    sort_order: int = Field(0, ge=0, le=9999)
    status: TagStatus = "active"

    @field_validator("name", "category", "color", "description", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class TagLibraryItemUpdate(BaseModel):
    """Update one tag library item."""

    name: str | None = Field(None, min_length=1, max_length=80)
    category: str | None = Field(None, min_length=1, max_length=80)
    parent_id: int | None = Field(None, ge=1)
    color: str | None = Field(None, max_length=20)
    description: str | None = Field(None, max_length=1000)
    sort_order: int | None = Field(None, ge=0, le=9999)
    status: TagStatus | None = None

    @field_validator("name", "category", "color", "description", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class TagLibraryItemResponse(BaseModel):
    """Tag library item response."""

    id: int
    name: str
    category: str
    parent_id: int | None = None
    color: str | None = None
    description: str | None = None
    sort_order: int
    status: TagStatus
    created_by: int | None = None
    updated_by: int | None = None
    created_at: datetime
    updated_at: datetime


class TagLibraryItemListResponse(BaseModel):
    """Paginated tag library item list."""

    items: list[TagLibraryItemResponse] = Field(default_factory=list)
    total: int
    skip: int = 0
    limit: int = 20


class BaseDataOperationLogResponse(BaseModel):
    """Base data operation log response."""

    id: int
    resource_type: str
    resource_id: int
    action: str
    actor_id: int | None = None
    before: dict | None = None
    after: dict | None = None
    created_at: datetime


class BaseDataOperationLogListResponse(BaseModel):
    """Paginated base data operation logs."""

    items: list[BaseDataOperationLogResponse] = Field(default_factory=list)
    total: int
    skip: int = 0
    limit: int = 20
