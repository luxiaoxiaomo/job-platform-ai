"""
Rule-based seeker-job matching service.
"""
from datetime import datetime, timezone
import hashlib
import re
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.application.models import JobApplication
from app.modules.job.models import JobFavorite, JobVisit
from app.modules.job.models import Job
from app.modules.job.repository import JobRepository
from app.modules.match.config import DEFAULT_RULE_DIMENSIONS, MatchRuleConfig, MatchRuleConfigService, MatchRuleDimensionConfig
from app.modules.match.models import (
    MatchRuleConfigModel,
    MatchRuleExperimentModel,
    MatchRuleMatchAuditModel,
    MatchRuleOperationAuditModel,
)
from app.modules.match.repository import MatchRuleConfigRepository
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
    MatchQualityAnomalyResponse,
    MatchQualityDashboardResponse,
    MatchQualityExperimentConfidenceResponse,
    MatchQualityMetricResponse,
    MatchQualityRuleVersionResponse,
    MatchQualitySegmentResponse,
    MatchQualityTuningSuggestionResponse,
    MatchQualityTimeBucketResponse,
    MatchRuleOperationAuditListResponse,
    MatchRuleOperationAuditResponse,
    MatchSourceResponse,
)
from app.modules.resume.repository import ResumeRepository
from app.modules.resume.service import ResumeService
from app.modules.user.models import User


MATCH_WEIGHTS = {
    "skill": 35,
    "experience": 20,
    "education": 15,
    "city": 10,
    "salary": 10,
    "intention": 10,
}

DIMENSION_LABELS = {
    "skill": "技能匹配",
    "experience": "经验年限",
    "education": "学历匹配",
    "city": "城市匹配",
    "salary": "薪资匹配",
    "intention": "岗位意向",
}

KNOWN_SKILLS = [
    "PeopleSoft",
    "HCM",
    "ERP",
    "Oracle",
    "SAP",
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "React",
    "Vue",
    "Node.js",
    "SQL",
    "MySQL",
    "PostgreSQL",
    "Excel",
    "PMP",
]

QUALITY_SEGMENT_TYPES = ("city", "position_category", "standard_position", "job_tag", "rule_version", "experiment_bucket")
QUALITY_SAMPLE_INSUFFICIENT = 30
QUALITY_SAMPLE_USABLE = 100
QUALITY_GUARDRAIL = (
    "Draft suggestion only; do not modify rules automatically. Create a new rule version through rule editing "
    "and release governance before applying changes."
)

EDUCATION_RANKS = {
    "不限": 0,
    "中专": 1,
    "高中": 1,
    "大专": 2,
    "专科": 2,
    "本科": 3,
    "硕士": 4,
    "研究生": 4,
    "博士": 5,
}


