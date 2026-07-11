# ruff: noqa: E402
from __future__ import annotations

"""Pure hybrid scoring service for P4 intelligent matching."""

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal


ScoreValue = float | int | None
MatchSource = Literal["rule_baseline", "hybrid", "hybrid_degraded"]
RecallSource = Literal["rule_only", "vector_only", "rule_and_vector"]


@dataclass(frozen=True)
class ThreeDimensionalWeights:
    """Weights inside the semantic/tag/keyword base score."""

    semantic_score: float = 0.50
    tag_score: float = 0.30
    keyword_score: float = 0.20

    def __post_init__(self) -> None:
        _validate_weight_total(
            "three_dimensional_weights_total_must_equal_1",
            self.semantic_score,
            self.tag_score,
            self.keyword_score,
        )

    def as_dict(self) -> dict[str, float]:
        return {
            "semantic_score": self.semantic_score,
            "tag_score": self.tag_score,
            "keyword_score": self.keyword_score,
        }


@dataclass(frozen=True)
class HybridScoreWeights:
    """Weights for final score fusion after the base match score is computed."""

    base_match_score: float = 0.95
    profile_coverage_score: float = 0.05
    behavior_quality_score: float = 0.0

    def __post_init__(self) -> None:
        _validate_weight_total(
            "hybrid_weights_total_must_equal_1",
            self.base_match_score,
            self.profile_coverage_score,
            self.behavior_quality_score,
        )
        if self.profile_coverage_score > 0.10:
            raise ValueError("profile_coverage_weight_must_not_exceed_0.1")

    def as_dict(self) -> dict[str, float]:
        return {
            "base_match_score": self.base_match_score,
            "profile_coverage_score": self.profile_coverage_score,
            "behavior_quality_score": self.behavior_quality_score,
        }


@dataclass(frozen=True)
class IntelligentScoringConfig:
    """Runtime knobs for deterministic hybrid scoring."""

    three_dimensional_weights: ThreeDimensionalWeights = field(
        default_factory=ThreeDimensionalWeights
    )
    final_weights: HybridScoreWeights = field(default_factory=HybridScoreWeights)
    low_rule_score_threshold: float = 50
    low_rule_score_cap: float = 69
    low_profile_coverage_threshold: float = 40
    low_profile_coverage_cap: float = 69

    def __post_init__(self) -> None:
        _validate_score("low_rule_score_threshold", self.low_rule_score_threshold)
        _validate_score("low_rule_score_cap", self.low_rule_score_cap)
        _validate_score(
            "low_profile_coverage_threshold", self.low_profile_coverage_threshold
        )
        _validate_score("low_profile_coverage_cap", self.low_profile_coverage_cap)


@dataclass(frozen=True)
class HardConstraintItem:
    """One hard constraint cap emitted by caller or by the scoring service."""

    code: str
    final_cap: float | None = None
    status: Literal["passed", "warning", "failed"] = "failed"
    message: str = ""

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("hard_constraint_code_required")
        if self.final_cap is not None:
            _validate_score("hard_constraint_final_cap", self.final_cap)


@dataclass(frozen=True)
class HardConstraintResult:
    """Cap summary after applying hard constraints."""

    final_cap: float | None = None
    items: tuple[HardConstraintItem, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, object]:
        return {
            "final_cap": _clean_number(self.final_cap),
            "items": [
                {
                    "code": item.code,
                    "status": item.status,
                    "final_cap": _clean_number(item.final_cap),
                    "message": item.message,
                }
                for item in self.items
            ],
        }


