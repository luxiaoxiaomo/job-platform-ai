"""
Admin base data API.
"""
from fastapi import APIRouter, Depends, Query, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_role
from app.db.session import get_db
from app.modules.base_data.schemas import (
    BaseDataOperationLogListResponse,
    StandardPositionCreate,
    StandardPositionListResponse,
    StandardPositionResponse,
    StandardPositionUpdate,
    TagLibraryItemCreate,
    TagLibraryItemListResponse,
    TagLibraryItemResponse,
    TagLibraryItemUpdate,
)
from app.modules.base_data.service import BaseDataService
from app.modules.user.models import User

router = APIRouter()


@router.get("/standard-positions/public", response_model=StandardPositionListResponse)
async def list_public_standard_positions(
    q: str | None = Query(default=None),
    category: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List active standard positions for business pages."""
    return await BaseDataService.list_standard_positions(
        db,
        q=q,
        category=category,
        status_="active",
        skip=skip,
        limit=limit,
    )


@router.get("/standard-positions", response_model=StandardPositionListResponse)
async def list_standard_positions(
    q: str | None = Query(default=None),
    category: str | None = Query(default=None),
    status: str | None = Query(default=None, pattern="^(active|inactive)$"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """List standard position library entries."""
    return await BaseDataService.list_standard_positions(
        db,
        q=q,
        category=category,
        status_=status,
        skip=skip,
        limit=limit,
    )


@router.get("/standard-positions/{position_id}", response_model=StandardPositionResponse)
async def get_standard_position(
    position_id: int,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Get one standard position library entry."""
    return await BaseDataService.get_standard_position(db, position_id)


@router.post(
    "/standard-positions",
    response_model=StandardPositionResponse,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_standard_position(
    data: StandardPositionCreate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Create a standard position library entry."""
    return await BaseDataService.create_standard_position(db, current_user, data)


@router.put("/standard-positions/{position_id}", response_model=StandardPositionResponse)
async def update_standard_position(
    position_id: int,
    data: StandardPositionUpdate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Update or deactivate a standard position library entry."""
    return await BaseDataService.update_standard_position(db, current_user, position_id, data)


@router.get("/operation-logs", response_model=BaseDataOperationLogListResponse)
async def list_operation_logs(
    resource_type: str | None = Query(default=None),
    resource_id: int | None = Query(default=None, ge=1),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """List base data operation logs."""
    return await BaseDataService.list_operation_logs(
        db,
        resource_type=resource_type,
        resource_id=resource_id,
        skip=skip,
        limit=limit,
    )


@router.get("/tags", response_model=TagLibraryItemListResponse)
async def list_tags(
    q: str | None = Query(default=None),
    category: str | None = Query(default=None),
    status: str | None = Query(default=None, pattern="^(active|inactive)$"),
    parent_id: int | None = Query(default=None, ge=1),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """List tag library entries."""
    return await BaseDataService.list_tags(
        db,
        q=q,
        category=category,
        status_=status,
        parent_id=parent_id,
        skip=skip,
        limit=limit,
    )


@router.get("/tags/public", response_model=TagLibraryItemListResponse)
async def list_public_tags(
    q: str | None = Query(default=None),
    category: str | None = Query(default=None),
    parent_id: int | None = Query(default=None, ge=1),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List active tag library entries for business pages."""
    return await BaseDataService.list_tags(
        db,
        q=q,
        category=category,
        status_="active",
        parent_id=parent_id,
        skip=skip,
        limit=limit,
    )


@router.get("/tags/{tag_id}", response_model=TagLibraryItemResponse)
async def get_tag(
    tag_id: int,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Get one tag library entry."""
    return await BaseDataService.get_tag(db, tag_id)


@router.post("/tags", response_model=TagLibraryItemResponse, status_code=http_status.HTTP_201_CREATED)
async def create_tag(
    data: TagLibraryItemCreate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Create a tag library entry."""
    return await BaseDataService.create_tag(db, current_user, data)


@router.put("/tags/{tag_id}", response_model=TagLibraryItemResponse)
async def update_tag(
    tag_id: int,
    data: TagLibraryItemUpdate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Update or deactivate a tag library entry."""
    return await BaseDataService.update_tag(db, current_user, tag_id, data)
