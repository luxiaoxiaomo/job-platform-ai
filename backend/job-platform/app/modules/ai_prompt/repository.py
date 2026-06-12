"""
AI prompt configuration repository.
"""
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai_prompt.models import AiPromptConfig


class AiPromptConfigRepository:
    @staticmethod
    async def list_by_scenario(db: AsyncSession, scenario_key: str) -> tuple[list[AiPromptConfig], int]:
        total_result = await db.execute(
            select(func.count()).select_from(AiPromptConfig).where(AiPromptConfig.scenario_key == scenario_key)
        )
        total = total_result.scalar_one()
        result = await db.execute(
            select(AiPromptConfig)
            .where(AiPromptConfig.scenario_key == scenario_key)
            .order_by(AiPromptConfig.version.desc())
        )
        return list(result.scalars().all()), total

    @staticmethod
    async def get_active(db: AsyncSession, scenario_key: str) -> Optional[AiPromptConfig]:
        result = await db.execute(
            select(AiPromptConfig)
            .where(AiPromptConfig.scenario_key == scenario_key, AiPromptConfig.is_active.is_(True))
            .order_by(AiPromptConfig.version.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(db: AsyncSession, config_id: int) -> Optional[AiPromptConfig]:
        result = await db.execute(select(AiPromptConfig).where(AiPromptConfig.id == config_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def next_version(db: AsyncSession, scenario_key: str) -> int:
        result = await db.execute(
            select(func.max(AiPromptConfig.version)).where(AiPromptConfig.scenario_key == scenario_key)
        )
        current = result.scalar_one()
        return int(current or 0) + 1

    @staticmethod
    async def create(db: AsyncSession, config: AiPromptConfig) -> AiPromptConfig:
        db.add(config)
        await db.commit()
        await db.refresh(config)
        return config

    @staticmethod
    async def publish(db: AsyncSession, config: AiPromptConfig) -> AiPromptConfig:
        await db.execute(
            update(AiPromptConfig)
            .where(AiPromptConfig.scenario_key == config.scenario_key)
            .values(is_active=False)
        )
        config.is_active = True
        await db.commit()
        await db.refresh(config)
        return config
