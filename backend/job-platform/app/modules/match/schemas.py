"""
Rule-based job matching schemas.
"""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


MatchLevel = Literal["high", "medium", "low"]


class MatchJobSummaryResponse(BaseModel):
    """Job fields used by seeker-job matching."""

    id: int
    title: str
    city: str
    salary_min: int
    salary_max: int


class MatchDimensionResponse(BaseModel):
    """One explainable matching dimension."""

    key: str
    label: str
    score: int = Field(ge=0, le=100)
    weight: float
    configured_weight: float
    effective_weight: float
    weighted_score: float
    matched: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    explanation: str
    description: str
    scoring_method: str
    logic: dict[str, Any] = Field(default_factory=dict)


class MatchRuleDimensionResponse(BaseModel):
    """One dimension in a match rule config."""

    key: str
    label: str
    weight: float
    configured_weight: float
    effective_weight: float
    enabled: bool
    description: str
    scoring_method: str
    logic: dict[str, Any] = Field(default_factory=dict)
    sort_order: int


class MatchRuleConfigResponse(BaseModel):
    """Rule config metadata returned to frontend."""

    id: int | str | None = None
    name: str
    strategy: str
    scope: str
    template_key: str = "default"
    template_name: str = "Default template"
    status: str
    version: int
    description: str
    parent_version_id: int | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    created_by: int | None = None
    updated_by: int | None = None
    configured_total_weight: float
    effective_total_weight: float
    dimensions: list[MatchRuleDimensionResponse]
    updated_at: datetime


class MatchRuleDimensionUpdateRequest(BaseModel):
    """Editable fields for one match rule dimension."""

    key: str
    label: str
    weight: float = Field(ge=0, le=100)
    enabled: bool = True
    description: str = ""
    scoring_method: str = ""
    logic: dict[str, Any] = Field(default_factory=dict)
    sort_order: int = Field(ge=0)


class MatchRuleConfigVersionCreateRequest(BaseModel):
    """Create a new rule config version from an existing config."""

    name: str
    description: str = ""
    status: str = Field(pattern="^(draft|active|testing|archived)$")
    scope: str = "global"
    template_key: str | None = None
    template_name: str | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    dimensions: list[MatchRuleDimensionUpdateRequest] = Field(min_length=1)


class MatchRuleTemplateCreateRequest(MatchRuleConfigVersionCreateRequest):
    """Create a first version for a new rule template."""

    template_key: str = Field(min_length=1, max_length=80)
    template_name: str = Field(min_length=1, max_length=120)


class MatchRuleConfigVersionCreateResponse(BaseModel):
    """Response after creating a new rule config version."""

    message: str = "rule_config_version_created"
    config: MatchRuleConfigResponse


class MatchRuleConfigListResponse(BaseModel):
    """Paginated match rule config list."""

    items: list[MatchRuleConfigResponse] = Field(default_factory=list)
    total: int
    skip: int = 0
    limit: int = 20


class MatchRuleDimensionDiffResponse(BaseModel):
    """One dimension diff between two rule config versions."""

    key: str
    label: str
    change_type: Literal["added", "removed", "changed", "unchanged"]
    base_weight: float | None = None
    target_weight: float | None = None
    weight_delta: float | None = None
    base_enabled: bool | None = None
    target_enabled: bool | None = None
    enabled_changed: bool = False
    label_changed: bool = False
    description_changed: bool = False
    scoring_method_changed: bool = False
    logic_changed: bool = False


class MatchRuleConfigCompareResponse(BaseModel):
    """Compare two rule config versions."""

    base: MatchRuleConfigResponse
    target: MatchRuleConfigResponse
    dimensions: list[MatchRuleDimensionDiffResponse]
    summary: dict[str, int]


class MatchRuleRollbackRequest(BaseModel):
    """Create a new version by copying a historical target version."""

    target_config_id: int
    status: str = Field(default="active", pattern="^(draft|active|testing|archived)$")
    name: str | None = None
    description: str | None = None


class MatchRuleReleaseCheckItemResponse(BaseModel):
    """One release check blocker or warning."""

    code: str
    message: str
    resource_type: str | None = None
    resource_id: int | None = None


class MatchRuleReleaseCheckResponse(BaseModel):
    """Pre-publish validation result for one rule config."""

    rule_config_id: int
    scope: str
    template_key: str
    status: str
    current_active_config_id: int | None = None
    can_publish: bool
    blockers: list[MatchRuleReleaseCheckItemResponse] = Field(default_factory=list)
    warnings: list[MatchRuleReleaseCheckItemResponse] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)