class MatchService:
    """Rule-based matching use cases."""

    @staticmethod
    def get_default_rule_config() -> MatchRuleConfigResponse:
        """Return the current default rule config."""
        return MatchService._rule_config_response(MatchRuleConfigService.get_default_config())

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
            items=[MatchService._rule_config_response(MatchRuleConfigService.from_model(item)) for item in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    async def get_rule_config(db: AsyncSession, config_id: int) -> MatchRuleConfigResponse:
        """Get one persisted rule config."""
        await MatchService._ensure_default_rule_config(db)
        config = await MatchRuleConfigRepository.get_by_id(db, config_id)
        if config is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="match_rule_config_not_found")
        return MatchService._rule_config_response(MatchRuleConfigService.from_model(config))

    @staticmethod
    async def get_rule_config_history(db: AsyncSession, config_id: int) -> MatchRuleConfigListResponse:
        """Get version history for one persisted rule config."""
        await MatchService._ensure_default_rule_config(db)
        config = await MatchRuleConfigRepository.get_by_id(db, config_id)
        if config is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="match_rule_config_not_found")
        items = await MatchRuleConfigRepository.get_history(db, config)
        return MatchRuleConfigListResponse(
            items=[MatchService._rule_config_response(MatchRuleConfigService.from_model(item)) for item in items],
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="match_rule_config_not_found")

        base = MatchService._rule_config_response(MatchRuleConfigService.from_model(base_model))
        target = MatchService._rule_config_response(MatchRuleConfigService.from_model(target_model))
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
                    or base_dimension.configured_weight != target_dimension.configured_weight
                    or base_dimension.enabled != target_dimension.enabled
                    or base_dimension.description != target_dimension.description
                    or base_dimension.scoring_method != target_dimension.scoring_method
                    or base_dimension.logic != target_dimension.logic
                )
                change_type = "changed" if changed else "unchanged"
            base_weight = base_dimension.configured_weight if base_dimension else None
            target_weight = target_dimension.configured_weight if target_dimension else None
            diffs.append(
                MatchRuleDimensionDiffResponse(
                    key=key,
                    label=label,
                    change_type=change_type,
                    base_weight=base_weight,
                    target_weight=target_weight,
                    weight_delta=(target_weight - base_weight) if base_weight is not None and target_weight is not None else None,
                    base_enabled=base_dimension.enabled if base_dimension else None,
                    target_enabled=target_dimension.enabled if target_dimension else None,
                    enabled_changed=bool(base_dimension and target_dimension and base_dimension.enabled != target_dimension.enabled),
                    label_changed=bool(base_dimension and target_dimension and base_dimension.label != target_dimension.label),
                    description_changed=bool(base_dimension and target_dimension and base_dimension.description != target_dimension.description),
                    scoring_method_changed=bool(
                        base_dimension and target_dimension and base_dimension.scoring_method != target_dimension.scoring_method
                    ),
                    logic_changed=bool(base_dimension and target_dimension and base_dimension.logic != target_dimension.logic),
                )
            )

        summary = {
            "added": sum(1 for item in diffs if item.change_type == "added"),
            "removed": sum(1 for item in diffs if item.change_type == "removed"),
            "changed": sum(1 for item in diffs if item.change_type == "changed"),
            "unchanged": sum(1 for item in diffs if item.change_type == "unchanged"),
        }
        return MatchRuleConfigCompareResponse(base=base, target=target, dimensions=diffs, summary=summary)

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
    async def get_match_audit(db: AsyncSession, audit_id: int) -> MatchRuleAuditResponse:
        audit = await MatchRuleConfigRepository.get_audit_by_id(db, audit_id)
        if audit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="match_rule_audit_not_found")
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
    async def get_rule_experiment_effects(db: AsyncSession, experiment_id: int) -> MatchRuleExperimentEffectResponse:
        experiment = await MatchRuleConfigRepository.get_experiment_by_id(db, experiment_id)
        if experiment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="match_rule_experiment_not_found")
        buckets = {
            "control": MatchRuleExperimentBucketEffectResponse(),
            "treatment": MatchRuleExperimentBucketEffectResponse(),
        }
        rows = await MatchRuleConfigRepository.get_experiment_effect_rows(db, experiment_id)
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
    async def get_match_quality_summary(
        db: AsyncSession,
        *,
        experiment_id: int | None = None,
        rule_config_id: int | None = None,
        scope: str | None = None,
        template_key: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        city: str | None = None,
        position_category: str | None = None,
        standard_position_id: int | None = None,
        job_tag: str | None = None,
        segment_type: str | None = None,
        include_insights: bool = True,
    ) -> MatchQualityDashboardResponse:
        """Aggregate match audit quality with downstream seeker behavior."""
        if segment_type is not None and segment_type not in QUALITY_SEGMENT_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_segment_type")
        if created_from and created_to and created_from > created_to:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_created_range")

        audits = await MatchRuleConfigRepository.list_quality_audits(
            db,
            experiment_id=experiment_id,
            rule_config_id=rule_config_id,
            scope=scope,
            template_key=template_key,
            created_from=created_from,
            created_to=created_to,
        )
        audits = MatchService._filter_quality_audits(
            audits,
            city=city,
            position_category=position_category,
            standard_position_id=standard_position_id,
            job_tag=job_tag,
        )
        behavior_pairs = await MatchService._quality_behavior_pairs(db, audits)
        summary = MatchService._quality_metric(audits, behavior_pairs)

        rule_groups: dict[int | None, list[MatchRuleMatchAuditModel]] = {}
        bucket_groups: dict[str, list[MatchRuleMatchAuditModel]] = {"control": [], "treatment": []}
        time_groups: dict[str, list[MatchRuleMatchAuditModel]] = {}
        for audit in audits:
            rule_groups.setdefault(audit.rule_config_id, []).append(audit)
            if audit.experiment_bucket:
                bucket_groups.setdefault(audit.experiment_bucket, []).append(audit)
            time_groups.setdefault(audit.created_at.date().isoformat(), []).append(audit)

        rule_versions = []
        for config_id, group in rule_groups.items():
            first = group[0]
            metric = MatchService._quality_metric(group, behavior_pairs)
            rule_versions.append(
                MatchQualityRuleVersionResponse(
                    **metric.model_dump(),
                    rule_config_id=config_id,
                    rule_config_name=first.rule_config.name if first.rule_config else None,
                    rule_config_version=first.rule_config.version if first.rule_config else None,
                    rule_config_status=first.rule_config.status if first.rule_config else None,
                )
            )
        rule_versions.sort(key=lambda item: (item.rule_config_version or 0, item.rule_config_id or 0), reverse=True)

        experiment_buckets = {
            bucket: MatchService._quality_metric(group, behavior_pairs)
            for bucket, group in sorted(bucket_groups.items())
        }
        time_buckets = [
            MatchQualityTimeBucketResponse(
                **MatchService._quality_metric(group, behavior_pairs).model_dump(),
                date=day,
            )
            for day, group in sorted(time_groups.items())
        ]
        segments = MatchService._quality_segments(
            audits,
            behavior_pairs,
            summary,
            segment_type=segment_type,
        ) if include_insights else []
        experiment_confidence = MatchService._quality_experiment_confidence(
            experiment_id,
            bucket_groups,
            behavior_pairs,
        ) if include_insights else None
        anomalies = MatchService._quality_anomalies(summary, segments) if include_insights else []
        tuning_suggestions = MatchService._quality_tuning_suggestions(anomalies) if include_insights else []

        return MatchQualityDashboardResponse(
            filters={
                "experiment_id": experiment_id,
                "rule_config_id": rule_config_id,
                "scope": scope,
                "template_key": template_key,
                "created_from": created_from.isoformat() if created_from else None,
                "created_to": created_to.isoformat() if created_to else None,
                "city": city,
                "position_category": position_category,
                "standard_position_id": standard_position_id,
                "job_tag": job_tag,
                "segment_type": segment_type,
                "include_insights": include_insights,
            },
            summary=summary,
            rule_versions=rule_versions,
            experiment_buckets=experiment_buckets,
            time_buckets=time_buckets,
            segments=segments,
            experiment_confidence=experiment_confidence,
            anomalies=anomalies,
            tuning_suggestions=tuning_suggestions,
        )

    @staticmethod
    async def get_default_rule_config_from_db(db: AsyncSession) -> MatchRuleConfigResponse:
        """Get active global rule config, creating default config when needed."""
        return MatchService._rule_config_response(await MatchService._get_active_rule_config(db))

    @staticmethod
    async def get_my_job_match(
        db: AsyncSession,
        current_user: User,
        job_id: int,
    ) -> JobMatchResponse:
        if current_user.role != "seeker":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only seekers can match jobs")

        job = await JobRepository.get_by_id(db, job_id)
        if job is None or job.status != "active":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job_not_found")

        return await MatchService._calculate_job_match(db, current_user, job, source="seeker_job_match")

    @staticmethod
    async def get_recruiter_application_match(
        db: AsyncSession,
        current_user: User,
        application_id: int,
    ) -> JobMatchResponse:
        if current_user.role != "recruiter":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only recruiters can view application match")

        from app.modules.application.repository import ApplicationRepository

        application = await ApplicationRepository.get_by_id(db, application_id)
        if application is None or application.recruiter_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="application_not_found")
        if application.job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job_not_found")
        seeker = application.seeker or User(id=application.seeker_id, role="seeker", display_name="")
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
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="profile_required")

        detail = await ResumeService._structured_profile_detail_response(db, profile)
        if detail.basic_info is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="profile_required")

        selection = await MatchService._select_rule_config(db, seeker=seeker, job=job)
        rule_config = selection["rule_config"]
        dimension_by_key = {dimension.key: dimension for dimension in rule_config.enabled_dimensions()}
        dimensions = [
            MatchService._score_skill(job, detail.skills),
            MatchService._score_experience(job, detail.basic_info.work_years),
            MatchService._score_education(job, detail.basic_info.highest_education),
            MatchService._score_city(job, detail.basic_info.current_city),
            MatchService._score_salary(job, detail.basic_info.expected_salary),
            MatchService._score_intention(job, detail.basic_info.target_position),
        ]
        dimensions = [
            MatchService._apply_dimension_config(dimension, dimension_by_key[dimension.key])
            for dimension in dimensions
            if dimension.key in dimension_by_key
        ]
        overall_score = MatchService._overall_score(dimensions)
        level, recommendation = MatchService._level_and_recommendation(overall_score)
        highlights = MatchService._build_highlights(dimensions)
        gaps = MatchService._build_gaps(dimensions)
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
            summary=MatchService._summary(overall_score, highlights, gaps),
            weights=effective_weights,
            configured_weights=rule_config.configured_weights,
            effective_weights=rule_config.effective_weights,
            rule_config=MatchService._rule_config_response(rule_config),
            dimensions=dimensions,
            highlights=highlights,
            gaps=gaps,
            source=MatchSourceResponse(
                profile_parse_run_id=profile.parse_run_id,
                job_id=job.id,
                rule_config_id=rule_config.id,
                experiment_id=selection["experiment"].id if selection.get("experiment") else None,
                experiment_bucket=selection.get("experiment_bucket"),
                audit_id=audit.id,
                scope=rule_config.scope,
                template_key=rule_config.template_key,
                generated_at=datetime.now(timezone.utc).replace(tzinfo=None),
            ),
        )

    @staticmethod
    def _dimension(
        key: str,
        score: int,
        *,
        matched: list[str] | None = None,
        missing: list[str] | None = None,
        explanation: str,
    ) -> MatchDimensionResponse:
        return MatchDimensionResponse(
            key=key,
            label=key,
            score=max(0, min(100, round(score))),
            weight=0,
            configured_weight=0,
            effective_weight=0,
            weighted_score=0,
            matched=matched or [],
            missing=missing or [],
            explanation=explanation,
            description="",
            scoring_method="",
            logic={},
        )

    @staticmethod
    def _apply_dimension_config(
        dimension: MatchDimensionResponse,
        config: MatchRuleDimensionConfig,
    ) -> MatchDimensionResponse:
        weighted_score = round(dimension.score * config.effective_weight / 100, 2)
        return dimension.model_copy(
            update={
                "label": config.label,
                "weight": int(config.effective_weight)
                if float(config.effective_weight).is_integer()
                else config.effective_weight,
                "configured_weight": config.configured_weight,
                "effective_weight": config.effective_weight,
                "weighted_score": int(weighted_score) if weighted_score.is_integer() else weighted_score,
                "description": config.description,
                "scoring_method": config.scoring_method,
                "logic": config.logic,
            }
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
    def _experiment_response(experiment: MatchRuleExperimentModel) -> MatchRuleExperimentResponse:
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
    def _operation_audit_response(audit: MatchRuleOperationAuditModel) -> MatchRuleOperationAuditResponse:
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
    def _filter_quality_audits(
        audits: list[MatchRuleMatchAuditModel],
        *,
        city: str | None,
        position_category: str | None,
        standard_position_id: int | None,
        job_tag: str | None,
    ) -> list[MatchRuleMatchAuditModel]:
        """Apply segment filters after loading the audit fact sample."""
        filtered = audits
        if city:
            city_text = city.strip().lower()
            filtered = [audit for audit in filtered if audit.job and (audit.job.city or "").strip().lower() == city_text]
        if position_category:
            category_text = position_category.strip().lower()
            filtered = [
                audit
                for audit in filtered
                if audit.job
                and audit.job.standard_position
                and (audit.job.standard_position.category or "").strip().lower() == category_text
            ]
        if standard_position_id is not None:
            filtered = [
                audit
                for audit in filtered
                if audit.job and audit.job.standard_position_id == standard_position_id
            ]
        if job_tag:
            tag_text = job_tag.strip().lower()
            filtered = [
                audit
                for audit in filtered
                if audit.job and any(str(tag).strip().lower() == tag_text for tag in (audit.job.tags or []))
            ]
        return filtered

    @staticmethod
    async def _quality_behavior_pairs(
        db: AsyncSession,
        audits: list[MatchRuleMatchAuditModel],
    ) -> dict[str, set[tuple[int, int]]]:
        pairs = {(audit.job_id, audit.seeker_id) for audit in audits if audit.job_id and audit.seeker_id}
        if not pairs:
            return {"applications": set(), "favorites": set(), "visits": set()}

        job_ids = {job_id for job_id, _ in pairs}
        seeker_ids = {seeker_id for _, seeker_id in pairs}

        application_result = await db.execute(
            select(JobApplication.job_id, JobApplication.seeker_id).where(
                JobApplication.job_id.in_(job_ids),
                JobApplication.seeker_id.in_(seeker_ids),
            )
        )
        favorite_result = await db.execute(
            select(JobFavorite.job_id, JobFavorite.seeker_id).where(
                JobFavorite.job_id.in_(job_ids),
                JobFavorite.seeker_id.in_(seeker_ids),
            )
        )
        visit_result = await db.execute(
            select(JobVisit.job_id, JobVisit.seeker_id).where(
                JobVisit.job_id.in_(job_ids),
                JobVisit.seeker_id.in_(seeker_ids),
            )
        )

        return {
            "applications": {(int(job_id), int(seeker_id)) for job_id, seeker_id in application_result.all()} & pairs,
            "favorites": {(int(job_id), int(seeker_id)) for job_id, seeker_id in favorite_result.all()} & pairs,
            "visits": {(int(job_id), int(seeker_id)) for job_id, seeker_id in visit_result.all()} & pairs,
        }

    @staticmethod
    def _quality_metric(
        audits: list[MatchRuleMatchAuditModel],
        behavior_pairs: dict[str, set[tuple[int, int]]],
    ) -> MatchQualityMetricResponse:
        match_count = len(audits)
        pairs = [(audit.job_id, audit.seeker_id) for audit in audits if audit.job_id and audit.seeker_id]
        favorite_count = sum(1 for pair in pairs if pair in behavior_pairs["favorites"])
        application_count = sum(1 for pair in pairs if pair in behavior_pairs["applications"])
        visit_count = sum(1 for pair in pairs if pair in behavior_pairs["visits"])

        def rate(count: int) -> float:
            return round(count / match_count * 100, 2) if match_count else 0

        low_count = sum(1 for audit in audits if audit.level == "low")
        return MatchQualityMetricResponse(
            match_count=match_count,
            avg_score=round(sum(audit.overall_score for audit in audits) / match_count, 2) if match_count else None,
            high_count=sum(1 for audit in audits if audit.level == "high"),
            medium_count=sum(1 for audit in audits if audit.level == "medium"),
            low_count=low_count,
            favorite_count=favorite_count,
            application_count=application_count,
            visit_count=visit_count,
            favorite_rate=rate(favorite_count),
            application_rate=rate(application_count),
            visit_rate=rate(visit_count),
            low_score_rate=rate(low_count),
            sample_status=MatchService._quality_sample_status(match_count),
        )

    @staticmethod
    def _quality_sample_status(match_count: int) -> str:
        if match_count < QUALITY_SAMPLE_INSUFFICIENT:
            return "insufficient"
        if match_count < QUALITY_SAMPLE_USABLE:
            return "limited"
        return "usable"

    @staticmethod
    def _quality_segments(
        audits: list[MatchRuleMatchAuditModel],
        behavior_pairs: dict[str, set[tuple[int, int]]],
        summary: MatchQualityMetricResponse,
        *,
        segment_type: str | None = None,
    ) -> list[MatchQualitySegmentResponse]:
        segment_types = [segment_type] if segment_type else list(QUALITY_SEGMENT_TYPES)
        segments: list[MatchQualitySegmentResponse] = []
        for current_type in segment_types:
            groups: dict[tuple[str, str], list[MatchRuleMatchAuditModel]] = {}
            for audit in audits:
                for key, label in MatchService._quality_segment_values(audit, current_type):
                    groups.setdefault((key, label), []).append(audit)

            for (key, label), group in groups.items():
                metric = MatchService._quality_metric(group, behavior_pairs)
                application_delta = round(metric.application_rate - summary.application_rate, 2)
                favorite_delta = round(metric.favorite_rate - summary.favorite_rate, 2)
                low_score_delta = round(metric.low_score_rate - summary.low_score_rate, 2)
                segments.append(
                    MatchQualitySegmentResponse(
                        **metric.model_dump(),
                        segment_type=current_type,
                        segment_key=key,
                        segment_label=label,
                        application_rate_delta=application_delta,
                        favorite_rate_delta=favorite_delta,
                        low_score_rate_delta=low_score_delta,
                        risk_level=MatchService._quality_segment_risk(metric, application_delta, low_score_delta),
                    )
                )

        risk_order = {"high": 0, "medium": 1, "low": 2}
        segments.sort(
            key=lambda item: (
                risk_order[item.risk_level],
                item.sample_status == "insufficient",
                item.application_rate_delta,
                -item.low_score_rate_delta,
                -item.match_count,
            )
        )
        return segments[:80]

    @staticmethod
    def _quality_segment_values(audit: MatchRuleMatchAuditModel, segment_type: str) -> list[tuple[str, str]]:
        unclassified = [("unclassified", "Unclassified")]
        if segment_type == "city":
            if audit.job and audit.job.city:
                return [(audit.job.city, audit.job.city)]
            return unclassified
        if segment_type == "position_category":
            if audit.job and audit.job.standard_position and audit.job.standard_position.category:
                return [(audit.job.standard_position.category, audit.job.standard_position.category)]
            return unclassified
        if segment_type == "standard_position":
            if audit.job and audit.job.standard_position:
                return [(str(audit.job.standard_position.id), audit.job.standard_position.name)]
            return unclassified
        if segment_type == "job_tag":
            if audit.job and isinstance(audit.job.tags, list) and audit.job.tags:
                return [(str(tag), str(tag)) for tag in audit.job.tags if str(tag).strip()]
            return unclassified
        if segment_type == "rule_version":
            if audit.rule_config:
                return [(str(audit.rule_config.id), f"{audit.rule_config.name} V{audit.rule_config.version}")]
            if audit.rule_config_id is not None:
                return [(str(audit.rule_config_id), str(audit.rule_config_id))]
            return unclassified
        if segment_type == "experiment_bucket":
            if audit.experiment_bucket:
                return [(audit.experiment_bucket, audit.experiment_bucket)]
            return unclassified
        return unclassified

    @staticmethod
    def _quality_segment_risk(metric: MatchQualityMetricResponse, application_delta: float, low_score_delta: float) -> str:
        if metric.sample_status == "insufficient":
            return "low"
        if metric.sample_status == "usable" and (application_delta <= -5 or low_score_delta >= 15):
            return "high"
        if application_delta <= -3 or low_score_delta >= 10:
            return "medium"
        return "low"

    @staticmethod
    def _quality_experiment_confidence(
        experiment_id: int | None,
        bucket_groups: dict[str, list[MatchRuleMatchAuditModel]],
        behavior_pairs: dict[str, set[tuple[int, int]]],
    ) -> MatchQualityExperimentConfidenceResponse | None:
        if experiment_id is None:
            return None

        control = MatchService._quality_metric(bucket_groups.get("control", []), behavior_pairs)
        treatment = MatchService._quality_metric(bucket_groups.get("treatment", []), behavior_pairs)
        sample_count = min(control.match_count, treatment.match_count)
        sample_status = MatchService._quality_sample_status(sample_count)
        application_delta = round(treatment.application_rate - control.application_rate, 2)
        favorite_delta = round(treatment.favorite_rate - control.favorite_rate, 2)
        if control.avg_score is None or treatment.avg_score is None:
            avg_score_delta = None
        else:
            avg_score_delta = round(treatment.avg_score - control.avg_score, 2)

        if control.match_count == 0 or treatment.match_count == 0:
            confidence_status = "not_applicable"
            hint = "Control and treatment samples are both required before judging experiment confidence."
        elif sample_status == "insufficient":
            confidence_status = "insufficient_sample"
            hint = "Sample is below 30 per bucket; expand the time range before drawing conclusions."
        elif application_delta >= 3:
            confidence_status = "treatment_likely_better"
            hint = "Treatment application rate is above control by the business threshold."
        elif application_delta <= -3:
            confidence_status = "treatment_likely_worse"
            hint = "Treatment application rate is below control by the business threshold."
        else:
            confidence_status = "no_clear_difference"
            hint = "Samples are usable, but application-rate delta is below the business threshold."

        return MatchQualityExperimentConfidenceResponse(
            experiment_id=experiment_id,
            control_match_count=control.match_count,
            treatment_match_count=treatment.match_count,
            control_application_rate=control.application_rate,
            treatment_application_rate=treatment.application_rate,
            application_rate_delta=application_delta,
            favorite_rate_delta=favorite_delta,
            avg_score_delta=avg_score_delta,
            sample_status=sample_status,
            confidence_status=confidence_status,
            decision_hint=hint,
        )

    @staticmethod
    def _quality_anomalies(
        summary: MatchQualityMetricResponse,
        segments: list[MatchQualitySegmentResponse],
    ) -> list[MatchQualityAnomalyResponse]:
        anomalies: list[MatchQualityAnomalyResponse] = []
        for segment in segments:
            if segment.sample_status == "insufficient" or segment.segment_key == "unclassified":
                continue
            if segment.application_rate_delta <= -5:
                severity = "high" if segment.sample_status == "usable" else "medium"
                anomalies.append(
                    MatchService._quality_anomaly(
                        severity=severity,
                        anomaly_type="low_application_rate",
                        segment=segment,
                        metric_delta=segment.application_rate_delta,
                        evidence=(
                            f"Application rate is {abs(segment.application_rate_delta):.2f} percentage points below "
                            f"overall, sample {segment.match_count}."
                        ),
                        action="Open this segment's match audits and inspect skill, salary, and city dimensions.",
                    )
                )
            if segment.low_score_rate_delta >= 15:
                severity = "high" if segment.sample_status == "usable" else "medium"
                anomalies.append(
                    MatchService._quality_anomaly(
                        severity=severity,
                        anomaly_type="high_low_score_rate",
                        segment=segment,
                        metric_delta=segment.low_score_rate_delta,
                        evidence=(
                            f"Low-score rate is {segment.low_score_rate_delta:.2f} percentage points above overall, "
                            f"sample {segment.match_count}."
                        ),
                        action="Review whether this segment needs broader matching logic or separate rule scope.",
                    )
                )
            if (
                summary.avg_score is not None
                and segment.avg_score is not None
                and segment.avg_score >= summary.avg_score + 5
                and segment.application_rate_delta <= -5
            ):
                anomalies.append(
                    MatchService._quality_anomaly(
                        severity="high" if segment.sample_status == "usable" else "medium",
                        anomaly_type="high_score_low_conversion",
                        segment=segment,
                        metric_delta=segment.application_rate_delta,
                        evidence=(
                            f"Average score is {segment.avg_score:.2f}, but application rate is "
                            f"{abs(segment.application_rate_delta):.2f} percentage points below overall."
                        ),
                        action="Check false-positive dimensions before promoting the current rule version.",
                    )
                )
        severity_order = {"high": 0, "medium": 1, "low": 2}
        anomalies.sort(key=lambda item: (severity_order[item.severity], item.metric_delta))
        return anomalies[:20]

    @staticmethod
    def _quality_anomaly(
        *,
        severity: str,
        anomaly_type: str,
        segment: MatchQualitySegmentResponse,
        metric_delta: float,
        evidence: str,
        action: str,
    ) -> MatchQualityAnomalyResponse:
        return MatchQualityAnomalyResponse(
            severity=severity,
            type=anomaly_type,
            segment_type=segment.segment_type,
            segment_key=segment.segment_key,
            segment_label=segment.segment_label,
            evidence=evidence,
            metric_delta=metric_delta,
            sample_status=segment.sample_status,
            suggested_next_action=action,
        )

    @staticmethod
    def _quality_tuning_suggestions(
        anomalies: list[MatchQualityAnomalyResponse],
    ) -> list[MatchQualityTuningSuggestionResponse]:
        suggestions: list[MatchQualityTuningSuggestionResponse] = []
        seen: set[tuple[str, str, str]] = set()
        for anomaly in anomalies:
            if anomaly.type == "high_low_score_rate":
                suggestion_type = "broaden_logic"
                dimension_key = MatchService._quality_dimension_for_segment(anomaly.segment_type)
                action = "Review whether this segment is over-filtered; consider broadening logic or creating a scoped rule."
            elif anomaly.type == "high_score_low_conversion":
                suggestion_type = "narrow_logic"
                dimension_key = "skill"
                action = "Inspect high-scoring low-conversion samples; narrow overly broad skill or intention matches if confirmed."
            else:
                suggestion_type = "review_dimension"
                dimension_key = MatchService._quality_dimension_for_segment(anomaly.segment_type)
                action = "Review the segment's dimension snapshots before changing weights."

            key = (suggestion_type, dimension_key, anomaly.segment_label)
            if key in seen:
                continue
            seen.add(key)
            suggestions.append(
                MatchQualityTuningSuggestionResponse(
                    suggestion_type=suggestion_type,
                    dimension_key=dimension_key,
                    priority=anomaly.severity,
                    affected_segment=anomaly.segment_label,
                    evidence=anomaly.evidence,
                    proposed_action=action,
                    confidence="medium" if anomaly.sample_status == "limited" else anomaly.severity,
                    guardrail=QUALITY_GUARDRAIL,
                )
            )
        return suggestions[:12]

    @staticmethod
    def _quality_dimension_for_segment(segment_type: str) -> str:
        if segment_type == "city":
            return "city"
        if segment_type in {"position_category", "standard_position", "job_tag"}:
            return "skill"
        if segment_type == "experiment_bucket":
            return "experiment"
        return "rule_config"

    @staticmethod
    async def _get_active_rule_config(db: AsyncSession, scope: str = "global") -> MatchRuleConfig:
        await MatchService._ensure_default_rule_config(db)
        db_config = await MatchRuleConfigRepository.get_active_by_scope(db, scope=scope)
        if db_config is None:
            return MatchRuleConfigService.get_default_config()
        try:
            return MatchRuleConfigService.from_model(db_config)
        except ValueError:
            return MatchRuleConfigService.get_default_config()

    @staticmethod
    async def _select_rule_config(db: AsyncSession, *, seeker: User, job: Job) -> dict[str, Any]:
        await MatchService._ensure_default_rule_config(db)
        for scope in [f"job_id:{job.id}", "global"]:
            experiment = await MatchRuleConfigRepository.get_running_experiment(db, scope=scope, template_key="default")
            if experiment is not None:
                bucket = MatchService._experiment_bucket(experiment, seeker_id=seeker.id, job_id=job.id)
                config_id = experiment.treatment_config_id if bucket == "treatment" else experiment.control_config_id
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

            db_config = await MatchRuleConfigRepository.get_active_by_scope(db, scope=scope, template_key="default")
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
    def _experiment_bucket(experiment: MatchRuleExperimentModel, *, seeker_id: int, job_id: int) -> str:
        if experiment.traffic_percent <= 0:
            return "control"
        if experiment.traffic_percent >= 100:
            return "treatment"
        digest = hashlib.sha256(f"{experiment.id}:{seeker_id}:{job_id}".encode("utf-8")).hexdigest()
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
    ) -> MatchRuleMatchAuditModel:
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
            dimension_scores=[
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
            ],
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
        existing = await MatchRuleConfigRepository.get_active_by_scope(db, scope="global")
        if existing is not None:
            return existing
        return await MatchRuleConfigRepository.create_default(db, DEFAULT_RULE_DIMENSIONS)

    @staticmethod
    def _score_skill(job: Job, resume_skills: list[Any]) -> MatchDimensionResponse:
        candidate_skills = MatchService._normalize_terms([skill.skill_name for skill in resume_skills])
        job_skills = MatchService._job_skill_terms(job)
        if not job_skills:
            return MatchService._dimension(
                "skill",
                70 if candidate_skills else 50,
                matched=[],
                missing=[],
                explanation="岗位暂未识别出明确技能要求，技能维度按中性分处理。",
            )

        matched = [skill for skill in job_skills if skill.lower() in {item.lower() for item in candidate_skills}]
        missing = [skill for skill in job_skills if skill not in matched]
        ratio = len(matched) / len(job_skills)
        score = 40 + ratio * 60
        if not candidate_skills:
            score = 35
        return MatchService._dimension(
            "skill",
            score,
            matched=[f"技能命中 {item}" for item in matched],
            missing=[f"岗位要求 {item}，简历中未识别到" for item in missing[:5]],
            explanation="根据岗位标签、任职要求和简历技能做规则匹配。",
        )

    @staticmethod
    def _score_experience(job: Job, work_years: float | None) -> MatchDimensionResponse:
        required_years = MatchService._parse_required_years(job.experience)
        if required_years is None:
            return MatchService._dimension(
                "experience",
                80,
                matched=["岗位不限经验"],
                explanation="岗位未设置明确年限要求。",
            )
        if work_years is None:
            return MatchService._dimension(
                "experience",
                50,
                missing=[f"岗位要求约 {required_years:g} 年经验，简历未识别到工作年限"],
                explanation="简历缺少工作年限，经验维度按保守分处理。",
            )

        if work_years >= required_years:
            score = 100
            matched = [f"工作年限 {work_years:g} 年，满足岗位要求 {required_years:g} 年"]
            missing = []
        else:
            gap = required_years - work_years
            score = 75 if gap <= 1 else 55 if gap <= 3 else 35
            matched = []
            missing = [f"工作年限 {work_years:g} 年，低于岗位要求 {required_years:g} 年"]
        return MatchService._dimension(
            "experience",
            score,
            matched=matched,
            missing=missing,
            explanation="根据岗位经验要求和简历工作年限计算。",
        )

    @staticmethod
    def _score_education(job: Job, candidate_education: str | None) -> MatchDimensionResponse:
        required_rank = MatchService._education_rank(job.education)
        if required_rank == 0:
            return MatchService._dimension(
                "education",
                80,
                matched=["岗位不限学历"],
                explanation="岗位未设置明确学历门槛。",
            )
        candidate_rank = MatchService._education_rank(candidate_education)
        if candidate_rank == 0:
            return MatchService._dimension(
                "education",
                50,
                missing=[f"岗位要求 {job.education}，简历未识别到最高学历"],
                explanation="简历缺少最高学历，学历维度按保守分处理。",
            )
        if candidate_rank >= required_rank:
            return MatchService._dimension(
                "education",
                100,
                matched=[f"最高学历 {candidate_education}，满足岗位要求 {job.education}"],
                explanation="候选人学历满足或高于岗位要求。",
            )
        return MatchService._dimension(
            "education",
            70 if required_rank - candidate_rank == 1 else 45,
            missing=[f"最高学历 {candidate_education}，低于岗位要求 {job.education}"],
            explanation="候选人学历低于岗位要求。",
        )

    @staticmethod
    def _score_city(job: Job, current_city: str | None) -> MatchDimensionResponse:
        if not current_city:
            return MatchService._dimension(
                "city",
                50,
                missing=[f"岗位城市为 {job.city}，简历未填写当前城市"],
                explanation="简历缺少当前城市，城市维度按保守分处理。",
            )
        if MatchService._contains_same_term(current_city, job.city):
            return MatchService._dimension(
                "city",
                100,
                matched=[f"当前城市与岗位城市一致：{job.city}"],
                explanation="当前城市与岗位城市一致。",
            )
        return MatchService._dimension(
            "city",
            40,
            missing=[f"当前城市 {current_city} 与岗位城市 {job.city} 不一致"],
            explanation="当前城市和岗位城市不一致。",
        )

    @staticmethod
    def _score_salary(job: Job, expected_salary: str | None) -> MatchDimensionResponse:
        expected_range = MatchService._parse_salary_range(expected_salary)
        if expected_range is None:
            return MatchService._dimension(
                "salary",
                60,
                missing=["简历未填写期望薪资"],
                explanation="缺少期望薪资，薪资维度按中性分处理。",
            )
        expected_min, expected_max = expected_range
        overlaps = expected_min <= job.salary_max and expected_max >= job.salary_min
        if overlaps:
            return MatchService._dimension(
                "salary",
                100,
                matched=[f"期望薪资 {expected_min:g}-{expected_max:g}K 与岗位 {job.salary_min}-{job.salary_max}K 有重叠"],
                explanation="期望薪资与岗位薪资区间有重叠。",
            )
        return MatchService._dimension(
            "salary",
            50,
            missing=[f"期望薪资 {expected_min:g}-{expected_max:g}K 与岗位 {job.salary_min}-{job.salary_max}K 不重叠"],
            explanation="期望薪资与岗位薪资区间不重叠。",
        )

    @staticmethod
    def _score_intention(job: Job, target_position: str | None) -> MatchDimensionResponse:
        if not target_position:
            return MatchService._dimension(
                "intention",
                50,
                missing=["简历未填写目标岗位"],
                explanation="缺少目标岗位，岗位意向维度按保守分处理。",
            )
        title_terms = MatchService._tokenize(job.title)
        target_terms = MatchService._tokenize(target_position)
        overlap = title_terms & target_terms
        if MatchService._contains_same_term(job.title, target_position) or len(overlap) >= 2:
            score = 100
        elif overlap:
            score = 75
        else:
            score = 30
        return MatchService._dimension(
            "intention",
            score,
            matched=[f"岗位意向命中 {item}" for item in sorted(overlap)] if overlap else [],
            missing=[] if overlap else [f"目标岗位 {target_position} 与岗位 {job.title} 相关度较低"],
            explanation="根据岗位标题和求职目标的关键词重合度计算。",
        )

    @staticmethod
    def _overall_score(dimensions: list[MatchDimensionResponse]) -> int:
        return round(sum(item.weighted_score for item in dimensions))

    @staticmethod
    def _level_and_recommendation(score: int) -> tuple[str, str]:
        if score >= 80:
            return "high", "建议投递"
        if score >= 60:
            return "medium", "可尝试投递"
        return "low", "谨慎投递"

    @staticmethod
    def _summary(score: int, highlights: list[str], gaps: list[str]) -> str:
        if score >= 80:
            return "你的画像与该岗位匹配度较高，建议优先投递。"
        if score >= 60:
            return "你的画像与该岗位有一定匹配度，可结合缺口项判断是否投递。"
        if gaps:
            return "当前画像与该岗位存在明显缺口，建议补充相关经历后再投递。"
        return "当前信息不足，建议先完善简历画像后再查看匹配结果。"

    @staticmethod
    def _build_highlights(dimensions: list[MatchDimensionResponse]) -> list[str]:
        highlights: list[str] = []
        for dimension in dimensions:
            if dimension.score >= 80:
                highlights.extend(dimension.matched[:2])
        return highlights[:6]

    @staticmethod
    def _build_gaps(dimensions: list[MatchDimensionResponse]) -> list[str]:
        gaps: list[str] = []
        for dimension in dimensions:
            if dimension.score < 80:
                gaps.extend(dimension.missing[:2])
        return gaps[:6]

    @staticmethod
    def _job_skill_terms(job: Job) -> list[str]:
        terms: list[str] = []
        if isinstance(job.tags, list):
            terms.extend(str(tag) for tag in job.tags)
        source_text = " ".join([job.title or "", job.description or "", job.requirement or ""])
        for skill in KNOWN_SKILLS:
            if re.search(rf"(?<![A-Za-z0-9]){re.escape(skill)}(?![A-Za-z0-9])", source_text, flags=re.IGNORECASE):
                terms.append(skill)
        return MatchService._normalize_terms(terms)

    @staticmethod
    def _normalize_terms(values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for value in values:
            item = str(value).strip()
            if item and item.lower() not in {existing.lower() for existing in cleaned}:
                cleaned.append(item)
        return cleaned

    @staticmethod
    def _parse_required_years(value: str | None) -> float | None:
        if not value or "不限" in value:
            return None
        match = re.search(r"(\d+(?:\.\d+)?)\s*(?:年|年以上|\+)", value)
        return float(match.group(1)) if match else None

    @staticmethod
    def _education_rank(value: str | None) -> int:
        if not value:
            return 0
        for label, rank in EDUCATION_RANKS.items():
            if label in value:
                return rank
        return 0

    @staticmethod
    def _parse_salary_range(value: str | None) -> tuple[float, float] | None:
        if not value:
            return None
        numbers = [float(item) for item in re.findall(r"\d+(?:\.\d+)?", value)]
        if not numbers:
            return None
        if len(numbers) == 1:
            return numbers[0], numbers[0]
        return min(numbers[0], numbers[1]), max(numbers[0], numbers[1])

    @staticmethod
    def _contains_same_term(left: str | None, right: str | None) -> bool:
        if not left or not right:
            return False
        left_text = left.strip().lower()
        right_text = right.strip().lower()
        return left_text in right_text or right_text in left_text

    @staticmethod
    def _tokenize(value: str | None) -> set[str]:
        if not value:
            return set()
        ascii_terms = set(re.findall(r"[A-Za-z][A-Za-z0-9+#.]*", value.lower()))
        chinese_terms = set(re.findall(r"[\u4e00-\u9fa5]{2,}", value))
        return ascii_terms | chinese_terms