@dataclass(frozen=True)
class IntelligentScoreInput:
    """Minimum score facts needed by BE-P4-05 without any database dependency."""

    semantic_score: ScoreValue
    tag_score: ScoreValue
    keyword_score: ScoreValue
    profile_coverage_score: ScoreValue
    behavior_quality_score: ScoreValue = None
    baseline_rule_score: ScoreValue = None
    vector_degrade_reason: str | None = None
    recall_source: RecallSource = "rule_and_vector"
    hard_constraints: tuple[HardConstraintItem, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ScoreComponents:
    """Auditable score components returned by the scoring service."""

    semantic_score: float | int | None
    tag_score: float | int | None
    keyword_score: float | int | None
    profile_coverage_score: float | int | None
    behavior_quality_score: float | int | None
    rule_score: float | int | None
    base_match_score: float | int | None
    uncapped_final_match_score: float | int | None
    final_match_score: float | int | None

    def as_dict(self) -> dict[str, float | int | None]:
        return {
            "semantic_score": self.semantic_score,
            "tag_score": self.tag_score,
            "keyword_score": self.keyword_score,
            "profile_coverage_score": self.profile_coverage_score,
            "behavior_quality_score": self.behavior_quality_score,
            "rule_score": self.rule_score,
            "base_match_score": self.base_match_score,
            "uncapped_final_match_score": self.uncapped_final_match_score,
            "final_match_score": self.final_match_score,
        }


@dataclass(frozen=True)
class IntelligentScorePreviewResult:
    """Full deterministic score preview for runtime or admin score-preview callers."""

    score_components: ScoreComponents
    actual_component_weights: dict[str, float]
    configured_weights: dict[str, dict[str, float]]
    hard_constraint_result: HardConstraintResult
    recall_source: RecallSource
    match_source: MatchSource
    degrade_reason: str | None
    audit_required: bool
    explanation_codes: list[str]
    weight_redistribution_reason: str | None = None
    vector_metadata: dict[str, object] | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "score_components": self.score_components.as_dict(),
            "actual_component_weights": self.actual_component_weights,
            "configured_weights": self.configured_weights,
            "hard_constraint_result": self.hard_constraint_result.as_dict(),
            "recall_source": self.recall_source,
            "match_source": self.match_source,
            "degrade_reason": self.degrade_reason,
            "audit_required": self.audit_required,
            "explanation_codes": self.explanation_codes,
            "weight_redistribution_reason": self.weight_redistribution_reason,
            "vector_metadata": self.vector_metadata,
        }


