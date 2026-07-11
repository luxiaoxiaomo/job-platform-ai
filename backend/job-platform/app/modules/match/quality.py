"""Match quality dashboard analytics."""

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.application.models import JobApplication
from app.modules.job.models import JobFavorite, JobVisit
from app.modules.match.models import MatchRuleMatchAuditModel
from app.modules.match.repository import MatchRuleConfigRepository
from app.modules.match.schemas import (
    MatchQualityAnomalyResponse,
    MatchQualityDashboardResponse,
    MatchQualityExperimentConfidenceResponse,
    MatchQualityMetricResponse,
    MatchQualityRuleVersionResponse,
    MatchQualitySegmentResponse,
    MatchQualityTuningSuggestionResponse,
    MatchQualityTimeBucketResponse,
)

QUALITY_SEGMENT_TYPES = (
    "city",
    "position_category",
    "standard_position",
    "job_tag",
    "rule_version",
    "experiment_bucket",
)
QUALITY_SAMPLE_INSUFFICIENT = 30
QUALITY_SAMPLE_USABLE = 100
QUALITY_GUARDRAIL = (
    "Draft suggestion only; do not modify rules automatically. Create a new rule version through rule editing "
    "and release governance before applying changes."
)


class MatchQualityService:
    """Aggregate audit facts into dashboard metrics and insights."""

    @staticmethod
    async def get_summary(
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_segment_type"
            )
        if created_from and created_to and created_from > created_to:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_created_range"
            )

        audits = await MatchRuleConfigRepository.list_quality_audits(
            db,
            experiment_id=experiment_id,
            rule_config_id=rule_config_id,
            scope=scope,
            template_key=template_key,
            created_from=created_from,
            created_to=created_to,
        )
        audits = MatchQualityService._filter_quality_audits(
            audits,
            city=city,
            position_category=position_category,
            standard_position_id=standard_position_id,
            job_tag=job_tag,
        )
        behavior_pairs = await MatchQualityService._quality_behavior_pairs(db, audits)
        summary = MatchQualityService._quality_metric(audits, behavior_pairs)

        rule_groups: dict[int | None, list[MatchRuleMatchAuditModel]] = {}
        bucket_groups: dict[str, list[MatchRuleMatchAuditModel]] = {
            "control": [],
            "treatment": [],
        }
        time_groups: dict[str, list[MatchRuleMatchAuditModel]] = {}
        for audit in audits:
            rule_groups.setdefault(audit.rule_config_id, []).append(audit)
            if audit.experiment_bucket:
                bucket_groups.setdefault(audit.experiment_bucket, []).append(audit)
            time_groups.setdefault(audit.created_at.date().isoformat(), []).append(
                audit
            )

        rule_versions = []
        for config_id, group in rule_groups.items():
            first = group[0]
            metric = MatchQualityService._quality_metric(group, behavior_pairs)
            rule_versions.append(
                MatchQualityRuleVersionResponse(
                    **metric.model_dump(),
                    rule_config_id=config_id,
                    rule_config_name=first.rule_config.name
                    if first.rule_config
                    else None,
                    rule_config_version=first.rule_config.version
                    if first.rule_config
                    else None,
                    rule_config_status=first.rule_config.status
                    if first.rule_config
                    else None,
                )
            )
        rule_versions.sort(
            key=lambda item: (item.rule_config_version or 0, item.rule_config_id or 0),
            reverse=True,
        )

        experiment_buckets = {
            bucket: MatchQualityService._quality_metric(group, behavior_pairs)
            for bucket, group in sorted(bucket_groups.items())
        }
        time_buckets = [
            MatchQualityTimeBucketResponse(
                **MatchQualityService._quality_metric(
                    group, behavior_pairs
                ).model_dump(),
                date=day,
            )
            for day, group in sorted(time_groups.items())
        ]
        segments = (
            MatchQualityService._quality_segments(
                audits,
                behavior_pairs,
                summary,
                segment_type=segment_type,
            )
            if include_insights
            else []
        )
        experiment_confidence = (
            MatchQualityService._quality_experiment_confidence(
                experiment_id,
                bucket_groups,
                behavior_pairs,
            )
            if include_insights
            else None
        )
        anomalies = (
            MatchQualityService._quality_anomalies(summary, segments)
            if include_insights
            else []
        )
        tuning_suggestions = (
            MatchQualityService._quality_tuning_suggestions(anomalies)
            if include_insights
            else []
        )

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
            filtered = [
                audit
                for audit in filtered
                if audit.job and (audit.job.city or "").strip().lower() == city_text
            ]
        if position_category:
            category_text = position_category.strip().lower()
            filtered = [
                audit
                for audit in filtered
                if audit.job
                and audit.job.standard_position
                and (audit.job.standard_position.category or "").strip().lower()
                == category_text
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
                if audit.job
                and any(
                    str(tag).strip().lower() == tag_text
                    for tag in (audit.job.tags or [])
                )
            ]
        return filtered

    @staticmethod
    async def _quality_behavior_pairs(
        db: AsyncSession,
        audits: list[MatchRuleMatchAuditModel],
    ) -> dict[str, set[tuple[int, int]]]:
        pairs = {
            (audit.job_id, audit.seeker_id)
            for audit in audits
            if audit.job_id and audit.seeker_id
        }
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
            "applications": {
                (int(job_id), int(seeker_id))
                for job_id, seeker_id in application_result.all()
            }
            & pairs,
            "favorites": {
                (int(job_id), int(seeker_id))
                for job_id, seeker_id in favorite_result.all()
            }
            & pairs,
            "visits": {
                (int(job_id), int(seeker_id))
                for job_id, seeker_id in visit_result.all()
            }
            & pairs,
        }

    @staticmethod
    def _quality_metric(
        audits: list[MatchRuleMatchAuditModel],
        behavior_pairs: dict[str, set[tuple[int, int]]],
    ) -> MatchQualityMetricResponse:
        match_count = len(audits)
        pairs = [
            (audit.job_id, audit.seeker_id)
            for audit in audits
            if audit.job_id and audit.seeker_id
        ]
        favorite_count = sum(1 for pair in pairs if pair in behavior_pairs["favorites"])
        application_count = sum(
            1 for pair in pairs if pair in behavior_pairs["applications"]
        )
        visit_count = sum(1 for pair in pairs if pair in behavior_pairs["visits"])

        def rate(count: int) -> float:
            return round(count / match_count * 100, 2) if match_count else 0

        low_count = sum(1 for audit in audits if audit.level == "low")
        return MatchQualityMetricResponse(
            match_count=match_count,
            avg_score=round(
                sum(audit.overall_score for audit in audits) / match_count, 2
            )
            if match_count
            else None,
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
            sample_status=MatchQualityService._quality_sample_status(match_count),
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
                for key, label in MatchQualityService._quality_segment_values(
                    audit, current_type
                ):
                    groups.setdefault((key, label), []).append(audit)

            for (key, label), group in groups.items():
                metric = MatchQualityService._quality_metric(group, behavior_pairs)
                application_delta = round(
                    metric.application_rate - summary.application_rate, 2
                )
                favorite_delta = round(metric.favorite_rate - summary.favorite_rate, 2)
                low_score_delta = round(
                    metric.low_score_rate - summary.low_score_rate, 2
                )
                segments.append(
                    MatchQualitySegmentResponse(
                        **metric.model_dump(),
                        segment_type=current_type,
                        segment_key=key,
                        segment_label=label,
                        application_rate_delta=application_delta,
                        favorite_rate_delta=favorite_delta,
                        low_score_rate_delta=low_score_delta,
                        risk_level=MatchQualityService._quality_segment_risk(
                            metric, application_delta, low_score_delta
                        ),
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
    def _quality_segment_values(
        audit: MatchRuleMatchAuditModel, segment_type: str
    ) -> list[tuple[str, str]]:
        unclassified = [("unclassified", "Unclassified")]
        if segment_type == "city":
            if audit.job and audit.job.city:
                return [(audit.job.city, audit.job.city)]
            return unclassified
        if segment_type == "position_category":
            if (
                audit.job
                and audit.job.standard_position
                and audit.job.standard_position.category
            ):
                return [
                    (
                        audit.job.standard_position.category,
                        audit.job.standard_position.category,
                    )
                ]
            return unclassified
        if segment_type == "standard_position":
            if audit.job and audit.job.standard_position:
                return [
                    (
                        str(audit.job.standard_position.id),
                        audit.job.standard_position.name,
                    )
                ]
            return unclassified
        if segment_type == "job_tag":
            if audit.job and isinstance(audit.job.tags, list) and audit.job.tags:
                return [
                    (str(tag), str(tag)) for tag in audit.job.tags if str(tag).strip()
                ]
            return unclassified
        if segment_type == "rule_version":
            if audit.rule_config:
                return [
                    (
                        str(audit.rule_config.id),
                        f"{audit.rule_config.name} V{audit.rule_config.version}",
                    )
                ]
            if audit.rule_config_id is not None:
                return [(str(audit.rule_config_id), str(audit.rule_config_id))]
            return unclassified
        if segment_type == "experiment_bucket":
            if audit.experiment_bucket:
                return [(audit.experiment_bucket, audit.experiment_bucket)]
            return unclassified
        return unclassified

    @staticmethod
    def _quality_segment_risk(
        metric: MatchQualityMetricResponse,
        application_delta: float,
        low_score_delta: float,
    ) -> str:
        if metric.sample_status == "insufficient":
            return "low"
        if metric.sample_status == "usable" and (
            application_delta <= -5 or low_score_delta >= 15
        ):
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

        control = MatchQualityService._quality_metric(
            bucket_groups.get("control", []), behavior_pairs
        )
        treatment = MatchQualityService._quality_metric(
            bucket_groups.get("treatment", []), behavior_pairs
        )
        sample_count = min(control.match_count, treatment.match_count)
        sample_status = MatchQualityService._quality_sample_status(sample_count)
        application_delta = round(
            treatment.application_rate - control.application_rate, 2
        )
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
            hint = (
                "Treatment application rate is above control by the business threshold."
            )
        elif application_delta <= -3:
            confidence_status = "treatment_likely_worse"
            hint = (
                "Treatment application rate is below control by the business threshold."
            )
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
            if (
                segment.sample_status == "insufficient"
                or segment.segment_key == "unclassified"
            ):
                continue
            if segment.application_rate_delta <= -5:
                severity = "high" if segment.sample_status == "usable" else "medium"
                anomalies.append(
                    MatchQualityService._quality_anomaly(
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
                    MatchQualityService._quality_anomaly(
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
                    MatchQualityService._quality_anomaly(
                        severity="high"
                        if segment.sample_status == "usable"
                        else "medium",
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
        anomalies.sort(
            key=lambda item: (severity_order[item.severity], item.metric_delta)
        )
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
                dimension_key = MatchQualityService._quality_dimension_for_segment(
                    anomaly.segment_type
                )
                action = "Review whether this segment is over-filtered; consider broadening logic or creating a scoped rule."
            elif anomaly.type == "high_score_low_conversion":
                suggestion_type = "narrow_logic"
                dimension_key = "skill"
                action = "Inspect high-scoring low-conversion samples; narrow overly broad skill or intention matches if confirmed."
            else:
                suggestion_type = "review_dimension"
                dimension_key = MatchQualityService._quality_dimension_for_segment(
                    anomaly.segment_type
                )
                action = (
                    "Review the segment's dimension snapshots before changing weights."
                )

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
                    confidence="medium"
                    if anomaly.sample_status == "limited"
                    else anomaly.severity,
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