class MatchRulePublishRequest(BaseModel):
    """Publish a draft/testing rule config as the active version."""

    reason: str = Field(min_length=1, max_length=500)
    confirm_warnings: bool = False


class MatchRulePublishResponse(BaseModel):
    """Response after publishing a rule config."""

    message: str = "match_rule_config_published"
    config: MatchRuleConfigResponse
    archived_config_ids: list[int] = Field(default_factory=list)
    release_check: MatchRuleReleaseCheckResponse


class MatchRuleExperimentCreateRequest(BaseModel):
    """Create a gray/AB test entry for rule config versions."""

    name: str
    description: str = ""
    scope: str = "global"
    template_key: str = "default"
    status: str = Field(default="draft", pattern="^(draft|running|paused|ended)$")
    traffic_percent: int = Field(ge=0, le=100)
    control_config_id: int
    treatment_config_id: int
    audience: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime | None = None
    ended_at: datetime | None = None


class MatchRuleExperimentStatusUpdateRequest(BaseModel):
    """Update experiment lifecycle status."""

    status: Literal["running", "paused", "ended"]
    reason: str = Field(min_length=1, max_length=500)


class MatchRuleExperimentResponse(BaseModel):
    """Gray/AB test entry response."""

    id: int
    name: str
    description: str
    scope: str
    template_key: str
    status: str
    traffic_percent: int
    control_config_id: int
    treatment_config_id: int
    audience: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime | None = None
    ended_at: datetime | None = None
    created_by: int | None = None
    updated_by: int | None = None
    created_at: datetime
    updated_at: datetime


class MatchRuleExperimentListResponse(BaseModel):
    """Paginated rule experiment list."""

    items: list[MatchRuleExperimentResponse] = Field(default_factory=list)
    total: int
    skip: int = 0
    limit: int = 20


class MatchRuleExperimentStatusUpdateResponse(BaseModel):
    """Response after updating experiment lifecycle status."""

    message: str = "match_rule_experiment_status_updated"
    experiment: MatchRuleExperimentResponse


class MatchSourceResponse(BaseModel):
    """Source metadata for the generated match analysis."""

    strategy: str = "rule_v1"
    profile_parse_run_id: int | None = None
    job_id: int
    rule_config_id: int | str | None = None
    experiment_id: int | None = None
    experiment_bucket: Literal["control", "treatment"] | None = None
    audit_id: int | None = None
    scope: str = "global"
    template_key: str = "default"
    generated_at: datetime


class MatchAuditJobSummaryResponse(BaseModel):
    """Job summary attached to one match audit."""

    id: int
    title: str
    city: str | None = None


class MatchAuditSeekerSummaryResponse(BaseModel):
    """Seeker summary attached to one match audit."""

    id: int
    display_name: str | None = None


class MatchAuditRuleConfigSummaryResponse(BaseModel):
    """Rule config summary attached to one match audit."""

    id: int
    name: str
    version: int
    status: str


class MatchAuditExperimentSummaryResponse(BaseModel):
    """Experiment summary attached to one match audit."""

    id: int
    name: str
    status: str


class MatchRuleAuditResponse(BaseModel):
    """Persisted match audit record."""

    id: int
    job_id: int
    seeker_id: int
    application_id: int | None = None
    profile_parse_run_id: int | None = None
    rule_config_id: int | None = None
    experiment_id: int | None = None
    experiment_bucket: Literal["control", "treatment"] | None = None
    scope: str
    template_key: str
    source: str
    overall_score: int
    level: str
    recommendation: str
    dimension_scores: list[dict[str, Any]] = Field(default_factory=list)
    job: MatchAuditJobSummaryResponse | None = None
    seeker: MatchAuditSeekerSummaryResponse | None = None
    rule_config: MatchAuditRuleConfigSummaryResponse | None = None
    experiment: MatchAuditExperimentSummaryResponse | None = None
    created_at: datetime


class MatchRuleAuditListResponse(BaseModel):
    """Paginated match audit list."""

    items: list[MatchRuleAuditResponse] = Field(default_factory=list)
    total: int
    skip: int = 0
    limit: int = 20


class MatchRuleOperationAuditResponse(BaseModel):
    """Admin operation audit record."""

    id: int
    actor_id: int | None = None
    action: str
    resource_type: str
    resource_id: int
    reason: str
    before_snapshot: dict[str, Any] | None = None
    after_snapshot: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class MatchRuleOperationAuditListResponse(BaseModel):
    """Paginated rule operation audit list."""

    items: list[MatchRuleOperationAuditResponse] = Field(default_factory=list)
    total: int
    skip: int = 0
    limit: int = 20


