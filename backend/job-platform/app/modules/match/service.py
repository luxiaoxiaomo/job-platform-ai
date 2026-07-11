"""
Rule-based seeker-job matching service.
"""

from datetime import datetime, timezone
import hashlib
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.job.models import Job
from app.modules.job.repository import JobRepository
from app.modules.match.baseline import BaselineMatchScorer
from app.modules.match.config import (
    DEFAULT_RULE_DIMENSIONS,
    MatchRuleConfig,
    MatchRuleConfigService,
)
from app.modules.match.models import (
    MatchRuleConfigModel,
    MatchRuleExperimentModel,
    MatchRuleMatchAuditModel,
    MatchRuleOperationAuditModel,
)
from app.modules.match.repository import MatchRuleConfigRepository
from app.modules.match.runtime import IntelligentMatchRuntime
from app.modules.match.schemas import (
    JobMatchResponse,
    MatchAuditExperimentSummaryResponse,
    MatchAuditJobSummaryResponse,
    MatchAuditRuleConfigSummaryResponse,
    MatchAuditSeekerSummaryResponse,
    MatchDimensionResponse,
    MatchJobSummaryResponse,
    MatchRuleConfigListResponse,
    MatchRuleConfigCompareResponse,
    MatchRuleConfigResponse,
    MatchRuleAuditListResponse,
    MatchRuleAuditResponse,
    MatchRuleDimensionDiffResponse,
    MatchRuleDimensionResponse,
    MatchRuleExperimentBucketEffectResponse,
    MatchRuleExperimentEffectResponse,
    MatchRuleExperimentListResponse,
    MatchRuleExperimentResponse,
    MatchRuleOperationAuditListResponse,
    MatchRuleOperationAuditResponse,
    MatchSourceResponse,
)
from app.modules.resume.repository import ResumeRepository
from app.modules.resume.service import ResumeService
from app.modules.user.models import User



