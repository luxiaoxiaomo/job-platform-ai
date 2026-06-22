"""Helpers for linking business records to tag library items."""
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.base_data.repository import TagLibraryItemRepository


async def resolve_active_tag_refs(db: AsyncSession, tag_ids: list[int] | None) -> list[dict]:
    """Return ordered tag snapshots for active tag IDs."""
    if not tag_ids:
        return []
    unique_ids: list[int] = []
    for tag_id in tag_ids:
        if tag_id and tag_id not in unique_ids:
            unique_ids.append(int(tag_id))

    tags = await TagLibraryItemRepository.list_by_ids(db, unique_ids)
    by_id = {tag.id: tag for tag in tags}
    refs: list[dict] = []
    for tag_id in unique_ids:
        tag = by_id.get(tag_id)
        if tag is None or tag.status != "active":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
        refs.append(
            {
                "id": tag.id,
                "name": tag.name,
                "category": tag.category,
                "color": tag.color,
            }
        )
    return refs


def tag_ref_names(tag_refs: list[dict] | None) -> list[str]:
    """Extract display names from stored tag snapshots."""
    names: list[str] = []
    for item in tag_refs or []:
        name = str(item.get("name") or "").strip() if isinstance(item, dict) else ""
        if name and name not in names:
            names.append(name)
    return names
