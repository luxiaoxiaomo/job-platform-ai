"""
Match rule configuration repository.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.job.models import Job
from app.modules.match.models import (
    IntelligentMatchingEvaluationModel,
    IntelligentMatchingStrategyModel,
    MatchRuleConfigModel,
    MatchRuleDimensionModel,
    MatchRuleExperimentModel,
    MatchRuleMatchAuditModel,
    MatchRuleOperationAuditModel,
)


class MatchRuleConfigRepository:
    """Database access for match rule configs."""

    @staticmethod
    async def list_configs(
        db: AsyncSession,
        *,
        scope: str | None = None,
        template_key: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[MatchRuleConfigModel], int]:
        filters = []
        if scope:
            filters.append(MatchRuleConfigModel.scope == scope)
        if template_key:
            filters.append(MatchRuleConfigModel.template_key == template_key)

        total_query = select(func.count()).select_from(MatchRuleConfigModel)
        if filters:
            total_query = total_query.where(*filters)
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()

        query = (
            select(MatchRuleConfigModel)
            .options(selectinload(MatchRuleConfigModel.dimensions))
            .order_by(MatchRuleConfigModel.scope.asc(), MatchRuleConfigModel.template_key.asc(), MatchRuleConfigModel.version.desc())
            .offset(skip)
            .limit(limit)
        )
        if filters:
            query = query.where(*filters)
        result = await db.execute(query)
        return list(result.scalars().all()), total

    @staticmethod
    async def get_by_id(db: AsyncSession, config_id: int) -> Optional[MatchRuleConfigModel]:
        result = await db.execute(
            select(MatchRuleConfigModel)
            .options(selectinload(MatchRuleConfigModel.dimensions))
            .where(MatchRuleConfigModel.id == config_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_active_by_scope(
        db: AsyncSession,
        scope: str = "global",
        template_key: str = "default",
    ) -> Optional[MatchRuleConfigModel]:
        result = await db.execute(
            select(MatchRuleConfigModel)
            .options(selectinload(MatchRuleConfigModel.dimensions))
            .where(
                MatchRuleConfigModel.scope == scope,
                MatchRuleConfigModel.template_key == template_key,
                MatchRuleConfigModel.status == "active",
            )
            .order_by(MatchRuleConfigModel.version.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_active_configs(
        db: AsyncSession,
        *,
        scope: str,
        template_key: str,
        strategy: str = "rule_v1",
    ) -> list[MatchRuleConfigModel]:
        result = await db.execute(
            select(MatchRuleConfigModel)
            .options(selectinload(MatchRuleConfigModel.dimensions))
            .where(
                MatchRuleConfigModel.scope == scope,
                MatchRuleConfigModel.template_key == template_key,
                MatchRuleConfigModel.strategy == strategy,
                MatchRuleConfigModel.status == "active",
            )
            .order_by(MatchRuleConfigModel.version.desc(), MatchRuleConfigModel.id.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_history(db: AsyncSession, config: MatchRuleConfigModel) -> list[MatchRuleConfigModel]:
        result = await db.execute(
            select(MatchRuleConfigModel)
            .options(selectinload(MatchRuleConfigModel.dimensions))
            .where(
                (MatchRuleConfigModel.id == config.id)
                | (MatchRuleConfigModel.parent_version_id == config.id)
                | (
                    (MatchRuleConfigModel.scope == config.scope)
                    & (MatchRuleConfigModel.strategy == config.strategy)
                    & (MatchRuleConfigModel.template_key == config.template_key)
                )
            )
            .order_by(MatchRuleConfigModel.version.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def create(db: AsyncSession, config: MatchRuleConfigModel) -> MatchRuleConfigModel:
        db.add(config)
        await db.commit()
        created = await MatchRuleConfigRepository.get_by_id(db, config.id)
        if created is None:
            raise RuntimeError("match_rule_config_create_failed")
        return created

    @staticmethod
    async def create_default(db: AsyncSession, dimensions: list[dict]) -> MatchRuleConfigModel:
        config = MatchRuleConfigModel(
            name="默认人岗匹配规则 V1",
            strategy="rule_v1",
            scope="global",
            template_key="default",
            template_name="Default template",
            status="active",
            version=1,
            description="规则版 V1，基于技能、经验、学历、城市、薪资和岗位意向计算匹配度",
        )
        for index, item in enumerate(dimensions):
            config.dimensions.append(
                MatchRuleDimensionModel(
                    dimension_key=str(item["key"]),
                    label=str(item["label"]),
                    weight=float(item.get("weight", 0)),
                    enabled=bool(item.get("enabled", True)),
                    description=str(item.get("description") or ""),
                    scoring_method=str(item.get("scoring_method") or ""),
                    logic_json=dict(item.get("logic") or {}),
                    sort_order=int(item.get("sort_order", index + 1)),
                )
            )
        return await MatchRuleConfigRepository.create(db, config)

    @staticmethod
    async def list_experiments(
        db: AsyncSession,
        *,
        scope: str | None = None,
        template_key: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[MatchRuleExperimentModel], int]:
        filters = []
        if scope:
            filters.append(MatchRuleExperimentModel.scope == scope)
        if template_key:
            filters.append(MatchRuleExperimentModel.template_key == template_key)

        total_query = select(func.count()).select_from(MatchRuleExperimentModel)
        if filters:
            total_query = total_query.where(*filters)
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()

        query = (
            select(MatchRuleExperimentModel)
            .order_by(MatchRuleExperimentModel.updated_at.desc(), MatchRuleExperimentModel.id.desc())
            .offset(skip)
            .limit(limit)
        )
        if filters:
            query = query.where(*filters)
        result = await db.execute(query)
        return list(result.scalars().all()), total

    @staticmethod
    async def create_experiment(db: AsyncSession, experiment: MatchRuleExperimentModel) -> MatchRuleExperimentModel:
        db.add(experiment)
        await db.commit()
        await db.refresh(experiment)
        return experiment

    @staticmethod
    async def get_experiment_by_id(db: AsyncSession, experiment_id: int) -> Optional[MatchRuleExperimentModel]:
        result = await db.execute(
            select(MatchRuleExperimentModel).where(MatchRuleExperimentModel.id == experiment_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_running_experiment(
        db: AsyncSession,
        *,
        scope: str,
        template_key: str | None = None,
        exclude_experiment_id: int | None = None,
    ) -> Optional[MatchRuleExperimentModel]:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        filters = [
            MatchRuleExperimentModel.scope == scope,
            MatchRuleExperimentModel.status == "running",
            or_(MatchRuleExperimentModel.started_at.is_(None), MatchRuleExperimentModel.started_at <= now),
            or_(MatchRuleExperimentModel.ended_at.is_(None), MatchRuleExperimentModel.ended_at > now),
        ]
        if template_key:
            filters.append(MatchRuleExperimentModel.template_key == template_key)
        if exclude_experiment_id is not None:
            filters.append(MatchRuleExperimentModel.id != exclude_experiment_id)
        result = await db.execute(
            select(MatchRuleExperimentModel)
            .where(and_(*filters))
            .order_by(MatchRuleExperimentModel.updated_at.desc(), MatchRuleExperimentModel.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_intelligent_strategies(
        db: AsyncSession,
        *,
        status_filter: str | None = None,
        base_rule_config_id: int | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[IntelligentMatchingStrategyModel], int]:
        filters = []
        if status_filter is not None:
            filters.append(IntelligentMatchingStrategyModel.status == status_filter)
        if base_rule_config_id is not None:
            filters.append(IntelligentMatchingStrategyModel.base_rule_config_id == base_rule_config_id)

        total_query = select(func.count()).select_from(IntelligentMatchingStrategyModel)
        if filters:
            total_query = total_query.where(*filters)
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()

        query = (
            select(IntelligentMatchingStrategyModel)
            .order_by(IntelligentMatchingStrategyModel.updated_at.desc(), IntelligentMatchingStrategyModel.id.desc())
            .offset(skip)
            .limit(limit)
        )
        if filters:
            query = query.where(*filters)
        result = await db.execute(query)
        return list(result.scalars().all()), total

    @staticmethod
    async def get_active_intelligent_strategy(
        db: AsyncSession,
        *,
        base_rule_config_id: int | None = None,
    ) -> Optional[IntelligentMatchingStrategyModel]:
        filters = [IntelligentMatchingStrategyModel.status == "active"]
        if base_rule_config_id is not None:
            filters.append(IntelligentMatchingStrategyModel.base_rule_config_id == base_rule_config_id)
        result = await db.execute(
            select(IntelligentMatchingStrategyModel)
            .where(*filters)
            .order_by(IntelligentMatchingStrategyModel.updated_at.desc(), IntelligentMatchingStrategyModel.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_intelligent_strategy_by_id(
        db: AsyncSession,
        strategy_id: int,
    ) -> Optional[IntelligentMatchingStrategyModel]:
        result = await db.execute(
            select(IntelligentMatchingStrategyModel).where(IntelligentMatchingStrategyModel.id == strategy_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_intelligent_strategy_by_name(
        db: AsyncSession,
        name: str,
    ) -> Optional[IntelligentMatchingStrategyModel]:
        result = await db.execute(
            select(IntelligentMatchingStrategyModel).where(IntelligentMatchingStrategyModel.name == name)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_intelligent_evaluation_by_id(
        db: AsyncSession,
        evaluation_id: int,
    ) -> Optional[IntelligentMatchingEvaluationModel]:
        result = await db.execute(
            select(IntelligentMatchingEvaluationModel).where(IntelligentMatchingEvaluationModel.id == evaluation_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_operation_audit(
        db: AsyncSession,
        audit: MatchRuleOperationAuditModel,
        *,
        commit: bool = True,
    ) -> MatchRuleOperationAuditModel:
        db.add(audit)
        if commit:
            await db.commit()
            await db.refresh(audit)
        return audit

    @staticmethod
    async def list_operation_audits(
        db: AsyncSession,
        *,
        resource_type: str | None = None,
        resource_id: int | None = None,
        action: str | None = None,
        actor_id: int | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[MatchRuleOperationAuditModel], int]:
        filters = []
        if resource_type is not None:
            filters.append(MatchRuleOperationAuditModel.resource_type == resource_type)
        if resource_id is not None:
            filters.append(MatchRuleOperationAuditModel.resource_id == resource_id)
        if action is not None:
            filters.append(MatchRuleOperationAuditModel.action == action)
        if actor_id is not None:
            filters.append(MatchRuleOperationAuditModel.actor_id == actor_id)

        total_query = select(func.count()).select_from(MatchRuleOperationAuditModel)
        if filters:
            total_query = total_query.where(*filters)
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()

        query = (
            select(MatchRuleOperationAuditModel)
            .order_by(MatchRuleOperationAuditModel.created_at.desc(), MatchRuleOperationAuditModel.id.desc())
            .offset(skip)
            .limit(limit)
        )
        if filters:
            query = query.where(*filters)
        result = await db.execute(query)
        return list(result.scalars().all()), total

    @staticmethod
    async def create_audit(db: AsyncSession, audit: MatchRuleMatchAuditModel) -> MatchRuleMatchAuditModel:
        db.add(audit)
        await db.commit()
        await db.refresh(audit)
        return audit

    @staticmethod
    async def list_audits(
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
    ) -> tuple[list[MatchRuleMatchAuditModel], int]:
        filters = []
        if experiment_id is not None:
            filters.append(MatchRuleMatchAuditModel.experiment_id == experiment_id)
        if rule_config_id is not None:
            filters.append(MatchRuleMatchAuditModel.rule_config_id == rule_config_id)
        if job_id is not None:
            filters.append(MatchRuleMatchAuditModel.job_id == job_id)
        if seeker_id is not None:
            filters.append(MatchRuleMatchAuditModel.seeker_id == seeker_id)
        if experiment_bucket is not None:
            filters.append(MatchRuleMatchAuditModel.experiment_bucket == experiment_bucket)
        if created_from is not None:
            filters.append(MatchRuleMatchAuditModel.created_at >= created_from)
        if created_to is not None:
            filters.append(MatchRuleMatchAuditModel.created_at <= created_to)

        total_query = select(func.count()).select_from(MatchRuleMatchAuditModel)
        if filters:
            total_query = total_query.where(*filters)
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()

        query = (
            select(MatchRuleMatchAuditModel)
            .options(
                selectinload(MatchRuleMatchAuditModel.job),
                selectinload(MatchRuleMatchAuditModel.seeker),
                selectinload(MatchRuleMatchAuditModel.rule_config),
                selectinload(MatchRuleMatchAuditModel.experiment),
            )
            .order_by(MatchRuleMatchAuditModel.created_at.desc(), MatchRuleMatchAuditModel.id.desc())
            .offset(skip)
            .limit(limit)
        )
        if filters:
            query = query.where(*filters)
        result = await db.execute(query)
        return list(result.scalars().all()), total

    @staticmethod
    async def get_audit_by_id(db: AsyncSession, audit_id: int) -> Optional[MatchRuleMatchAuditModel]:
        result = await db.execute(
            select(MatchRuleMatchAuditModel)
            .options(
                selectinload(MatchRuleMatchAuditModel.job),
                selectinload(MatchRuleMatchAuditModel.seeker),
                selectinload(MatchRuleMatchAuditModel.rule_config),
                selectinload(MatchRuleMatchAuditModel.experiment),
            )
            .where(MatchRuleMatchAuditModel.id == audit_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_quality_audits(
        db: AsyncSession,
        *,
        experiment_id: int | None = None,
        rule_config_id: int | None = None,
        scope: str | None = None,
        template_key: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> list[MatchRuleMatchAuditModel]:
        filters = []
        if experiment_id is not None:
            filters.append(MatchRuleMatchAuditModel.experiment_id == experiment_id)
        if rule_config_id is not None:
            filters.append(MatchRuleMatchAuditModel.rule_config_id == rule_config_id)
        if scope is not None:
            filters.append(MatchRuleMatchAuditModel.scope == scope)
        if template_key is not None:
            filters.append(MatchRuleMatchAuditModel.template_key == template_key)
        if created_from is not None:
            filters.append(MatchRuleMatchAuditModel.created_at >= created_from)
        if created_to is not None:
            filters.append(MatchRuleMatchAuditModel.created_at <= created_to)

        query = (
            select(MatchRuleMatchAuditModel)
            .options(
                selectinload(MatchRuleMatchAuditModel.job).selectinload(Job.standard_position),
                selectinload(MatchRuleMatchAuditModel.rule_config),
                selectinload(MatchRuleMatchAuditModel.experiment),
            )
            .order_by(MatchRuleMatchAuditModel.created_at.asc(), MatchRuleMatchAuditModel.id.asc())
        )
        if filters:
            query = query.where(*filters)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_experiment_effect_rows(db: AsyncSession, experiment_id: int) -> list[tuple[str, int, float, int, int, int]]:
        result = await db.execute(
            select(
                MatchRuleMatchAuditModel.experiment_bucket,
                func.count(MatchRuleMatchAuditModel.id),
                func.avg(MatchRuleMatchAuditModel.overall_score),
                func.sum(case((MatchRuleMatchAuditModel.level == "high", 1), else_=0)),
                func.sum(case((MatchRuleMatchAuditModel.level == "medium", 1), else_=0)),
                func.sum(case((MatchRuleMatchAuditModel.level == "low", 1), else_=0)),
            )
            .where(MatchRuleMatchAuditModel.experiment_id == experiment_id)
            .group_by(MatchRuleMatchAuditModel.experiment_bucket)
        )
        return list(result.all())