class MatchService:
    """Rule-based matching use cases."""

    @staticmethod
    def get_default_rule_config() -> MatchRuleConfigResponse:
        """Return the current default rule config."""
        return MatchService._rule_config_response(
            MatchRuleConfigService.get_default_config()
        )

    @staticmethod
    async def list_rule_configs(
        db: AsyncSession,
        *,
        scope: str | None = None,
        template_key: str | None = None,
        job_id: int | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> MatchRuleConfigListResponse:
        """List persisted rule configs for admin read-only pages."""
        if job_id is not None and scope is None:
            scope = "global"
        await MatchService._ensure_default_rule_config(db)
        items, total = await MatchRuleConfigRepository.list_configs(
            db,
            scope=scope,
            template_key=template_key,
            skip=skip,
            limit=limit,
        )
        return MatchRuleConfigListResponse(
            items=[
                MatchService._rule_config_response(
                    MatchRuleConfigService.from_model(item)
                )
                for item in items
            ],
            total=total,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    async def get_rule_config(
        db: AsyncSession, config_id: int
    ) -> MatchRuleConfigResponse:
        """Get one persisted rule config."""
        await MatchService._ensure_default_rule_config(db)
        config = await MatchRuleConfigRepository.get_by_id(db, config_id)
        if config is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="match_rule_config_not_found",
            )
        return MatchService._rule_config_response(
            MatchRuleConfigService.from_model(config)
        )

    @staticmethod
    async def get_rule_config_history(
        db: AsyncSession, config_id: int
    ) -> MatchRuleConfigListResponse:
        """Get version history for one persisted rule config."""
        await MatchService._ensure_default_rule_config(db)
        config = await MatchRuleConfigRepository.get_by_id(db, config_id)
        if config is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="match_rule_config_not_found",
            )
        items = await MatchRuleConfigRepository.get_history(db, config)
        return MatchRuleConfigListResponse(
            items=[
                MatchService._rule_config_response(
                    MatchRuleConfigService.from_model(item)
                )
                for item in items
            ],
            total=len(items),
            skip=0,
            limit=len(items),
        )

    @staticmethod
    async def compare_rule_configs(
        db: AsyncSession,
        base_config_id: int,
        target_config_id: int,
    ) -> MatchRuleConfigCompareResponse:
        """Compare two persisted rule config versions dimension by dimension."""
        await MatchService._ensure_default_rule_config(db)
        base_model = await MatchRuleConfigRepository.get_by_id(db, base_config_id)
        target_model = await MatchRuleConfigRepository.get_by_id(db, target_config_id)
        if base_model is None or target_model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="match_rule_config_not_found",
            )

        base = MatchService._rule_config_response(
            MatchRuleConfigService.from_model(base_model)
        )
        target = MatchService._rule_config_response(
            MatchRuleConfigService.from_model(target_model)
        )
        base_dimensions = {item.key: item for item in base.dimensions}
        target_dimensions = {item.key: item for item in target.dimensions}
        diffs: list[MatchRuleDimensionDiffResponse] = []
        for key in sorted(base_dimensions.keys() | target_dimensions.keys()):
            base_dimension = base_dimensions.get(key)
            target_dimension = target_dimensions.get(key)
            label = (target_dimension or base_dimension).label
            if base_dimension is None:
                change_type = "added"
            elif target_dimension is None:
                change_type = "removed"
            else:
                changed = (
                    base_dimension.label != target_dimension.label
                    or base_dimension.configured_weight
                    != target_dimension.configured_weight
                    or base_dimension.enabled != target_dimension.enabled
                    or base_dimension.description != target_dimension.description
                    or base_dimension.scoring_method != target_dimension.scoring_method
                    or base_dimension.logic != target_dimension.logic
                )
                change_type = "changed" if changed else "unchanged"
            base_weight = base_dimension.configured_weight if base_dimension else None
            target_weight = (
                target_dimension.configured_weight if target_dimension else None
            )
            diffs.append(
                MatchRuleDimensionDiffResponse(
                    key=key,
                    label=label,
                    change_type=change_type,
                    base_weight=base_weight,
                    target_weight=target_weight,
                    weight_delta=(target_weight - base_weight)
                    if base_weight is not None and target_weight is not None
                    else None,
                    base_enabled=base_dimension.enabled if base_dimension else None,
                    target_enabled=target_dimension.enabled
                    if target_dimension
                    else None,
                    enabled_changed=bool(
                        base_dimension
                        and target_dimension
                        and base_dimension.enabled != target_dimension.enabled
                    ),
                    label_changed=bool(
                        base_dimension
                        and target_dimension
                        and base_dimension.label != target_dimension.label
                    ),
                    description_changed=bool(
                        base_dimension
                        and target_dimension
                        and base_dimension.description != target_dimension.description
                    ),
                    scoring_method_changed=bool(
                        base_dimension
                        and target_dimension
                        and base_dimension.scoring_method
                        != target_dimension.scoring_method
                    ),
                    logic_changed=bool(
                        base_dimension
                        and target_dimension
                        and base_dimension.logic != target_dimension.logic
                    ),
                )
            )

        summary = {
            "added": sum(1 for item in diffs if item.change_type == "added"),
            "removed": sum(1 for item in diffs if item.change_type == "removed"),
            "changed": sum(1 for item in diffs if item.change_type == "changed"),
            "unchanged": sum(1 for item in diffs if item.change_type == "unchanged"),
        }
        return MatchRuleConfigCompareResponse(
            base=base, target=target, dimensions=diffs, summary=summary
        )

    @staticmethod
    async def list_rule_experiments(
        db: AsyncSession,
        *,
        scope: str | None = None,
        template_key: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> MatchRuleExperimentListResponse:
        items, total = await MatchRuleConfigRepository.list_experiments(
            db,
            scope=scope,
            template_key=template_key,
            skip=skip,
            limit=limit,
        )
        return MatchRuleExperimentListResponse(
            items=[MatchService._experiment_response(item) for item in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    async def list_match_audits(
        db: AsyncSession,
        *,
        experiment_id: int | None = None,
        rule_config_id: int | None = None,
        job_id: int | None = None,
        seeker_id: int | None = None,
        experiment_bucket: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> MatchRuleAuditListResponse:
        items, total = await MatchRuleConfigRepository.list_audits(
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
        return MatchRuleAuditListResponse(
            items=[MatchService._audit_response(item) for item in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    async def get_match_audit(
        db: AsyncSession, audit_id: int
    ) -> MatchRuleAuditResponse:
        audit = await MatchRuleConfigRepository.get_audit_by_id(db, audit_id)
        if audit is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="match_rule_audit_not_found",
            )
        return MatchService._audit_response(audit)

    @staticmethod
    async def list_rule_operation_audits(
        db: AsyncSession,
        *,
        resource_type: str | None = None,
        resource_id: int | None = None,
        action: str | None = None,
        actor_id: int | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> MatchRuleOperationAuditListResponse:
        items, total = await MatchRuleConfigRepository.list_operation_audits(
            db,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            actor_id=actor_id,
            skip=skip,
            limit=limit,
        )
        return MatchRuleOperationAuditListResponse(
            items=[MatchService._operation_audit_response(item) for item in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    async def get_rule_experiment_effects(
        db: AsyncSession, experiment_id: int
    ) -> MatchRuleExperimentEffectResponse:
        experiment = await MatchRuleConfigRepository.get_experiment_by_id(
            db, experiment_id
        )
        if experiment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="match_rule_experiment_not_found",
            )
        buckets = {
            "control": MatchRuleExperimentBucketEffectResponse(),
            "treatment": MatchRuleExperimentBucketEffectResponse(),
        }
        rows = await MatchRuleConfigRepository.get_experiment_effect_rows(
            db, experiment_id
        )
        for bucket, match_count, avg_score, high_count, medium_count, low_count in rows:
            if bucket not in buckets:
                continue
            buckets[bucket] = MatchRuleExperimentBucketEffectResponse(
                match_count=int(match_count or 0),
                avg_score=round(float(avg_score), 2) if avg_score is not None else None,
                high_count=int(high_count or 0),
                medium_count=int(medium_count or 0),
                low_count=int(low_count or 0),
            )
        return MatchRuleExperimentEffectResponse(
            experiment_id=experiment.id,
            scope=experiment.scope,
            template_key=experiment.template_key,
            traffic_percent=experiment.traffic_percent,
            buckets=buckets,
        )

    @staticmethod
    async def get_default_rule_config_from_db(
        db: AsyncSession,
    ) -> MatchRuleConfigResponse:
        """Get active global rule config, creating default config when needed."""
        return MatchService._rule_config_response(
            await MatchService._get_active_rule_config(db)
        )

    @staticmethod
    async def get_my_job_match(
        db: AsyncSession,
        current_user: User,
        job_id: int,
    ) -> JobMatchResponse:
        if current_user.role != "seeker":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only seekers can match jobs",
            )

        job = await JobRepository.get_by_id(db, job_id)
        if job is None or job.status != "active":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="job_not_found"
            )

        return await MatchService._calculate_job_match(
            db, current_user, job, source="seeker_job_match"
        )

    @staticmethod
    async def get_recruiter_application_match(
        db: AsyncSession,
        current_user: User,
        application_id: int,
    ) -> JobMatchResponse:
        if current_user.role != "recruiter":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only recruiters can view application match",
            )

        from app.modules.application.repository import ApplicationRepository

        application = await ApplicationRepository.get_by_id(db, application_id)
        if application is None or application.recruiter_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="application_not_found"
            )
        if application.job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="job_not_found"
            )
        seeker = application.seeker or User(
            id=application.seeker_id, role="seeker", display_name=""
        )
        return await MatchService._calculate_job_match(
            db,
            seeker,
            application.job,
            source="recruiter_application_match",
            application_id=application.id,
        )

    @staticmethod
    async def _calculate_job_match(
        db: AsyncSession,
        seeker: User,
        job: Job,
        *,
        source: str = "seeker_job_match",
        application_id: int | None = None,
    ) -> JobMatchResponse:
        profile = await ResumeRepository.get_latest_structured_profile(db, seeker.id)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="profile_required",
            )

        detail = await ResumeService._structured_profile_detail_response(db, profile)
        if detail.basic_info is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="profile_required",
            )

        selection = await MatchService._select_rule_config(db, seeker=seeker, job=job)
        rule_config = selection["rule_config"]
        dimension_by_key = {
            dimension.key: dimension for dimension in rule_config.enabled_dimensions()
        }
        dimensions = [
            BaselineMatchScorer.score_skill(job, detail.skills),
            BaselineMatchScorer.score_experience(job, detail.basic_info.work_years),
            BaselineMatchScorer.score_education(
                job, detail.basic_info.highest_education
            ),
            BaselineMatchScorer.score_city(job, detail.basic_info.current_city),
            BaselineMatchScorer.score_salary(job, detail.basic_info.expected_salary),
            BaselineMatchScorer.score_intention(job, detail.basic_info.target_position),
        ]
        dimensions = [
            BaselineMatchScorer.apply_dimension_config(
                dimension, dimension_by_key[dimension.key]
            )
            for dimension in dimensions
            if dimension.key in dimension_by_key
        ]
        rule_overall_score = BaselineMatchScorer.overall_score(dimensions)
        intelligent_strategy = (
            await IntelligentMatchRuntime.active_strategy(db, rule_config)
        )
        intelligent_preview = None
        if intelligent_strategy is not None:
            intelligent_preview = await IntelligentMatchRuntime.preview_score(
                db,
                seeker=seeker,
                job=job,
                detail=detail,
                baseline_rule_score=rule_overall_score,
                strategy=intelligent_strategy,
            )
        overall_score = IntelligentMatchRuntime.overall_score(
            intelligent_preview, rule_overall_score
        )
        level, recommendation = BaselineMatchScorer.level_and_recommendation(
            overall_score
        )
        highlights = BaselineMatchScorer.build_highlights(dimensions)
        gaps = BaselineMatchScorer.build_gaps(dimensions)
        effective_weights = {
            key: int(value) if float(value).is_integer() else value
            for key, value in rule_config.effective_weights.items()
        }
        audit = await MatchService._record_match_audit(
            db,
            seeker=seeker,
            job=job,
            application_id=application_id,
            profile_parse_run_id=profile.parse_run_id,
            rule_config=rule_config,
            experiment=selection.get("experiment"),
            experiment_bucket=selection.get("experiment_bucket"),
            source=source,
            overall_score=overall_score,
            level=level,
            recommendation=recommendation,
            dimensions=dimensions,
            intelligent_snapshot=IntelligentMatchRuntime.audit_snapshot(
                intelligent_preview, overall_score
            ),
        )

        return JobMatchResponse(
            job=MatchJobSummaryResponse(
                id=job.id,
                title=job.title,
                city=job.city,
                salary_min=job.salary_min,
                salary_max=job.salary_max,
            ),
            overall_score=overall_score,
            level=level,
            recommendation=recommendation,
            summary=BaselineMatchScorer.summary(overall_score, highlights, gaps),
            weights=effective_weights,
            configured_weights=rule_config.configured_weights,
            effective_weights=rule_config.effective_weights,
            rule_config=MatchService._rule_config_response(rule_config),
            dimensions=dimensions,
            highlights=highlights,
            gaps=gaps,
            source=MatchSourceResponse(
                strategy="intelligent_hybrid_v1"
                if intelligent_preview is not None
                else "rule_v1",
                intelligent_strategy_id=intelligent_strategy.id
                if intelligent_strategy is not None
                else None,
                match_source=intelligent_preview.match_source
                if intelligent_preview is not None
                else "rule_baseline",
                recall_source=intelligent_preview.recall_source
                if intelligent_preview is not None
                else "rule_only",
                degrade_reason=intelligent_preview.degrade_reason
                if intelligent_preview is not None
                else None,
                profile_parse_run_id=profile.parse_run_id,
                job_id=job.id,
                rule_config_id=rule_config.id,
                experiment_id=selection["experiment"].id
                if selection.get("experiment")
                else None,
                experiment_bucket=selection.get("experiment_bucket"),
                audit_id=audit.id,
                scope=rule_config.scope,
                template_key=rule_config.template_key,
                generated_at=datetime.now(timezone.utc).replace(tzinfo=None),
            ),
        )











    @staticmethod
    def _rule_config_response(rule_config: MatchRuleConfig) -> MatchRuleConfigResponse:
        return MatchRuleConfigResponse(
            id=rule_config.id,
            name=rule_config.name,
            strategy=rule_config.strategy,
            scope=rule_config.scope,
            template_key=rule_config.template_key,
            template_name=rule_config.template_name,
            status=rule_config.status,
            version=rule_config.version,
            description=rule_config.description,
            parent_version_id=rule_config.parent_version_id,
            effective_from=rule_config.effective_from,
            effective_to=rule_config.effective_to,
            created_by=rule_config.created_by,
            updated_by=rule_config.updated_by,
            configured_total_weight=rule_config.configured_total_weight,
            effective_total_weight=rule_config.effective_total_weight,
            dimensions=[
                MatchRuleDimensionResponse(
                    key=dimension.key,
                    label=dimension.label,
                    weight=dimension.configured_weight,
                    configured_weight=dimension.configured_weight,
                    effective_weight=dimension.effective_weight,
                    enabled=dimension.enabled,
                    description=dimension.description,
                    scoring_method=dimension.scoring_method,
                    logic=dimension.logic,
                    sort_order=dimension.sort_order,
                )
                for dimension in rule_config.dimensions
            ],
            updated_at=rule_config.updated_at,
        )

    @staticmethod
    def _experiment_response(
        experiment: MatchRuleExperimentModel,
    ) -> MatchRuleExperimentResponse:
        return MatchRuleExperimentResponse(
            id=experiment.id,
            name=experiment.name,
            description=experiment.description,
            scope=experiment.scope,
            template_key=experiment.template_key,
            status=experiment.status,
            traffic_percent=experiment.traffic_percent,
            control_config_id=experiment.control_config_id,
            treatment_config_id=experiment.treatment_config_id,
            audience=experiment.audience or {},
            started_at=experiment.started_at,
            ended_at=experiment.ended_at,
            created_by=experiment.created_by,
            updated_by=experiment.updated_by,
            created_at=experiment.created_at,
            updated_at=experiment.updated_at,
        )

    @staticmethod
    def _operation_audit_response(
        audit: MatchRuleOperationAuditModel,
    ) -> MatchRuleOperationAuditResponse:
        return MatchRuleOperationAuditResponse(
            id=audit.id,
            actor_id=audit.actor_id,
            action=audit.action,
            resource_type=audit.resource_type,
            resource_id=audit.resource_id,
            reason=audit.reason,
            before_snapshot=audit.before_snapshot,
            after_snapshot=audit.after_snapshot,
            metadata=audit.metadata_json or {},
            created_at=audit.created_at,
        )













    @staticmethod
    async def _get_active_rule_config(
        db: AsyncSession, scope: str = "global"
    ) -> MatchRuleConfig:
        await MatchService._ensure_default_rule_config(db)
        db_config = await MatchRuleConfigRepository.get_active_by_scope(db, scope=scope)
        if db_config is None:
            return MatchRuleConfigService.get_default_config()
        try:
            return MatchRuleConfigService.from_model(db_config)
        except ValueError:
            return MatchRuleConfigService.get_default_config()

    @staticmethod
    async def _select_rule_config(
        db: AsyncSession, *, seeker: User, job: Job
    ) -> dict[str, Any]:
        await MatchService._ensure_default_rule_config(db)
        for scope in [f"job_id:{job.id}", "global"]:
            experiment = await MatchRuleConfigRepository.get_running_experiment(
                db, scope=scope, template_key="default"
            )
            if experiment is not None:
                bucket = MatchService._experiment_bucket(
                    experiment, seeker_id=seeker.id, job_id=job.id
                )
                config_id = (
                    experiment.treatment_config_id
                    if bucket == "treatment"
                    else experiment.control_config_id
                )
                config = await MatchRuleConfigRepository.get_by_id(db, config_id)
                if config is not None:
                    try:
                        return {
                            "rule_config": MatchRuleConfigService.from_model(config),
                            "experiment": experiment,
                            "experiment_bucket": bucket,
                        }
                    except ValueError:
                        pass

            db_config = await MatchRuleConfigRepository.get_active_by_scope(
                db, scope=scope, template_key="default"
            )
            if db_config is not None:
                try:
                    return {
                        "rule_config": MatchRuleConfigService.from_model(db_config),
                        "experiment": None,
                        "experiment_bucket": None,
                    }
                except ValueError:
                    pass

        return {
            "rule_config": MatchRuleConfigService.get_default_config(),
            "experiment": None,
            "experiment_bucket": None,
        }

    @staticmethod
    def _experiment_bucket(
        experiment: MatchRuleExperimentModel, *, seeker_id: int, job_id: int
    ) -> str:
        if experiment.traffic_percent <= 0:
            return "control"
        if experiment.traffic_percent >= 100:
            return "treatment"
        digest = hashlib.sha256(
            f"{experiment.id}:{seeker_id}:{job_id}".encode("utf-8")
        ).hexdigest()
        bucket_value = int(digest[:8], 16) % 100
        return "treatment" if bucket_value < experiment.traffic_percent else "control"

    @staticmethod
    async def _record_match_audit(
        db: AsyncSession,
        *,
        seeker: User,
        job: Job,
        application_id: int | None,
        profile_parse_run_id: int | None,
        rule_config: MatchRuleConfig,
        experiment: MatchRuleExperimentModel | None,
        experiment_bucket: str | None,
        source: str,
        overall_score: int,
        level: str,
        recommendation: str,
        dimensions: list[MatchDimensionResponse],
        intelligent_snapshot: dict[str, Any] | None = None,
    ) -> MatchRuleMatchAuditModel:
        dimension_scores = [
            {
                "key": dimension.key,
                "label": dimension.label,
                "score": dimension.score,
                "configured_weight": dimension.configured_weight,
                "effective_weight": dimension.effective_weight,
                "weighted_score": dimension.weighted_score,
                "matched": dimension.matched,
                "missing": dimension.missing,
                "explanation": dimension.explanation,
            }
            for dimension in dimensions
        ]
        if intelligent_snapshot is not None:
            dimension_scores.append(intelligent_snapshot)
        audit = MatchRuleMatchAuditModel(
            job_id=job.id,
            seeker_id=seeker.id,
            application_id=application_id,
            profile_parse_run_id=profile_parse_run_id,
            rule_config_id=rule_config.id if isinstance(rule_config.id, int) else None,
            experiment_id=experiment.id if experiment else None,
            experiment_bucket=experiment_bucket,
            scope=rule_config.scope,
            template_key=rule_config.template_key,
            source=source,
            overall_score=overall_score,
            level=level,
            recommendation=recommendation,
            dimension_scores=dimension_scores,
        )
        return await MatchRuleConfigRepository.create_audit(db, audit)

    @staticmethod
    def _audit_response(audit: MatchRuleMatchAuditModel) -> MatchRuleAuditResponse:
        return MatchRuleAuditResponse(
            id=audit.id,
            job_id=audit.job_id,
            seeker_id=audit.seeker_id,
            application_id=audit.application_id,
            profile_parse_run_id=audit.profile_parse_run_id,
            rule_config_id=audit.rule_config_id,
            experiment_id=audit.experiment_id,
            experiment_bucket=audit.experiment_bucket,
            scope=audit.scope,
            template_key=audit.template_key,
            source=audit.source,
            overall_score=audit.overall_score,
            level=audit.level,
            recommendation=audit.recommendation,
            dimension_scores=audit.dimension_scores or [],
            job=MatchAuditJobSummaryResponse(
                id=audit.job.id,
                title=audit.job.title,
                city=audit.job.city,
            )
            if audit.job
            else None,
            seeker=MatchAuditSeekerSummaryResponse(
                id=audit.seeker.id,
                display_name=audit.seeker.display_name,
            )
            if audit.seeker
            else None,
            rule_config=MatchAuditRuleConfigSummaryResponse(
                id=audit.rule_config.id,
                name=audit.rule_config.name,
                version=audit.rule_config.version,
                status=audit.rule_config.status,
            )
            if audit.rule_config
            else None,
            experiment=MatchAuditExperimentSummaryResponse(
                id=audit.experiment.id,
                name=audit.experiment.name,
                status=audit.experiment.status,
            )
            if audit.experiment
            else None,
            created_at=audit.created_at,
        )

    @staticmethod
    async def _ensure_default_rule_config(db: AsyncSession) -> MatchRuleConfigModel:
        existing = await MatchRuleConfigRepository.get_active_by_scope(
            db, scope="global"
        )
        if existing is not None:
            return existing
        return await MatchRuleConfigRepository.create_default(
            db, DEFAULT_RULE_DIMENSIONS
        )