class IntelligentScoringService:
    """Hybrid score calculator with no runtime, API, or persistence dependency."""

    @staticmethod
    def preview_score(
        score_input: IntelligentScoreInput,
        *,
        config: IntelligentScoringConfig | None = None,
    ) -> IntelligentScorePreviewResult:
        config = config or IntelligentScoringConfig()
        validated = _ValidatedScoreInput.from_input(score_input)
        configured_weights = {
            "three_dimensional_weights": config.three_dimensional_weights.as_dict(),
            "final_weights": config.final_weights.as_dict(),
        }

        if validated.semantic_score is None and score_input.vector_degrade_reason:
            return IntelligentScoringService._fallback_result(
                validated,
                configured_weights=configured_weights,
                degrade_reason=score_input.vector_degrade_reason,
            )

        components, base_weights, weight_reasons = (
            IntelligentScoringService.calculate_components(validated, config=config)
        )
        hard_constraint_result = IntelligentScoringService.apply_hard_constraints(
            components,
            hard_constraints=tuple(score_input.hard_constraints or ()),
            config=config,
        )
        final_score = components.uncapped_final_match_score
        if hard_constraint_result.final_cap is not None and final_score is not None:
            final_score = min(
                float(final_score), float(hard_constraint_result.final_cap)
            )
        components = _replace_final_score(components, final_score)

        explanation_codes = IntelligentScoringService._explanation_codes(
            validated, hard_constraint_result
        )
        return IntelligentScorePreviewResult(
            score_components=components,
            actual_component_weights=base_weights,
            configured_weights=configured_weights,
            hard_constraint_result=hard_constraint_result,
            recall_source=score_input.recall_source,
            match_source="hybrid",
            degrade_reason=None,
            audit_required=True,
            explanation_codes=explanation_codes,
            weight_redistribution_reason=_join_reasons(weight_reasons),
        )

    @staticmethod
    def calculate_components(
        score_input: IntelligentScoreInput | "_ValidatedScoreInput",
        *,
        config: IntelligentScoringConfig | None = None,
    ) -> tuple[ScoreComponents, dict[str, float], list[str]]:
        config = config or IntelligentScoringConfig()
        validated = (
            score_input
            if isinstance(score_input, _ValidatedScoreInput)
            else _ValidatedScoreInput.from_input(score_input)
        )
        rule_score = _weighted_average(
            {
                "tag_score": validated.tag_score,
                "keyword_score": validated.keyword_score,
            },
            {"tag_score": 0.60, "keyword_score": 0.40},
        )
        base_score, internal_weights, internal_reasons = (
            _weighted_average_with_actual_weights(
                {
                    "semantic_score": validated.semantic_score,
                    "tag_score": validated.tag_score,
                    "keyword_score": validated.keyword_score,
                },
                config.three_dimensional_weights.as_dict(),
            )
        )
        if base_score is None:
            base_score = (
                validated.baseline_rule_score
                if validated.baseline_rule_score is not None
                else rule_score
            )
            internal_weights = {"semantic_score": 0, "tag_score": 0, "keyword_score": 0}
            internal_reasons.append("base_components_unavailable")

        final_score, final_weights, final_reasons = (
            _weighted_average_with_actual_weights(
                {
                    "base_match_score": base_score,
                    "profile_coverage_score": validated.profile_coverage_score,
                    "behavior_quality_score": validated.behavior_quality_score,
                },
                config.final_weights.as_dict(),
                profile_weight_max=0.10,
            )
        )
        flattened_weights = _flatten_component_weights(internal_weights, final_weights)
        components = ScoreComponents(
            semantic_score=_clean_number(validated.semantic_score),
            tag_score=_clean_number(validated.tag_score),
            keyword_score=_clean_number(validated.keyword_score),
            profile_coverage_score=_clean_number(validated.profile_coverage_score),
            behavior_quality_score=_clean_number(validated.behavior_quality_score),
            rule_score=_clean_number(rule_score),
            base_match_score=_clean_number(base_score),
            uncapped_final_match_score=_clean_number(final_score),
            final_match_score=_clean_number(final_score),
        )
        return components, flattened_weights, internal_reasons + final_reasons

    @staticmethod
    def apply_hard_constraints(
        components: ScoreComponents,
        *,
        hard_constraints: tuple[HardConstraintItem, ...] = (),
        config: IntelligentScoringConfig | None = None,
    ) -> HardConstraintResult:
        config = config or IntelligentScoringConfig()
        items = list(hard_constraints or ())
        if (
            components.rule_score is not None
            and float(components.rule_score) < config.low_rule_score_threshold
        ):
            items.append(
                HardConstraintItem(
                    code="low_rule_score_cap",
                    final_cap=config.low_rule_score_cap,
                    message="Rule score is below the safety threshold.",
                )
            )
        if (
            components.profile_coverage_score is not None
            and float(components.profile_coverage_score)
            < config.low_profile_coverage_threshold
        ):
            items.append(
                HardConstraintItem(
                    code="low_profile_coverage_cap",
                    final_cap=config.low_profile_coverage_cap,
                    message="Profile coverage is too low for a strong recommendation.",
                )
            )
        caps = [
            float(item.final_cap)
            for item in items
            if item.status != "passed" and item.final_cap is not None
        ]
        final_cap = min(caps) if caps else None
        return HardConstraintResult(
            final_cap=_clean_number(final_cap), items=tuple(items)
        )

    @staticmethod
    def _fallback_result(
        validated: "_ValidatedScoreInput",
        *,
        configured_weights: dict[str, dict[str, float]],
        degrade_reason: str,
    ) -> IntelligentScorePreviewResult:
        rule_score = _weighted_average(
            {
                "tag_score": validated.tag_score,
                "keyword_score": validated.keyword_score,
            },
            {"tag_score": 0.60, "keyword_score": 0.40},
        )
        fallback_score = (
            validated.baseline_rule_score
            if validated.baseline_rule_score is not None
            else rule_score
        )
        fallback_score = fallback_score if fallback_score is not None else 0
        components = ScoreComponents(
            semantic_score=None,
            tag_score=_clean_number(validated.tag_score),
            keyword_score=_clean_number(validated.keyword_score),
            profile_coverage_score=_clean_number(validated.profile_coverage_score),
            behavior_quality_score=_clean_number(validated.behavior_quality_score),
            rule_score=_clean_number(rule_score),
            base_match_score=_clean_number(fallback_score),
            uncapped_final_match_score=_clean_number(fallback_score),
            final_match_score=_clean_number(fallback_score),
        )
        return IntelligentScorePreviewResult(
            score_components=components,
            actual_component_weights={
                "semantic_score": 0,
                "tag_score": 0,
                "keyword_score": 0,
                "profile_coverage_score": 0,
                "behavior_quality_score": 0,
            },
            configured_weights=configured_weights,
            hard_constraint_result=HardConstraintResult(),
            recall_source="rule_only",
            match_source="rule_baseline",
            degrade_reason=degrade_reason,
            audit_required=True,
            explanation_codes=[degrade_reason, "fallback_rule_baseline"],
            weight_redistribution_reason=degrade_reason,
        )

    @staticmethod
    def _explanation_codes(
        validated: "_ValidatedScoreInput", hard_constraints: HardConstraintResult
    ) -> list[str]:
        codes: list[str] = []
        if validated.semantic_score is None:
            codes.append("semantic_unavailable")
        elif validated.semantic_score >= 80:
            codes.append("semantic_match_high")
        else:
            codes.append("semantic_match_available")

        if (
            validated.profile_coverage_score is None
            or validated.profile_coverage_score < 40
        ):
            codes.append("profile_coverage_low")
        else:
            codes.append("profile_coverage_valid")

        if validated.behavior_quality_score is None:
            codes.append("behavior_quality_unavailable")
        else:
            codes.append("behavior_quality_available")

        codes.extend(
            item.code for item in hard_constraints.items if item.code not in codes
        )
        return codes


