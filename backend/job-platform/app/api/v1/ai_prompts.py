"""
AI prompt configuration API.
"""
from fastapi import APIRouter, Depends, Query, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_role
from app.db.session import get_db
from app.modules.ai_prompt.schemas import (
    AiPromptConfigCreate,
    AiPromptConfigListResponse,
    AiPromptConfigResponse,
    JobPreReviewRequest,
    JobPreReviewResponse,
    PromptTestRequest,
)
from app.modules.ai_prompt.service import AiPromptService, JOB_CONTENT_REVIEW_SCENARIO
from app.modules.user.models import User

router = APIRouter()


@router.get("", response_model=AiPromptConfigListResponse)
async def list_prompt_configs(
    scenario_key: str = Query(JOB_CONTENT_REVIEW_SCENARIO),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """List prompt configs for a scenario."""
    return await AiPromptService.list_configs(db, scenario_key)


@router.get("/active", response_model=AiPromptConfigResponse)
async def get_active_prompt_config(
    scenario_key: str = Query(JOB_CONTENT_REVIEW_SCENARIO),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Get active prompt config for a scenario."""
    return await AiPromptService.get_active(db, scenario_key)


@router.post("", response_model=AiPromptConfigResponse, status_code=http_status.HTTP_201_CREATED)
async def create_prompt_config(
    data: AiPromptConfigCreate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new prompt config draft version."""
    return await AiPromptService.create_config(db, current_user, data)


@router.post("/{config_id}/publish", response_model=AiPromptConfigResponse)
async def publish_prompt_config(
    config_id: int,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Publish one prompt version and deactivate previous versions for the same scenario."""
    return await AiPromptService.publish_config(db, current_user, config_id)


@router.post("/test", response_model=JobPreReviewResponse)
async def test_prompt_config(
    data: PromptTestRequest,
    current_user: User = Depends(require_role("admin")),
):
    """Run prompt test against a sample job. Local rules are used until model execution is wired."""
    return await AiPromptService.test_prompt(data)


@router.post("/job-content-review", response_model=JobPreReviewResponse)
async def pre_review_job_content(
    data: JobPreReviewRequest,
    current_user: User = Depends(require_role("recruiter", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """Run job content pre-review using the active prompt configuration."""
    return await AiPromptService.pre_review_job(db, data)
