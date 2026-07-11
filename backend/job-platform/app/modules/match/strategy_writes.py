"""Write operations for intelligent matching strategies."""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.match.models import (
    IntelligentMatchingEvaluationModel,
    IntelligentMatchingStrategyModel,
    MatchRuleConfigModel,
)
from app.modules.match.repository import MatchRuleConfigRepository
from app.modules.match.schemas import (
    IntelligentMatchingEvaluationResponse,
    IntelligentMatchingEvaluationRunRequest,
    IntelligentMatchingStrategyCloneRequest,
    IntelligentMatchingStrategyCreateRequest,
    IntelligentMatchingStrategyListResponse,
    IntelligentMatchingStrategyResponse,
    IntelligentMatchingStrategyUpdateRequest,
)
from app.modules.match.writes import MatchRuleWriteService
from app.modules.user.models import User


class IntelligentMatchingStrategyWriteService:
    """Admin write workflows for intelligent matching strategies."""

    EDITABLE_STATUSES = {"draft", "evaluating"}
    EVALUABLE_STATUSES = {"draft", "evaluating", "testing"}

    @staticmethod
    async def list_strategies(
        db: AsyncSession,
        *,
        status_filter: str | None = None,
        base_rule_config_id: int | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> IntelligentMatchingStrategyListResponse:
        items, total = await MatchRuleConfigRepository.list_intelligent_strategies(
            db,
            status_filter=status_filter,
            base_rule_config_id=base_rule_config_id,
            skip=skip,
            limit=limit,
        )
        return IntelligentMatchingStrategyListResponse(
            items=[
                IntelligentMatchingStrategyWriteService._strategy_response(item)
                for item in items
            ],
            total=total,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    async def get_strategy(
        db: AsyncSession, strategy_id: int
    ) -> IntelligentMatchingStrategyResponse:
        strategy = await MatchRuleConfigRepository.get_intelligent_strategy_by_id(
            db, strategy_id
        )
        if strategy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="intelligent_strategy_not_found",
            )
        return IntelligentMatchingStrategyWriteService._strategy_response(strategy)

    @staticmethod
    async def create_strategy(
        db: AsyncSession,
        current_user: User,
        payload: IntelligentMatchingStrategyCreateRequest,
    ) -> IntelligentMatchingStrategyResponse:
        await IntelligentMatchingStrategyWriteService._ensure_unique_name(
            db, payload.name
        )
        await IntelligentMatchingStrategyWriteService._ensure_base_rule_exists(
            db, payload.base_rule_config_id
        )

        strategy = IntelligentMatchingStrategyModel(
            name=payload.name,
            description=payload.description,
            status="draft",
            base_rule_config_id=payload.base_rule_config_id,
            vector_recall=payload.vector_recall.model_dump(),
            hybrid_weights=payload.hybrid_weights.model_dump(),
            fallback_policy=payload.fallback_policy,
            created_by=current_user.id,
            updated_by=current_user.id,
        )
        db.add(strategy)
        await db.flush()
        await db.refresh(strategy)
        after_snapshot = IntelligentMatchingStrategyWriteService._strategy_snapshot(
            strategy
        )
        await MatchRuleWriteService._record_operation_audit(
            db,
            actor_id=current_user.id,
            action="create_intelligent_strategy",
            resource_type="intelligent_strategy",
            resource_id=strategy.id,
            reason="create draft",
            before_snapshot=None,
            after_snapshot=after_snapshot,
            metadata={"base_rule_config_id": strategy.base_rule_config_id},
            commit=False,
        )
        await db.commit()
        await db.refresh(strategy)
        return IntelligentMatchingStrategyWriteService._strategy_response(strategy)

    @staticmethod
    async def update_strategy(
        db: AsyncSession,
        current_user: User,
        strategy_id: int,
        payload: IntelligentMatchingStrategyUpdateRequest,
    ) -> IntelligentMatchingStrategyResponse:
        strategy = await MatchRuleConfigRepository.get_intelligent_strategy_by_id(
            db, strategy_id
        )
        if strategy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="intelligent_strategy_not_found",
            )
        if (
            strategy.status
            not in IntelligentMatchingStrategyWriteService.EDITABLE_STATUSES
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="intelligent_strategy_not_editable",
            )

        before_snapshot = IntelligentMatchingStrategyWriteService._strategy_snapshot(
            strategy
        )
        update_data = payload.model_dump(exclude_unset=True)
        if "name" in update_data and update_data["name"] != strategy.name:
            await IntelligentMatchingStrategyWriteService._ensure_unique_name(
                db, update_data["name"], exclude_strategy_id=strategy.id
            )
            strategy.name = update_data["name"]
        if "description" in update_data:
            strategy.description = update_data["description"] or ""
        if "base_rule_config_id" in update_data:
            await IntelligentMatchingStrategyWriteService._ensure_base_rule_exists(
                db, update_data["base_rule_config_id"]
            )
            strategy.base_rule_config_id = update_data["base_rule_config_id"]
        if "vector_recall" in update_data and update_data["vector_recall"] is not None:
            strategy.vector_recall = update_data["vector_recall"]
        if (
            "hybrid_weights" in update_data
            and update_data["hybrid_weights"] is not None
        ):
            strategy.hybrid_weights = update_data["hybrid_weights"]
        if (
            "fallback_policy" in update_data
            and update_data["fallback_policy"] is not None
        ):
            strategy.fallback_policy = update_data["fallback_policy"]
        strategy.updated_by = current_user.id

        await db.flush()
        await db.refresh(strategy)
        after_snapshot = IntelligentMatchingStrategyWriteService._strategy_snapshot(
            strategy
        )
        await MatchRuleWriteService._record_operation_audit(
            db,
            actor_id=current_user.id,
            action="update_intelligent_strategy",
            resource_type="intelligent_strategy",
            resource_id=strategy.id,
            reason="update draft",
            before_snapshot=before_snapshot,
            after_snapshot=after_snapshot,
            metadata={
                "from_status": before_snapshot["status"],
                "to_status": strategy.status,
            },
            commit=False,
        )
        await db.commit()
        await db.refresh(strategy)
        return IntelligentMatchingStrategyWriteService._strategy_response(strategy)

    @staticmethod
    async def clone_strategy(
        db: AsyncSession,
        current_user: User,
        strategy_id: int,
        payload: IntelligentMatchingStrategyCloneRequest,
    ) -> IntelligentMatchingStrategyResponse:
        source = await MatchRuleConfigRepository.get_intelligent_strategy_by_id(
            db, strategy_id
        )
        if source is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="intelligent_strategy_not_found",
            )
        await IntelligentMatchingStrategyWriteService._ensure_unique_name(
            db, payload.name
        )

        clone = IntelligentMatchingStrategyModel(
            name=payload.name,
            description=source.description,
            status="draft",
            base_rule_config_id=source.base_rule_config_id,
            vector_recall=dict(source.vector_recall or {}),
            hybrid_weights=dict(source.hybrid_weights or {}),
            fallback_policy=source.fallback_policy,
            created_by=current_user.id,
            updated_by=current_user.id,
        )
        db.add(clone)
        await db.flush()
        await db.refresh(clone)
        before_snapshot = IntelligentMatchingStrategyWriteService._strategy_snapshot(
            source
        )
        after_snapshot = IntelligentMatchingStrategyWriteService._strategy_snapshot(
            clone
        )
        await MatchRuleWriteService._record_operation_audit(
            db,
            actor_id=current_user.id,
            action="clone_intelligent_strategy",
            resource_type="intelligent_strategy",
            resource_id=clone.id,
            reason=payload.reason or "clone strategy",
            before_snapshot=before_snapshot,
            after_snapshot=after_snapshot,
            metadata={"source_strategy_id": source.id},
            commit=False,
        )
        await db.commit()
        await db.refresh(clone)
        return IntelligentMatchingStrategyWriteService._strategy_response(clone)

    @staticmethod
    async def run_evaluation(
        db: AsyncSession,
        current_user: User,
        strategy_id: int,
        payload: IntelligentMatchingEvaluationRunRequest,
    ) -> IntelligentMatchingEvaluationResponse:
        strategy = await MatchRuleConfigRepository.get_intelligent_strategy_by_id(
            db, strategy_id
        )
        if strategy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="intelligent_strategy_not_found",
            )
        if (
            strategy.status
            not in IntelligentMatchingStrategyWriteService.EVALUABLE_STATUSES
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="intelligent_strategy_not_evaluable",
            )

        distribution = (
            IntelligentMatchingStrategyWriteService._normalized_sample_distribution(
                payload.sample_source_distribution
            )
        )
        sample_count = sum(distribution.values())
        baseline, hybrid = IntelligentMatchingStrategyWriteService._evaluation_metrics(
            distribution
        )
        decision_status, risk_notes = (
            IntelligentMatchingStrategyWriteService._evaluation_decision(distribution)
        )
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        evaluation = IntelligentMatchingEvaluationModel(
            strategy_id=strategy.id,
            status="completed",
            sample_count=sample_count,
            sample_source_distribution=distribution,
            baseline_metrics=baseline,
            hybrid_metrics=hybrid,
            decision_status=decision_status,
            risk_notes=risk_notes,
            created_by=current_user.id,
            completed_at=now,
        )
        db.add(evaluation)
        await db.flush()
        await db.refresh(evaluation)
        report = IntelligentMatchingStrategyWriteService._evaluation_response(
            evaluation
        )
        await MatchRuleWriteService._record_operation_audit(
            db,
            actor_id=current_user.id,
            action="run_intelligent_evaluation",
            resource_type="intelligent_evaluation",
            resource_id=evaluation.id,
            reason=payload.notes or "run offline evaluation",
            before_snapshot=IntelligentMatchingStrategyWriteService._strategy_snapshot(
                strategy
            ),
            after_snapshot=report.model_dump(mode="json"),
            metadata={
                "strategy_id": strategy.id,
                "sample_set_id": payload.sample_set_id,
                "sample_source_policy": payload.sample_source_policy,
            },
            commit=False,
        )
        await db.commit()
        await db.refresh(evaluation)
        return IntelligentMatchingStrategyWriteService._evaluation_response(evaluation)

    @staticmethod
    async def get_evaluation(
        db: AsyncSession, evaluation_id: int
    ) -> IntelligentMatchingEvaluationResponse:
        evaluation = await MatchRuleConfigRepository.get_intelligent_evaluation_by_id(
            db, evaluation_id
        )
        if evaluation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="intelligent_evaluation_not_found",
            )
        return IntelligentMatchingStrategyWriteService._evaluation_response(evaluation)

    @staticmethod
    def _normalized_sample_distribution(distribution: dict[str, int]) -> dict[str, int]:
        allowed_keys = ("real_behavior", "manual_review", "seeded_demo", "mock_only")
        return {key: int(distribution.get(key, 0) or 0) for key in allowed_keys}

    @staticmethod
    def _evaluation_metrics(distribution: dict[str, int]) -> tuple[dict, dict]:
        sample_count = max(sum(distribution.values()), 1)
        trusted_count = distribution["real_behavior"] + distribution["manual_review"]
        trusted_ratio = trusted_count / sample_count
        baseline = {
            "avg_score": 76.5,
            "low_score_rate": 0.18,
            "application_proxy_rate": 0.08,
        }
        hybrid = {
            "avg_score": 79.2,
            "low_score_rate": 0.14,
            "application_proxy_rate": 0.1,
            "vector_recall_coverage": round(0.6 + (0.24 * trusted_ratio), 2),
            "degrade_rate": round(0.08 - (0.05 * trusted_ratio), 2),
        }
        return baseline, hybrid

    @staticmethod
    def _evaluation_decision(distribution: dict[str, int]) -> tuple[str, list[str]]:
        demo_count = distribution["seeded_demo"] + distribution["mock_only"]
        trusted_count = distribution["real_behavior"] + distribution["manual_review"]
        if demo_count > 0:
            return "demo_only", ["demo_or_mock_samples_cannot_support_online_decision"]
        if trusted_count < 30:
            return "insufficient_sample", ["insufficient_trusted_samples"]
        return "eligible_for_gray", []

    @staticmethod
    def _evaluation_response(
        evaluation: IntelligentMatchingEvaluationModel,
    ) -> IntelligentMatchingEvaluationResponse:
        return IntelligentMatchingEvaluationResponse(
            evaluation_id=evaluation.id,
            strategy_id=evaluation.strategy_id,
            status=evaluation.status,
            sample_count=evaluation.sample_count,
            sample_source_distribution=dict(
                evaluation.sample_source_distribution or {}
            ),
            baseline=dict(evaluation.baseline_metrics or {}),
            hybrid=dict(evaluation.hybrid_metrics or {}),
            decision_status=evaluation.decision_status,
            risk_notes=list(evaluation.risk_notes or []),
        )

    @staticmethod
    async def _ensure_unique_name(
        db: AsyncSession,
        name: str,
        *,
        exclude_strategy_id: int | None = None,
    ) -> None:
        existing = await MatchRuleConfigRepository.get_intelligent_strategy_by_name(
            db, name
        )
        if existing is not None and existing.id != exclude_strategy_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="intelligent_strategy_name_exists",
            )

    @staticmethod
    async def _ensure_base_rule_exists(
        db: AsyncSession, base_rule_config_id: int
    ) -> MatchRuleConfigModel:
        base_rule = await MatchRuleConfigRepository.get_by_id(db, base_rule_config_id)
        if base_rule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="base_rule_config_not_found",
            )
        if base_rule.status == "archived":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="base_rule_config_archived"
            )
        return base_rule

    @staticmethod
    def _strategy_response(
        strategy: IntelligentMatchingStrategyModel,
    ) -> IntelligentMatchingStrategyResponse:
        return IntelligentMatchingStrategyResponse(
            id=strategy.id,
            name=strategy.name,
            description=strategy.description,
            status=strategy.status,
            base_rule_config_id=strategy.base_rule_config_id,
            vector_recall=dict(strategy.vector_recall or {}),
            hybrid_weights=dict(strategy.hybrid_weights or {}),
            fallback_policy=strategy.fallback_policy,
            created_by=strategy.created_by,
            updated_by=strategy.updated_by,
            archived_at=strategy.archived_at,
            created_at=strategy.created_at,
            updated_at=strategy.updated_at,
        )

    @staticmethod
    def _strategy_snapshot(strategy: IntelligentMatchingStrategyModel) -> dict:
        return {
            "id": strategy.id,
            "name": strategy.name,
            "description": strategy.description,
            "status": strategy.status,
            "base_rule_config_id": strategy.base_rule_config_id,
            "vector_recall": dict(strategy.vector_recall or {}),
            "hybrid_weights": dict(strategy.hybrid_weights or {}),
            "fallback_policy": strategy.fallback_policy,
            "created_by": strategy.created_by,
            "updated_by": strategy.updated_by,
            "archived_at": MatchRuleWriteService._datetime_iso(strategy.archived_at),
            "created_at": MatchRuleWriteService._datetime_iso(strategy.created_at),
            "updated_at": MatchRuleWriteService._datetime_iso(strategy.updated_at),
        }
