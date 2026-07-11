import pytest

from app.modules.match.scoring import (
    HardConstraintItem,
    HybridScoreWeights,
    IntelligentScoreInput,
    IntelligentScoringConfig,
    IntelligentScoringService,
    ThreeDimensionalWeights,
)


def test_preview_score_uses_three_dimensional_base_and_bounded_profile_adjustment():
    result = IntelligentScoringService.preview_score(
        IntelligentScoreInput(
            semantic_score=84,
            tag_score=78,
            keyword_score=72,
            profile_coverage_score=82,
            behavior_quality_score=None,
        )
    )

    assert result.match_source == "hybrid"
    assert result.degrade_reason is None
    assert result.score_components.rule_score == 75.6
    assert result.score_components.base_match_score == 79.8
    assert result.score_components.final_match_score == 79.91
    assert result.actual_component_weights == {
        "semantic_score": 0.475,
        "tag_score": 0.285,
        "keyword_score": 0.19,
        "profile_coverage_score": 0.05,
        "behavior_quality_score": 0,
    }
    assert result.explanation_codes == [
        "semantic_match_high",
        "profile_coverage_valid",
        "behavior_quality_unavailable",
    ]


def test_behavior_score_null_does_not_punish_candidate_when_behavior_weight_is_configured():
    result = IntelligentScoringService.preview_score(
        IntelligentScoreInput(
            semantic_score=80,
            tag_score=80,
            keyword_score=80,
            profile_coverage_score=80,
            behavior_quality_score=None,
        ),
        config=IntelligentScoringConfig(
            final_weights=HybridScoreWeights(
                base_match_score=0.90,
                profile_coverage_score=0.05,
                behavior_quality_score=0.05,
            )
        ),
    )

    assert result.score_components.base_match_score == 80
    assert result.score_components.final_match_score == 80
    assert result.actual_component_weights["behavior_quality_score"] == 0
    assert result.weight_redistribution_reason == "behavior_quality_unavailable"


def test_low_rule_score_caps_high_semantic_candidate():
    result = IntelligentScoringService.preview_score(
        IntelligentScoreInput(
            semantic_score=100,
            tag_score=49,
            keyword_score=49,
            profile_coverage_score=100,
            behavior_quality_score=None,
        )
    )

    assert result.score_components.rule_score == 49
    assert result.score_components.uncapped_final_match_score == 75.78
    assert result.score_components.final_match_score == 69
    assert result.hard_constraint_result.final_cap == 69
    assert "low_rule_score_cap" in result.explanation_codes


def test_vector_unavailable_falls_back_to_rule_baseline_with_degrade_reason():
    result = IntelligentScoringService.preview_score(
        IntelligentScoreInput(
            semantic_score=None,
            tag_score=76,
            keyword_score=70,
            profile_coverage_score=90,
            behavior_quality_score=None,
            baseline_rule_score=73,
            vector_degrade_reason="vector_unavailable",
        )
    )

    assert result.match_source == "rule_baseline"
    assert result.degrade_reason == "vector_unavailable"
    assert result.score_components.semantic_score is None
    assert result.score_components.base_match_score == 73
    assert result.score_components.final_match_score == 73
    assert result.actual_component_weights == {
        "semantic_score": 0,
        "tag_score": 0,
        "keyword_score": 0,
        "profile_coverage_score": 0,
        "behavior_quality_score": 0,
    }


def test_invalid_weights_are_rejected():
    with pytest.raises(
        ValueError, match="three_dimensional_weights_total_must_equal_1"
    ):
        ThreeDimensionalWeights(semantic_score=0.6, tag_score=0.3, keyword_score=0.2)

    with pytest.raises(ValueError, match="hybrid_weights_total_must_equal_1"):
        HybridScoreWeights(
            base_match_score=0.95,
            profile_coverage_score=0.1,
            behavior_quality_score=0.1,
        )

    with pytest.raises(ValueError, match="profile_coverage_weight_must_not_exceed_0.1"):
        HybridScoreWeights(
            base_match_score=0.85, profile_coverage_score=0.15, behavior_quality_score=0
        )


def test_explicit_hard_constraints_apply_lowest_cap_after_scoring():
    result = IntelligentScoringService.preview_score(
        IntelligentScoreInput(
            semantic_score=90,
            tag_score=90,
            keyword_score=90,
            profile_coverage_score=90,
            hard_constraints=(
                HardConstraintItem(code="salary_no_overlap", final_cap=69),
                HardConstraintItem(code="city_mismatch", final_cap=59),
            ),
        )
    )

    assert result.score_components.uncapped_final_match_score == 90
    assert result.score_components.final_match_score == 59
    assert result.hard_constraint_result.final_cap == 59
    assert [item.code for item in result.hard_constraint_result.items] == [
        "salary_no_overlap",
        "city_mismatch",
    ]