@dataclass(frozen=True)
class _ValidatedScoreInput:
    semantic_score: float | None
    tag_score: float | None
    keyword_score: float | None
    profile_coverage_score: float | None
    behavior_quality_score: float | None
    baseline_rule_score: float | None

    @classmethod
    def from_input(cls, score_input: IntelligentScoreInput) -> "_ValidatedScoreInput":
        return cls(
            semantic_score=_validate_score(
                "semantic_score", score_input.semantic_score
            ),
            tag_score=_validate_score("tag_score", score_input.tag_score),
            keyword_score=_validate_score("keyword_score", score_input.keyword_score),
            profile_coverage_score=_validate_score(
                "profile_coverage_score", score_input.profile_coverage_score
            ),
            behavior_quality_score=_validate_score(
                "behavior_quality_score", score_input.behavior_quality_score
            ),
            baseline_rule_score=_validate_score(
                "baseline_rule_score", score_input.baseline_rule_score
            ),
        )


def _weighted_average(
    values: dict[str, float | None], weights: dict[str, float]
) -> float | None:
    score, _actual_weights, _reasons = _weighted_average_with_actual_weights(
        values, weights
    )
    return score


def _weighted_average_with_actual_weights(
    values: dict[str, float | None],
    weights: dict[str, float],
    *,
    profile_weight_max: float | None = None,
) -> tuple[float | None, dict[str, float], list[str]]:
    available_weights = {
        key: weights[key]
        for key, value in values.items()
        if value is not None and weights.get(key, 0) > 0
    }
    reasons = [
        _unavailable_reason_code(key)
        for key, value in values.items()
        if value is None and weights.get(key, 0) > 0
    ]
    available_total = sum(available_weights.values())
    if available_total <= 0:
        return None, {key: 0 for key in weights}, reasons

    actual_weights = {
        key: available_weights.get(key, 0) / available_total for key in weights
    }
    if profile_weight_max is not None:
        actual_weights = _cap_profile_weight(actual_weights, profile_weight_max)

    score = sum(
        float(values[key]) * actual_weights[key]
        for key in actual_weights
        if values.get(key) is not None
    )
    return (
        score,
        {key: _clean_weight(value) for key, value in actual_weights.items()},
        reasons,
    )


