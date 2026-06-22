"""
Default rule configuration for rule-based job matching.
"""
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class MatchRuleDimensionConfig:
    """One configurable matching dimension."""

    key: str
    label: str
    configured_weight: float
    effective_weight: float
    enabled: bool
    description: str
    scoring_method: str
    logic: dict
    sort_order: int


@dataclass(frozen=True)
class MatchRuleConfig:
    """Runtime rule config used by the rule-based matcher."""

    id: int | str | None
    name: str
    strategy: str
    scope: str
    template_key: str
    template_name: str
    status: str
    version: int
    description: str
    configured_total_weight: float
    effective_total_weight: float
    dimensions: list[MatchRuleDimensionConfig]
    updated_at: datetime
    parent_version_id: int | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    created_by: int | None = None
    updated_by: int | None = None

    @property
    def configured_weights(self) -> dict[str, float]:
        return {item.key: item.configured_weight for item in self.dimensions}

    @property
    def effective_weights(self) -> dict[str, float]:
        return {item.key: item.effective_weight for item in self.dimensions if item.enabled}

    def enabled_dimensions(self) -> list[MatchRuleDimensionConfig]:
        return [item for item in self.dimensions if item.enabled]


DEFAULT_RULE_DIMENSIONS = [
    {
        "key": "skill",
        "label": "技能匹配",
        "weight": 35,
        "description": "岗位标签、岗位描述中的技能要求与简历技能做规则匹配",
        "scoring_method": "命中岗位技能越多，分数越高；未识别岗位技能时按中性分处理",
        "logic": {"type": "keyword_match", "sources": ["job.tags", "job.description", "job.requirement", "resume.skills"]},
    },
    {
        "key": "experience",
        "label": "经验年限",
        "weight": 20,
        "description": "简历工作年限与岗位经验要求做比较",
        "scoring_method": "满足要求给高分，低于要求按差距扣分",
        "logic": {"type": "threshold_compare", "source": "resume.basic_info.work_years"},
    },
    {
        "key": "education",
        "label": "学历匹配",
        "weight": 15,
        "description": "最高学历与岗位学历门槛做等级比较",
        "scoring_method": "达到或超过岗位要求给高分，低于要求按等级差距扣分",
        "logic": {"type": "rank_compare", "source": "resume.basic_info.highest_education"},
    },
    {
        "key": "city",
        "label": "城市匹配",
        "weight": 10,
        "description": "当前城市与岗位城市做文本匹配",
        "scoring_method": "城市一致给高分，不一致扣分；缺失当前城市按中性分处理",
        "logic": {"type": "text_contains", "source": "resume.basic_info.current_city"},
    },
    {
        "key": "salary",
        "label": "薪资匹配",
        "weight": 10,
        "description": "期望薪资与岗位薪资区间是否重叠",
        "scoring_method": "区间重叠给高分，缺失信息按中性分处理",
        "logic": {"type": "range_overlap", "source": "resume.basic_info.expected_salary"},
    },
    {
        "key": "intention",
        "label": "岗位意向",
        "weight": 10,
        "description": "求职目标岗位与当前岗位标题做关键词匹配",
        "scoring_method": "标题和求职意向关键词重合越多，分数越高",
        "logic": {"type": "token_overlap", "source": "resume.basic_info.target_position"},
    },
]


class MatchRuleConfigService:
    """Rule config provider.

    R-P3-03 keeps the provider in code, but the shape mirrors the future table
    design so the API contract does not need to change when configs move to DB.
    """

    @staticmethod
    def get_default_config() -> MatchRuleConfig:
        return MatchRuleConfigService.build_config(DEFAULT_RULE_DIMENSIONS)

    @staticmethod
    def from_model(config) -> MatchRuleConfig:
        raw_dimensions = [
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
            for dimension in config.dimensions
        ]
        runtime_config = MatchRuleConfigService.build_config(raw_dimensions)
        return replace(
            runtime_config,
            id=config.id,
            name=config.name,
            strategy=config.strategy,
            scope=config.scope,
            template_key=getattr(config, "template_key", "default"),
            template_name=getattr(config, "template_name", "Default template"),
            status=config.status,
            version=config.version,
            description=config.description,
            updated_at=config.updated_at,
            parent_version_id=config.parent_version_id,
            effective_from=config.effective_from,
            effective_to=config.effective_to,
            created_by=config.created_by,
            updated_by=config.updated_by,
        )

    @staticmethod
    def build_config(
        raw_dimensions: list[dict],
        *,
        config_id: int | str | None = "default_rule_v1",
        name: str = "默认人岗匹配规则 V1",
        strategy: str = "rule_v1",
        scope: str = "global",
        template_key: str = "default",
        template_name: str = "Default template",
        status: str = "active",
        version: int = 1,
        description: str = "规则版 V1，基于技能、经验、学历、城市、薪资和岗位意向计算匹配度",
        updated_at: datetime | None = None,
        parent_version_id: int | None = None,
        effective_from: datetime | None = None,
        effective_to: datetime | None = None,
        created_by: int | None = None,
        updated_by: int | None = None,
    ) -> MatchRuleConfig:
        enabled_dimensions = [item for item in raw_dimensions if item.get("enabled", True)]
        configured_total = sum(float(item.get("weight", 0)) for item in enabled_dimensions)
        if configured_total <= 0:
            raise ValueError("match_rule_config_weight_total_must_be_positive")

        dimensions: list[MatchRuleDimensionConfig] = []
        for index, item in enumerate(raw_dimensions):
            configured_weight = float(item.get("weight", 0))
            enabled = bool(item.get("enabled", True))
            effective_weight = configured_weight / configured_total * 100 if enabled else 0.0
            dimensions.append(
                MatchRuleDimensionConfig(
                    key=str(item["key"]),
                    label=str(item["label"]),
                    configured_weight=MatchRuleConfigService._round_weight(configured_weight),
                    effective_weight=MatchRuleConfigService._round_weight(effective_weight),
                    enabled=enabled,
                    description=str(item.get("description") or ""),
                    scoring_method=str(item.get("scoring_method") or ""),
                    logic=dict(item.get("logic") or {}),
                    sort_order=int(item.get("sort_order", index + 1)),
                )
            )

        return MatchRuleConfig(
            id=config_id,
            name=name,
            strategy=strategy,
            scope=scope,
            template_key=template_key,
            template_name=template_name,
            status=status,
            version=version,
            description=description,
            configured_total_weight=MatchRuleConfigService._round_weight(
                sum(float(item.get("weight", 0)) for item in raw_dimensions if item.get("enabled", True))
            ),
            effective_total_weight=100,
            dimensions=sorted(dimensions, key=lambda item: item.sort_order),
            updated_at=updated_at or datetime(2026, 6, 17),
            parent_version_id=parent_version_id,
            effective_from=effective_from,
            effective_to=effective_to,
            created_by=created_by,
            updated_by=updated_by,
        )

    @staticmethod
    def _round_weight(value: float) -> float:
        rounded = round(value, 2)
        return int(rounded) if rounded.is_integer() else rounded
