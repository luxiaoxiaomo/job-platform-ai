"""Search API."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_role
from app.db.session import get_db
from app.modules.search.schemas import SearchJobResponse, SearchResumeResponse
from app.modules.search.service import SearchService
from app.modules.user.models import User

router = APIRouter()


@router.get("/jobs", response_model=SearchJobResponse)
async def search_jobs(
    q: str = Query(..., min_length=1, max_length=120),
    tag_id: int | None = Query(None, ge=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """Search active jobs with a deterministic semantic fallback."""
    return await SearchService.search_jobs(db, current_user, query=q.strip(), tag_id=tag_id, skip=skip, limit=limit)


@router.get("/resumes", response_model=SearchResumeResponse)
async def search_resumes(
    q: str = Query(..., min_length=1, max_length=120),
    tag_id: int | None = Query(None, ge=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(require_role("recruiter")),
    db: AsyncSession = Depends(get_db),
):
    """Search seeker resumes with a deterministic semantic fallback."""
    return await SearchService.search_resumes(db, current_user, query=q.strip(), tag_id=tag_id, skip=skip, limit=limit)