class MatchRuleExperimentBucketEffectResponse(BaseModel):
    """Aggregated effect metrics for one experiment bucket."""

    match_count: int = 0
    avg_score: float | None = None
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0


class MatchRuleExperimentEffectResponse(BaseModel):
    """Experiment effect query response."""

    experiment_id: int
    scope: str
    template_key: str
    traffic_percent: int
    buckets: dict[str, MatchRuleExperimentBucketEffectResponse]


class MatchQualityMetricResponse(BaseModel):
    """Aggregated quality and downstream behavior metrics."""

    match_count: int = 0
    avg_score: float | None = None
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    favorite_count: int = 0
    application_count: int = 0
    visit_count: int = 0
    favorite_rate: float = 0
    application_rate: float = 0
    visit_rate: float = 0
    low_score_rate: float = 0
    sample_status: Literal["insufficient", "limited", "usable"] = "insufficient"


class MatchQualityRuleVersionResponse(MatchQualityMetricResponse):
    """Quality metrics grouped by rule version."""

    rule_config_id: int | None = None
    rule_config_name: str | None = None
    rule_config_version: int | None = None
    rule_config_status: str | None = None


class MatchQualityTimeBucketResponse(MatchQualityMetricResponse):
    """Quality metrics grouped by calendar date."""

    date: str


class MatchQualitySegmentResponse(MatchQualityMetricResponse):
    """Quality metrics grouped by one operations segment."""

    segment_type: str
    segment_key: str
    segment_label: str
    application_rate_delta: float = 0
    favorite_rate_delta: float = 0
    low_score_rate_delta: float = 0
    risk_level: Literal["low", "medium", "high"] = "low"


class MatchQualityExperimentConfidenceResponse(BaseModel):
    """Business-threshold confidence hint for one experiment."""

    experiment_id: int | None = None
    control_match_count: int = 0
    treatment_match_count: int = 0
    control_application_rate: float = 0
    treatment_application_rate: float = 0
    application_rate_delta: float = 0
    favorite_rate_delta: float = 0
    avg_score_delta: float | None = None
    sample_status: Literal["insufficient", "limited", "usable"] = "insufficient"
    confidence_status: Literal[
        "not_applicable",
        "insufficient_sample",
        "treatment_likely_better",
        "treatment_likely_worse",
        "no_clear_difference",
    ] = "not_applicable"
    decision_hint: str = ""


class MatchQualityAnomalyResponse(BaseModel):
    """One quality anomaly hint derived from visible segment metrics."""

    severity: Literal["low", "medium", "high"]
    type: str
    segment_type: str
    segment_key: str
    segment_label: str
    evidence: str
    metric_delta: float = 0
    sample_status: Literal["insufficient", "limited", "usable"] = "insufficient"
    suggested_next_action: str


class MatchQualityTuningSuggestionResponse(BaseModel):
    """Draft tuning suggestion; never mutates rule configs automatically."""

    suggestion_type: Literal[
        "lower_weight",
        "raise_weight",
        "narrow_logic",
        "broaden_logic",
        "review_dimension",
        "run_experiment",
    ]
    dimension_key: str
    priority: Literal["low", "medium", "high"]
    affected_segment: str
    evidence: str
    proposed_action: str
    confidence: Literal["low", "medium", "high"]
    guardrail: str


class MatchQualityDashboardResponse(BaseModel):
    """Admin match quality dashboard response."""

    filters: dict[str, Any] = Field(default_factory=dict)
    summary: MatchQualityMetricResponse
    rule_versions: list[MatchQualityRuleVersionResponse] = Field(default_factory=list)
    experiment_buckets: dict[str, MatchQualityMetricResponse] = Field(default_factory=dict)
    time_buckets: list[MatchQualityTimeBucketResponse] = Field(default_factory=list)
    segments: list[MatchQualitySegmentResponse] = Field(default_factory=list)
    experiment_confidence: MatchQualityExperimentConfidenceResponse | None = None
    anomalies: list[MatchQualityAnomalyResponse] = Field(default_factory=list)
    tuning_suggestions: list[MatchQualityTuningSuggestionResponse] = Field(default_factory=list)


class JobMatchResponse(BaseModel):
    """Rule-based seeker-job match analysis."""

    job: MatchJobSummaryResponse
    overall_score: int = Field(ge=0, le=100)
    level: MatchLevel
    recommendation: str
    summary: str
    weights: dict[str, float]
    configured_weights: dict[str, float]
    effective_weights: dict[str, float]
    rule_config: MatchRuleConfigResponse
    dimensions: list[MatchDimensionResponse]
    highlights: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    source: MatchSourceResponse
