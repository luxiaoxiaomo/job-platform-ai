"""
Rule-based job matching API.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_role
from app.db.session import get_db
from app.modules.match.config import MatchRuleConfigService
from app.modules.match.schemas import (
    JobMatchResponse,
    MatchQualityDashboardResponse,
    MatchRuleAuditListResponse,
    MatchRuleAuditResponse,
    MatchRuleConfigCompareResponse,
    MatchRuleConfigListResponse,
    MatchRuleConfigResponse,
    MatchRuleConfigVersionCreateRequest,
    MatchRuleConfigVersionCreateResponse,
    MatchRuleExperimentCreateRequest,
    MatchRuleExperimentEffectResponse,
    MatchRuleExperimentListResponse,
    MatchRuleExperimentResponse,
    MatchRuleExperimentStatusUpdateRequest,
    MatchRuleExperimentStatusUpdateResponse,
    MatchRuleOperationAuditListResponse,
    MatchRulePublishRequest,
    MatchRulePublishResponse,
    MatchRuleReleaseCheckResponse,
    MatchRuleRollbackRequest,
    MatchRuleTemplateCreateRequest,
)
from app.modules.match.service import MatchService
from app.modules.match.writes import MatchRuleWriteService
from app.modules.user.models import User

router = APIRouter()


@router.get("/rule-configs", response_model=MatchRuleConfigListResponse)
async def list_match_rule_configs(
    scope: str | None = Query(default=None),
    template_key: str | None = Query(default=None),
    job_id: int | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """List match rule configs for admin read-only pages."""
    return await MatchService.list_rule_configs(
        db,
        scope=scope,
        template_key=template_key,
        job_id=job_id,
        skip=skip,
        limit=limit,
    )


@router.get("/rule-configs/default", response_model=MatchRuleConfigResponse)
async def get_default_match_rule_config(
    current_user: User = Depends(require_role("seeker", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """Get the default rule config used by rule-based matching."""
    return await MatchService.get_default_rule_config_from_db(db)


@router.post("/rule-configs/templates", response_model=MatchRuleConfigVersionCreateResponse)
async def create_match_rule_template(
    payload: MatchRuleTemplateCreateRequest,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Create the first version for a new rule template."""
    config = await MatchRuleWriteService.create_template(db, current_user, payload)
    return MatchRuleConfigVersionCreateResponse(
        message="rule_config_template_created",
        config=MatchService._rule_config_response(MatchRuleConfigService.from_model(config)),
    )


