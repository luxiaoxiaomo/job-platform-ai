"""
Write operations for match rule configs.
"""
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.match.config import MatchRuleConfigService
from app.modules.match.models import (
    MatchRuleConfigModel,
    MatchRuleDimensionModel,
    MatchRuleExperimentModel,
    MatchRuleOperationAuditModel,
)
from app.modules.match.repository import MatchRuleConfigRepository
from app.modules.match.schemas import (
    MatchRuleConfigVersionCreateRequest,
    MatchRulePublishRequest,
    MatchRulePublishResponse,
    MatchRuleReleaseCheckItemResponse,
    MatchRuleReleaseCheckResponse,
    MatchRuleExperimentCreateRequest,
    MatchRuleExperimentStatusUpdateRequest,
    MatchRuleExperimentStatusUpdateResponse,
    MatchRuleRollbackRequest,
    MatchRuleTemplateCreateRequest,
)
from app.modules.user.models import User


class MatchRuleWriteService:
    """Admin write workflows for rule config versions."""

    @staticmethod
    async def create_version(
        db: AsyncSession,
        current_user: User,
        source_config_id: int,
        payload: MatchRuleConfigVersionCreateRequest,
    ) -> MatchRuleConfigModel:
        source_config = await MatchRuleConfigRepository.get_by_id(db, source_config_id)
        if source_config is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="match_rule_config_not_found")

        dimensions_payload = MatchRuleWriteService._validated_dimensions_payload(payload)

        scope = payload.scope or source_config.scope
        template_key = payload.template_key or source_config.template_key
        template_name = payload.template_name or source_config.template_name
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        MatchRuleConfigService.build_config(
            dimensions_payload,
            config_id=f"draft_from_{source_config.id}",
            name=payload.name,
            strategy=source_config.strategy,
            scope=scope,
            template_key=template_key,
            template_name=template_name,
            status=payload.status,
            version=1,
            description=payload.description,
            updated_at=now,
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
            parent_version_id=source_config.id,
            created_by=current_user.id,
            updated_by=current_user.id,
        )

        version_result = await db.execute(
            select(func.max(MatchRuleConfigModel.version)).where(
                MatchRuleConfigModel.scope == scope,
                MatchRuleConfigModel.strategy == source_config.strategy,
                MatchRuleConfigModel.template_key == template_key,
            )
        )
        next_version = int(version_result.scalar() or 0) + 1

        if payload.status == "active":
            active_result = await db.execute(
                select(MatchRuleConfigModel)
                .options(selectinload(MatchRuleConfigModel.dimensions))
                .where(
                    MatchRuleConfigModel.scope == scope,
                    MatchRuleConfigModel.strategy == source_config.strategy,
                    MatchRuleConfigModel.template_key == template_key,
                    MatchRuleConfigModel.status == "active",
                )
            )
            for active_config in active_result.scalars().all():
                active_config.status = "archived"
                active_config.effective_to = now
                active_config.updated_by = current_user.id

        new_config = MatchRuleConfigModel(
            name=payload.name,
            strategy=source_config.strategy,
            scope=scope,
            template_key=template_key,
            template_name=template_name,
            status=payload.status,
            version=next_version,
            description=payload.description,
            parent_version_id=source_config.id,
            effective_from=payload.effective_from or (now if payload.status == "active" else None),
            effective_to=payload.effective_to,
            created_by=current_user.id,
            updated_by=current_user.id,
        )
        for dimension in sorted(dimensions_payload, key=lambda item: int(item.get("sort_order", 0))):
            new_config.dimensions.append(
                MatchRuleDimensionModel(
                    dimension_key=str(dimension["key"]),
                    label=str(dimension["label"]),
                    weight=float(dimension.get("weight", 0)),
                    enabled=bool(dimension.get("enabled", True)),
                    description=str(dimension.get("description") or ""),
                    scoring_method=str(dimension.get("scoring_method") or ""),
                    logic_json=dict(dimension.get("logic") or {}),
                    sort_order=int(dimension.get("sort_order", 0)),
                )
            )

        db.add(new_config)
        await db.commit()
        created = await MatchRuleConfigRepository.get_by_id(db, new_config.id)
        if created is None:
            raise RuntimeError("match_rule_config_create_failed")
        return created

    @staticmethod
    async def create_template(
        db: AsyncSession,
        current_user: User,
        payload: MatchRuleTemplateCreateRequest,
    ) -> MatchRuleConfigModel:
        dimensions_payload = MatchRuleWriteService._validated_dimensions_payload(payload)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        MatchRuleConfigService.build_config(
            dimensions_payload,
            config_id=f"template_{payload.template_key}_draft",
            name=payload.name,
            strategy="rule_v1",
            scope=payload.scope,
            template_key=payload.template_key,
            template_name=payload.template_name,
            status=payload.status,
            version=1,
            description=payload.description,
            updated_at=now,
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
            created_by=current_user.id,
            updated_by=current_user.id,
        )

        existing_result = await db.execute(
            select(MatchRuleConfigModel).where(
                MatchRuleConfigModel.scope == payload.scope,
                MatchRuleConfigModel.strategy == "rule_v1",
                MatchRuleConfigModel.template_key == payload.template_key,
            )
        )
        if existing_result.scalars().first() is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="match_rule_template_exists")

        config = MatchRuleConfigModel(
            name=payload.name,
            strategy="rule_v1",
            scope=payload.scope,
            template_key=payload.template_key,
            template_name=payload.template_name,
            status=payload.status,
            version=1,
            description=payload.description,
            effective_from=payload.effective_from or (now if payload.status == "active" else None),
            effective_to=payload.effective_to,
            created_by=current_user.id,
            updated_by=current_user.id,
        )
        MatchRuleWriteService._append_dimensions(config, dimensions_payload)
        db.add(config)
        await db.commit()
        created = await MatchRuleConfigRepository.get_by_id(db, config.id)
        if created is None:
            raise RuntimeError("match_rule_config_create_failed")
        return created

    @staticmethod
    async def rollback_version(
        db: AsyncSession,
        current_user: User,
        current_config_id: int,
        payload: MatchRuleRollbackRequest,
    ) -> MatchRuleConfigModel:
        current_config = await MatchRuleConfigRepository.get_by_id(db, current_config_id)
        target_config = await MatchRuleConfigRepository.get_by_id(db, payload.target_config_id)
        if current_config is None or target_config is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="match_rule_config_not_found")
        if current_config.scope != target_config.scope or current_config.strategy != target_config.strategy:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="match_rule_config_scope_mismatch")
        if current_config.template_key != target_config.template_key:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="match_rule_template_mismatch")

        version_payload = MatchRuleConfigVersionCreateRequest(
            name=payload.name or f"Rollback to V{target_config.version}",
            description=payload.description if payload.description is not None else target_config.description,
            status=payload.status,
            scope=current_config.scope,
            template_key=current_config.template_key,
            template_name=current_config.template_name,
            dimensions=[
                {
                    "key": dimension.dimension_key,
                    "label": dimension.label,
                    "weight": dimension.weight,
                    "enabled": dimension.enabled,
                    "description": dimension.description,
                    "scoring_method": dimension.scoring_method,
                    "logic": dimension.logic_json or {},
                    "sort_order": dimension.sort_order,
                }
                for dimension in target_config.dimensions
            ],
        )
        return await MatchRuleWriteService.create_version(db, current_user, current_config_id, version_payload)

    @staticmethod
    async def release_check(
        db: AsyncSession,
        config_id: int,
    ) -> MatchRuleReleaseCheckResponse:
        config = await MatchRuleConfigRepository.get_by_id(db, config_id)
        if config is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="match_rule_config_not_found")

        blockers: list[MatchRuleReleaseCheckItemResponse] = []
        warnings: list[MatchRuleReleaseCheckItemResponse] = []
        active_configs = await MatchRuleConfigRepository.list_active_configs(
            db,
            scope=config.scope,
            template_key=config.template_key,
            strategy=config.strategy,
        )
        current_active = next((item for item in active_configs if item.id != config.id), active_configs[0] if active_configs else None)

        if config.status == "archived":
            blockers.append(
                MatchRuleReleaseCheckItemResponse(
                    code="rule_archived",
                    message="Archived rule configs cannot be published.",
                    resource_type="rule_config",
                    resource_id=config.id,
                )
            )
        if config.status == "active":
            blockers.append(
                MatchRuleReleaseCheckItemResponse(
                    code="rule_already_active",
                    message="Rule config is already active.",
                    resource_type="rule_config",
                    resource_id=config.id,
                )
            )
        if config.effective_from and config.effective_to and config.effective_to <= config.effective_from:
            blockers.append(
                MatchRuleReleaseCheckItemResponse(
                    code="invalid_effective_window",
                    message="Effective end time must be later than effective start time.",
                    resource_type="rule_config",
                    resource_id=config.id,
                )
            )

        enabled_dimensions = [item for item in config.dimensions if item.enabled]
        configured_total = sum(float(item.weight or 0) for item in enabled_dimensions)
        if not enabled_dimensions:
            blockers.append(
                MatchRuleReleaseCheckItemResponse(
                    code="no_enabled_dimensions",
                    message="At least one dimension must be enabled before publishing.",
                    resource_type="rule_config",
                    resource_id=config.id,
                )
            )
        if configured_total <= 0:
            blockers.append(
                MatchRuleReleaseCheckItemResponse(
                    code="invalid_weight_total",
                    message="Enabled dimension weights must sum to a positive value.",
                    resource_type="rule_config",
                    resource_id=config.id,
                )
            )
        try:
            MatchRuleConfigService.from_model(config)
        except ValueError:
            blockers.append(
                MatchRuleReleaseCheckItemResponse(
                    code="invalid_rule_config",
                    message="Rule config cannot be converted to runtime configuration.",
                    resource_type="rule_config",
                    resource_id=config.id,
                )
            )

        running_experiment = await MatchRuleConfigRepository.get_running_experiment(
            db,
            scope=config.scope,
            template_key=config.template_key,
        )
        if running_experiment is not None:
            blockers.append(
                MatchRuleReleaseCheckItemResponse(
                    code="running_experiment_conflict",
                    message="A running experiment exists for the same scope and template.",
                    resource_type="rule_experiment",
                    resource_id=running_experiment.id,
                )
            )

        if config.status == "draft":
            warnings.append(
                MatchRuleReleaseCheckItemResponse(
                    code="publish_from_draft",
                    message="Publishing directly from draft skips testing status.",
                    resource_type="rule_config",
                    resource_id=config.id,
                )
            )
        if current_active is not None:
            large_delta_keys = MatchRuleWriteService._large_weight_delta_keys(current_active, config)
            if large_delta_keys:
                warnings.append(
                    MatchRuleReleaseCheckItemResponse(
                        code="large_weight_change",
                        message=f"Large configured weight change detected: {', '.join(large_delta_keys)}.",
                        resource_type="rule_config",
                        resource_id=config.id,
                    )
                )

        return MatchRuleReleaseCheckResponse(
            rule_config_id=config.id,
            scope=config.scope,
            template_key=config.template_key,
            status=config.status,
            current_active_config_id=current_active.id if current_active is not None else None,
            can_publish=len(blockers) == 0,
            blockers=blockers,
            warnings=warnings,
            summary={
                "enabled_dimension_count": len(enabled_dimensions),
                "configured_total_weight": configured_total,
                "blocker_count": len(blockers),
                "warning_count": len(warnings),
            },
        )

    @staticmethod
    async def publish_rule_config(
        db: AsyncSession,
        current_user: User,
        config_id: int,
        payload: MatchRulePublishRequest,
    ) -> MatchRulePublishResponse:
        from app.modules.match.service import MatchService

        target = await MatchRuleConfigRepository.get_by_id(db, config_id)
        if target is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="match_rule_config_not_found")

        before_snapshot = MatchRuleWriteService._config_snapshot(target)
        release_check = await MatchRuleWriteService.release_check(db, config_id)
        if release_check.blockers:
            await MatchRuleWriteService._record_operation_audit(
                db,
                actor_id=current_user.id,
                action="block_publish",
                resource_type="rule_config",
                resource_id=target.id,
                reason=payload.reason,
                before_snapshot=before_snapshot,
                after_snapshot=before_snapshot,
                metadata={"release_check": release_check.model_dump(mode="json")},
                commit=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "match_rule_publish_blocked",
                    "release_check": release_check.model_dump(mode="json"),
                },
            )
        if release_check.warnings and not payload.confirm_warnings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "match_rule_publish_warning_unconfirmed",
                    "release_check": release_check.model_dump(mode="json"),
                },
            )

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        active_configs = await MatchRuleConfigRepository.list_active_configs(
            db,
            scope=target.scope,
            template_key=target.template_key,
            strategy=target.strategy,
        )
        archived_config_ids: list[int] = []
        for active_config in active_configs:
            if active_config.id == target.id:
                continue
            active_config.status = "archived"
            active_config.effective_to = now
            active_config.updated_by = current_user.id
            archived_config_ids.append(active_config.id)

        target.status = "active"
        target.effective_from = target.effective_from or now
        target.effective_to = None
        target.updated_by = current_user.id
        after_snapshot = MatchRuleWriteService._config_snapshot(target)
        await MatchRuleWriteService._record_operation_audit(
            db,
            actor_id=current_user.id,
            action="publish_rule",
            resource_type="rule_config",
            resource_id=target.id,
            reason=payload.reason,
            before_snapshot=before_snapshot,
            after_snapshot=after_snapshot,
            metadata={"release_check": release_check.model_dump(mode="json"), "archived_config_ids": archived_config_ids},
            commit=False,
        )
        await db.commit()

        published = await MatchRuleConfigRepository.get_by_id(db, target.id)
        if published is None:
            raise RuntimeError("match_rule_config_publish_failed")
        return MatchRulePublishResponse(
            config=MatchService._rule_config_response(MatchRuleConfigService.from_model(published)),
            archived_config_ids=archived_config_ids,
            release_check=release_check,
        )

    @staticmethod
    async def create_experiment(
        db: AsyncSession,
        current_user: User,
        payload: MatchRuleExperimentCreateRequest,
    ) -> MatchRuleExperimentModel:
        control = await MatchRuleConfigRepository.get_by_id(db, payload.control_config_id)
        treatment = await MatchRuleConfigRepository.get_by_id(db, payload.treatment_config_id)
        if control is None or treatment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="match_rule_config_not_found")
        if control.scope != payload.scope or treatment.scope != payload.scope:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="match_rule_config_scope_mismatch")
        if control.template_key != payload.template_key or treatment.template_key != payload.template_key:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="match_rule_template_mismatch")
        if payload.status == "running":
            running_experiment = await MatchRuleConfigRepository.get_running_experiment(
                db,
                scope=payload.scope,
                template_key=payload.template_key,
            )
            if running_experiment is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="running_experiment_conflict")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        experiment = MatchRuleExperimentModel(
            name=payload.name,
            description=payload.description,
            scope=payload.scope,
            template_key=payload.template_key,
            status=payload.status,
            traffic_percent=payload.traffic_percent,
            control_config_id=payload.control_config_id,
            treatment_config_id=payload.treatment_config_id,
            audience=payload.audience,
            started_at=payload.started_at or (now if payload.status == "running" else None),
            ended_at=payload.ended_at,
            created_by=current_user.id,
            updated_by=current_user.id,
        )
        return await MatchRuleConfigRepository.create_experiment(db, experiment)

    @staticmethod
    async def update_experiment_status(
        db: AsyncSession,
        current_user: User,
        experiment_id: int,
        payload: MatchRuleExperimentStatusUpdateRequest,
    ) -> MatchRuleExperimentStatusUpdateResponse:
        from app.modules.match.service import MatchService

        experiment = await MatchRuleConfigRepository.get_experiment_by_id(db, experiment_id)
        if experiment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="match_rule_experiment_not_found")
        if experiment.status == "ended" and payload.status != "ended":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="experiment_already_ended")

        before_snapshot = MatchRuleWriteService._experiment_snapshot(experiment)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        action = "update_experiment_status"
        if payload.status == "paused":
            if experiment.status != "running":
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="experiment_must_be_running")
            experiment.status = "paused"
            action = "pause_experiment"
        elif payload.status == "running":
            running_experiment = await MatchRuleConfigRepository.get_running_experiment(
                db,
                scope=experiment.scope,
                template_key=experiment.template_key,
                exclude_experiment_id=experiment.id,
            )
            if running_experiment is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="running_experiment_conflict")
            action = "resume_experiment" if experiment.status == "paused" else "start_experiment"
            experiment.status = "running"
            experiment.started_at = experiment.started_at or now
            experiment.ended_at = None
        elif payload.status == "ended":
            experiment.status = "ended"
            experiment.ended_at = experiment.ended_at or now
            action = "end_experiment"

        experiment.updated_by = current_user.id
        after_snapshot = MatchRuleWriteService._experiment_snapshot(experiment)
        await MatchRuleWriteService._record_operation_audit(
            db,
            actor_id=current_user.id,
            action=action,
            resource_type="rule_experiment",
            resource_id=experiment.id,
            reason=payload.reason,
            before_snapshot=before_snapshot,
            after_snapshot=after_snapshot,
            metadata={"from_status": before_snapshot["status"], "to_status": experiment.status},
            commit=False,
        )
        await db.commit()
        await db.refresh(experiment)
        return MatchRuleExperimentStatusUpdateResponse(experiment=MatchService._experiment_response(experiment))

    @staticmethod
    def _validated_dimensions_payload(payload: MatchRuleConfigVersionCreateRequest) -> list[dict]:
        dimensions_payload = [item.model_dump() for item in payload.dimensions]
        dimension_keys = [str(item["key"]) for item in dimensions_payload]
        if len(set(dimension_keys)) != len(dimension_keys):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="duplicate_dimension_key")
        return dimensions_payload

    @staticmethod
    def _append_dimensions(config: MatchRuleConfigModel, dimensions_payload: list[dict]) -> None:
        for dimension in sorted(dimensions_payload, key=lambda item: int(item.get("sort_order", 0))):
            config.dimensions.append(
                MatchRuleDimensionModel(
                    dimension_key=str(dimension["key"]),
                    label=str(dimension["label"]),
                    weight=float(dimension.get("weight", 0)),
                    enabled=bool(dimension.get("enabled", True)),
                    description=str(dimension.get("description") or ""),
                    scoring_method=str(dimension.get("scoring_method") or ""),
                    logic_json=dict(dimension.get("logic") or {}),
                    sort_order=int(dimension.get("sort_order", 0)),
                )
            )

    @staticmethod
    def _large_weight_delta_keys(base: MatchRuleConfigModel, target: MatchRuleConfigModel) -> list[str]:
        base_weights = {dimension.dimension_key: float(dimension.weight or 0) for dimension in base.dimensions}
        target_weights = {dimension.dimension_key: float(dimension.weight or 0) for dimension in target.dimensions}
        return [
            key
            for key in sorted(base_weights.keys() & target_weights.keys())
            if abs(target_weights[key] - base_weights[key]) >= 30
        ]

    @staticmethod
    async def _record_operation_audit(
        db: AsyncSession,
        *,
        actor_id: int | None,
        action: str,
        resource_type: str,
        resource_id: int,
        reason: str,
        before_snapshot: dict | None = None,
        after_snapshot: dict | None = None,
        metadata: dict | None = None,
        commit: bool = False,
    ) -> MatchRuleOperationAuditModel:
        audit = MatchRuleOperationAuditModel(
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            reason=reason,
            before_snapshot=before_snapshot,
            after_snapshot=after_snapshot,
            metadata_json=metadata or {},
        )
        return await MatchRuleConfigRepository.create_operation_audit(db, audit, commit=commit)

    @staticmethod
    def _config_snapshot(config: MatchRuleConfigModel) -> dict:
        return {
            "id": config.id,
            "name": config.name,
            "strategy": config.strategy,
            "scope": config.scope,
            "template_key": config.template_key,
            "template_name": config.template_name,
            "status": config.status,
            "version": config.version,
            "effective_from": MatchRuleWriteService._datetime_iso(config.effective_from),
            "effective_to": MatchRuleWriteService._datetime_iso(config.effective_to),
            "updated_by": config.updated_by,
        }

    @staticmethod
    def _experiment_snapshot(experiment: MatchRuleExperimentModel) -> dict:
        return {
            "id": experiment.id,
            "name": experiment.name,
            "scope": experiment.scope,
            "template_key": experiment.template_key,
            "status": experiment.status,
            "traffic_percent": experiment.traffic_percent,
            "control_config_id": experiment.control_config_id,
            "treatment_config_id": experiment.treatment_config_id,
            "started_at": MatchRuleWriteService._datetime_iso(experiment.started_at),
            "ended_at": MatchRuleWriteService._datetime_iso(experiment.ended_at),
            "updated_by": experiment.updated_by,
        }

    @staticmethod
    def _datetime_iso(value: datetime | None) -> str | None:
        return value.isoformat() if value is not None else None
