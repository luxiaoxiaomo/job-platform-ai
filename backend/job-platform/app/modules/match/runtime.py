"""Runtime intelligent matching orchestration."""

from dataclasses import replace
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.application.models import JobApplication
from app.modules.job.models import Job, JobFavorite, JobVisit
from app.modules.match.config import MatchRuleConfig
from app.modules.match.models import IntelligentMatchingStrategyModel
from app.modules.match.repository import MatchRuleConfigRepository
from app.modules.match.scoring import (
    HybridScoreWeights,
    IntelligentScoreInput,
    IntelligentScoringConfig,
    IntelligentScoringService,
    ThreeDimensionalWeights,
)
from app.modules.match.vector import VectorRecallResult, resolve_vector_recall_provider
from app.modules.user.models import User


class IntelligentMatchRuntime:
    """Resolve an active strategy and calculate its runtime preview."""

    @staticmethod
    async def active_strategy(
        db: AsyncSession, rule_config: MatchRuleConfig
    ) -> IntelligentMatchingStrategyModel | None:
        base_rule_config_id = (
            rule_config.id if isinstance(rule_config.id, int) else None
        )
        strategy = await MatchRuleConfigRepository.get_active_intelligent_strategy(
            db, base_rule_config_id=base_rule_config_id
        )
        if strategy is not None or base_rule_config_id is not None:
            return strategy
        return await MatchRuleConfigRepository.get_active_intelligent_strategy(db)

    @classmethod
    async def preview_score(
        cls,
        db: AsyncSession,
        *,
        seeker: User,
        job: Job,
        detail: Any,
        baseline_rule_score: int,
        strategy: IntelligentMatchingStrategyModel,
    ):
        weights = dict(strategy.hybrid_weights or {})
        vector_recall = dict(strategy.vector_recall or {})
        vector_weight = cls.float_weight(weights.get("vector_score"), 0)
        vector_result = cls.vector_recall_result(
            job=job,
            detail=detail,
            vector_recall=vector_recall,
            vector_enabled=bool(vector_recall.get("enabled")),
            vector_weight=vector_weight,
        )
        preview = IntelligentScoringService.preview_score(
            IntelligentScoreInput(
                semantic_score=vector_result.semantic_score,
                tag_score=baseline_rule_score,
                keyword_score=None,
                profile_coverage_score=cls.profile_coverage_score(detail),
                behavior_quality_score=await cls.behavior_quality_score(
                    db, job_id=job.id, seeker_id=seeker.id
                ),
                baseline_rule_score=baseline_rule_score,
                vector_degrade_reason=vector_result.degrade_reason,
                recall_source=vector_result.recall_source,
            ),
            config=cls.scoring_config(weights),
        )
        return replace(preview, vector_metadata=vector_result.as_audit_metadata())

    @staticmethod
    def vector_recall_result(
        *,
        job: Job,
        detail: Any,
        vector_recall: dict[str, Any],
        vector_enabled: bool,
        vector_weight: float,
    ) -> VectorRecallResult:
        if not vector_enabled or vector_weight <= 0:
            return VectorRecallResult(semantic_score=None, recall_source="rule_only")
        provider = resolve_vector_recall_provider(vector_recall)
        if provider is None:
            return VectorRecallResult(
                semantic_score=None,
                recall_source="rule_only",
                degrade_reason="vector_store_unavailable",
                provider=str(vector_recall.get("provider") or "unconfigured"),
            )
        return provider.score(job=job, detail=detail, config=vector_recall)

    @classmethod
    def scoring_config(cls, weights: dict[str, Any]) -> IntelligentScoringConfig:
        rule_weight = cls.float_weight(weights.get("rule_score"), 0.7)
        vector_weight = cls.float_weight(weights.get("vector_score"), 0.2)
        profile_weight = cls.float_weight(weights.get("profile_coverage_score"), 0.1)
        behavior_weight = cls.float_weight(weights.get("behavior_quality_score"), 0)
        base_weight = rule_weight + vector_weight
        return IntelligentScoringConfig(
            three_dimensional_weights=ThreeDimensionalWeights(
                semantic_score=vector_weight / base_weight if base_weight > 0 else 0,
                tag_score=rule_weight / base_weight if base_weight > 0 else 1,
                keyword_score=0,
            ),
            final_weights=HybridScoreWeights(
                base_match_score=base_weight,
                profile_coverage_score=profile_weight,
                behavior_quality_score=behavior_weight,
            ),
        )

    @staticmethod
    def overall_score(preview, baseline_rule_score: int) -> int:
        if preview is None or preview.score_components.final_match_score is None:
            return baseline_rule_score
        return max(
            0, min(100, round(float(preview.score_components.final_match_score)))
        )

    @classmethod
    def profile_coverage_score(cls, detail: Any) -> int:
        basic = detail.basic_info
        values = [
            basic.highest_education if basic else None,
            basic.work_years if basic else None,
            basic.current_city if basic else None,
            basic.target_position if basic else None,
            basic.expected_salary if basic else None,
            detail.skills,
        ]
        return (
            round(
                sum(1 for value in values if cls.has_value(value)) / len(values) * 100
            )
            if values
            else 0
        )

    @staticmethod
    async def behavior_quality_score(
        db: AsyncSession, *, job_id: int, seeker_id: int
    ) -> int | None:
        application_status = (
            await db.execute(
                select(JobApplication.status)
                .where(
                    JobApplication.job_id == job_id,
                    JobApplication.seeker_id == seeker_id,
                )
                .limit(1)
            )
        ).scalar_one_or_none()
        if application_status is not None:
            return {
                "hired": 100,
                "interview_invited": 95,
                "viewed": 90,
                "submitted": 88,
                "rejected": 55,
            }.get(str(application_status), 88)
        favorite_id = (
            await db.execute(
                select(JobFavorite.id)
                .where(JobFavorite.job_id == job_id, JobFavorite.seeker_id == seeker_id)
                .limit(1)
            )
        ).scalar_one_or_none()
        if favorite_id is not None:
            return 85
        visit_id = (
            await db.execute(
                select(JobVisit.id)
                .where(JobVisit.job_id == job_id, JobVisit.seeker_id == seeker_id)
                .limit(1)
            )
        ).scalar_one_or_none()
        return 70 if visit_id is not None else None

    @staticmethod
    def audit_snapshot(preview, overall_score: int) -> dict[str, Any] | None:
        if preview is None:
            return None
        return {
            "key": "intelligent_scoring",
            "label": "Intelligent scoring",
            "score": overall_score,
            "configured_weight": 100,
            "effective_weight": 100,
            "weighted_score": overall_score,
            "matched": [],
            "missing": [],
            "explanation": "Runtime hybrid scoring snapshot.",
            "match_source": preview.match_source,
            "recall_source": preview.recall_source,
            "degrade_reason": preview.degrade_reason,
            "score_components": preview.score_components.as_dict(),
            "actual_component_weights": preview.actual_component_weights,
            "configured_weights": preview.configured_weights,
            "hard_constraint_result": preview.hard_constraint_result.as_dict(),
            "explanation_codes": preview.explanation_codes,
            "weight_redistribution_reason": preview.weight_redistribution_reason,
            "vector_metadata": preview.vector_metadata,
        }

    @staticmethod
    def has_value(value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (list, tuple, set, dict)):
            return bool(value)
        return True

    @staticmethod
    def float_weight(value: Any, default: float) -> float:
        return default if value is None else float(value)