@router.get("/rule-configs/{config_id}", response_model=MatchRuleConfigResponse)
async def get_match_rule_config(
    config_id: int,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Get one match rule config for admin read-only detail page."""
    return await MatchService.get_rule_config(db, config_id)


@router.get("/rule-configs/{config_id}/release-check", response_model=MatchRuleReleaseCheckResponse)
async def check_match_rule_config_release(
    config_id: int,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Run publish pre-checks for one match rule config."""
    return await MatchRuleWriteService.release_check(db, config_id)


@router.post("/rule-configs/{config_id}/publish", response_model=MatchRulePublishResponse)
async def publish_match_rule_config(
    config_id: int,
    payload: MatchRulePublishRequest,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Publish one draft/testing match rule config as active."""
    return await MatchRuleWriteService.publish_rule_config(db, current_user, config_id, payload)


@router.get("/rule-configs/{config_id}/history", response_model=MatchRuleConfigListResponse)
async def get_match_rule_config_history(
    config_id: int,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Get match rule config history for future history pages."""
    return await MatchService.get_rule_config_history(db, config_id)


@router.get("/rule-configs/{config_id}/compare/{target_config_id}", response_model=MatchRuleConfigCompareResponse)
async def compare_match_rule_configs(
    config_id: int,
    target_config_id: int,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Compare two rule config versions."""
    return await MatchService.compare_rule_configs(db, config_id, target_config_id)


@router.post("/rule-configs/{config_id}/versions", response_model=MatchRuleConfigVersionCreateResponse)
async def create_match_rule_config_version(
    config_id: int,
    payload: MatchRuleConfigVersionCreateRequest,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new version from an existing rule config."""
    config = await MatchRuleWriteService.create_version(db, current_user, config_id, payload)
    return MatchRuleConfigVersionCreateResponse(
        config=MatchService._rule_config_response(MatchRuleConfigService.from_model(config))
    )


@router.post("/rule-configs/{config_id}/rollback", response_model=MatchRuleConfigVersionCreateResponse)
async def rollback_match_rule_config_version(
    config_id: int,
    payload: MatchRuleRollbackRequest,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new version by copying a historical rule config."""
    config = await MatchRuleWriteService.rollback_version(db, current_user, config_id, payload)
    return MatchRuleConfigVersionCreateResponse(
        message="rule_config_version_rolled_back",
        config=MatchService._rule_config_response(MatchRuleConfigService.from_model(config)),
    )


@router.get("/rule-experiments", response_model=MatchRuleExperimentListResponse)
async def list_match_rule_experiments(
    scope: str | None = Query(default=None),
    template_key: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """List gray/AB test entries for rule versions."""
    return await MatchService.list_rule_experiments(
        db,
        scope=scope,
        template_key=template_key,
        skip=skip,
        limit=limit,
    )


@router.get("/rule-experiments/{experiment_id}/effects", response_model=MatchRuleExperimentEffectResponse)
async def get_match_rule_experiment_effects(
    experiment_id: int,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated match effects for one rule experiment."""
    return await MatchService.get_rule_experiment_effects(db, experiment_id)


@router.post("/rule-experiments", response_model=MatchRuleExperimentResponse)
async def create_match_rule_experiment(
    payload: MatchRuleExperimentCreateRequest,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Create a gray/AB test entry for rule versions."""
    experiment = await MatchRuleWriteService.create_experiment(db, current_user, payload)
    return MatchService._experiment_response(experiment)


@router.post("/rule-experiments/{experiment_id}/status", response_model=MatchRuleExperimentStatusUpdateResponse)
async def update_match_rule_experiment_status(
    experiment_id: int,
    payload: MatchRuleExperimentStatusUpdateRequest,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Pause, resume, start, or end one rule experiment."""
    return await MatchRuleWriteService.update_experiment_status(db, current_user, experiment_id, payload)


@router.get("/rule-operation-audits", response_model=MatchRuleOperationAuditListResponse)
async def list_match_rule_operation_audits(
    resource_type: str | None = Query(default=None),
    resource_id: int | None = Query(default=None),
    action: str | None = Query(default=None),
    actor_id: int | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """List admin operation audits for rule releases and experiments."""
    return await MatchService.list_rule_operation_audits(
        db,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        actor_id=actor_id,
        skip=skip,
        limit=limit,
    )


@router.get("/quality/summary", response_model=MatchQualityDashboardResponse)
async def get_match_quality_summary(
    experiment_id: int | None = Query(default=None),
    rule_config_id: int | None = Query(default=None),
    scope: str | None = Query(default=None),
    template_key: str | None = Query(default=None),
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    city: str | None = Query(default=None),
    position_category: str | None = Query(default=None),
    standard_position_id: int | None = Query(default=None),
    job_tag: str | None = Query(default=None),
    segment_type: str | None = Query(default=None),
    include_insights: bool = Query(default=True),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Get match quality and downstream behavior metrics for admin operations."""
    return await MatchService.get_match_quality_summary(
        db,
        experiment_id=experiment_id,
        rule_config_id=rule_config_id,
        scope=scope,
        template_key=template_key,
        created_from=created_from,
        created_to=created_to,
        city=city,
        position_category=position_category,
        standard_position_id=standard_position_id,
        job_tag=job_tag,
        segment_type=segment_type,
        include_insights=include_insights,
    )


@router.get("/audits", response_model=MatchRuleAuditListResponse)
async def list_match_rule_audits(
    experiment_id: int | None = Query(default=None),
    rule_config_id: int | None = Query(default=None),
    job_id: int | None = Query(default=None),
    seeker_id: int | None = Query(default=None),
    experiment_bucket: str | None = Query(default=None, pattern="^(control|treatment)$"),
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """List persisted rule match audit records."""
    return await MatchService.list_match_audits(
        db,
        experiment_id=experiment_id,
        rule_config_id=rule_config_id,
        job_id=job_id,
        seeker_id=seeker_id,
        experiment_bucket=experiment_bucket,
        created_from=created_from,
        created_to=created_to,
        skip=skip,
        limit=limit,
    )


@router.get("/audits/{audit_id}", response_model=MatchRuleAuditResponse)
async def get_match_rule_audit(
    audit_id: int,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Get one persisted rule match audit with traceable snapshots."""
    return await MatchService.get_match_audit(db, audit_id)


@router.get("/jobs/{job_id}/me", response_model=JobMatchResponse)
async def get_my_job_match(
    job_id: int,
    current_user: User = Depends(require_role("seeker")),
    db: AsyncSession = Depends(get_db),
):
    """Get current seeker's rule-based match analysis for one active job."""
    return await MatchService.get_my_job_match(db, current_user, job_id)


@router.get("/applications/{application_id}", response_model=JobMatchResponse)
async def get_recruiter_application_match(
    application_id: int,
    current_user: User = Depends(require_role("recruiter")),
    db: AsyncSession = Depends(get_db),
):
    """Get recruiter-side rule-based match analysis for one received application."""
    return await MatchService.get_recruiter_application_match(db, current_user, application_id)