def _cap_profile_weight(
    actual_weights: dict[str, float], profile_weight_max: float
) -> dict[str, float]:
    profile_weight = actual_weights.get("profile_coverage_score", 0)
    if profile_weight <= profile_weight_max:
        return actual_weights

    capped = dict(actual_weights)
    capped["profile_coverage_score"] = profile_weight_max
    remaining_weight = 1 - profile_weight_max
    redistribution_keys = [
        key
        for key, value in actual_weights.items()
        if key != "profile_coverage_score" and value > 0
    ]
    redistribution_total = sum(actual_weights[key] for key in redistribution_keys)
    if redistribution_total <= 0:
        return capped
    for key in redistribution_keys:
        capped[key] = remaining_weight * actual_weights[key] / redistribution_total
    return capped


def _flatten_component_weights(
    internal_weights: dict[str, float],
    final_weights: dict[str, float],
) -> dict[str, float]:
    base_weight = final_weights.get("base_match_score", 0)
    return {
        "semantic_score": _clean_weight(
            base_weight * internal_weights.get("semantic_score", 0)
        ),
        "tag_score": _clean_weight(base_weight * internal_weights.get("tag_score", 0)),
        "keyword_score": _clean_weight(
            base_weight * internal_weights.get("keyword_score", 0)
        ),
        "profile_coverage_score": _clean_weight(
            final_weights.get("profile_coverage_score", 0)
        ),
        "behavior_quality_score": _clean_weight(
            final_weights.get("behavior_quality_score", 0)
        ),
    }


def _replace_final_score(
    components: ScoreComponents, final_score: float | int | None
) -> ScoreComponents:
    return ScoreComponents(
        semantic_score=components.semantic_score,
        tag_score=components.tag_score,
        keyword_score=components.keyword_score,
        profile_coverage_score=components.profile_coverage_score,
        behavior_quality_score=components.behavior_quality_score,
        rule_score=components.rule_score,
        base_match_score=components.base_match_score,
        uncapped_final_match_score=components.uncapped_final_match_score,
        final_match_score=_clean_number(final_score),
    )


def _validate_weight_total(error_code: str, *weights: float) -> None:
    if any(weight < 0 or weight > 1 for weight in weights):
        raise ValueError("weight_must_be_between_0_and_1")
    if abs(sum(weights) - 1.0) > 0.001:
        raise ValueError(error_code)


def _validate_score(name: str, value: ScoreValue) -> float | None:
    if value is None:
        return None
    numeric_value = float(value)
    if numeric_value < 0 or numeric_value > 100:
        raise ValueError(f"{name}_must_be_between_0_and_100")
    return numeric_value


def _clean_number(value: float | int | None) -> float | int | None:
    if value is None:
        return None
    rounded = float(
        Decimal(f"{float(value):.10f}").quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    )
    return int(rounded) if rounded.is_integer() else rounded


def _clean_weight(value: float | int) -> float:
    rounded = round(float(value), 6)
    return int(rounded) if rounded.is_integer() else rounded


def _unavailable_reason_code(component_key: str) -> str:
    aliases = {
        "behavior_quality_score": "behavior_quality_unavailable",
    }
    return aliases.get(component_key, f"{component_key}_unavailable")


def _join_reasons(reasons: list[str]) -> str | None:
    if not reasons:
        return None
    unique_reasons = list(dict.fromkeys(reasons))
    return ",".join(unique_reasons)
