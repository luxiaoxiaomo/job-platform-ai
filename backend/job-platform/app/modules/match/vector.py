# ruff: noqa: E402
from __future__ import annotations

"""Replaceable vector recall adapters for intelligent matching runtime."""

from collections import Counter
from dataclasses import dataclass
import math
import re
from typing import Any, Protocol

from app.modules.job.models import Job


LOCAL_PROFILE_TEXT_PROVIDER = "local_profile_text"
LOCAL_PROFILE_TEXT_INDEX_VERSION = "local-profile-text-v1"


@dataclass(frozen=True)
class VectorRecallResult:
    semantic_score: float | None
    recall_source: str = "rule_only"
    degrade_reason: str | None = None
    provider: str | None = None
    vector_index_version: str | None = None
    similarity: float | None = None

    def as_audit_metadata(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "vector_index_version": self.vector_index_version,
            "similarity": _clean_number(self.similarity),
            "degrade_reason": self.degrade_reason,
        }


class VectorRecallProvider(Protocol):
    def score(self, *, job: Job, detail: Any, config: dict[str, Any]) -> VectorRecallResult:
        """Return a semantic score or a typed degradation result."""


class LocalProfileTextVectorProvider:
    """Deterministic local text-similarity adapter for development/demo runtime."""

    provider = LOCAL_PROFILE_TEXT_PROVIDER
    index_version = LOCAL_PROFILE_TEXT_INDEX_VERSION

    def score(self, *, job: Job, detail: Any, config: dict[str, Any]) -> VectorRecallResult:
        min_similarity = _float_config(config.get("min_similarity"), 0.62)
        job_terms = _job_terms(job)
        profile_terms = _profile_terms(detail)
        if not job_terms:
            return self._degraded("missing_job_vector")
        if not profile_terms:
            return self._degraded("missing_talent_vector")

        similarity = _cosine_similarity(job_terms, profile_terms)
        if similarity < min_similarity:
            return VectorRecallResult(
                semantic_score=None,
                recall_source="rule_only",
                degrade_reason="vector_low_similarity",
                provider=self.provider,
                vector_index_version=self.index_version,
                similarity=similarity,
            )
        return VectorRecallResult(
            semantic_score=round(similarity * 100, 2),
            recall_source="rule_and_vector",
            provider=self.provider,
            vector_index_version=self.index_version,
            similarity=similarity,
        )

    def _degraded(self, reason: str) -> VectorRecallResult:
        return VectorRecallResult(
            semantic_score=None,
            recall_source="rule_only",
            degrade_reason=reason,
            provider=self.provider,
            vector_index_version=self.index_version,
        )


def resolve_vector_recall_provider(config: dict[str, Any]) -> VectorRecallProvider | None:
    provider = str(config.get("provider") or "").strip()
    if provider == LOCAL_PROFILE_TEXT_PROVIDER:
        return LocalProfileTextVectorProvider()
    return None


def _job_terms(job: Job) -> Counter[str]:
    terms: list[str] = []
    terms.extend(_text_terms(job.title))
    terms.extend(_text_terms(job.description))
    terms.extend(_text_terms(job.requirement))
    terms.extend(_text_terms(job.education))
    terms.extend(_text_terms(job.experience))
    if isinstance(job.tags, list):
        for tag in job.tags:
            terms.extend(_text_terms(str(tag)))
    return Counter(terms)


def _profile_terms(detail: Any) -> Counter[str]:
    terms: list[str] = []
    basic = getattr(detail, "basic_info", None)
    if basic is not None:
        terms.extend(_text_terms(getattr(basic, "target_position", None)))
        terms.extend(_text_terms(getattr(basic, "highest_education", None)))
        terms.extend(_text_terms(getattr(basic, "current_city", None)))
    for skill in getattr(detail, "skills", []) or []:
        terms.extend(_text_terms(getattr(skill, "skill_name", None)))
        terms.extend(_text_terms(getattr(skill, "category", None)))
        terms.extend(_text_terms(getattr(skill, "skill_level", None)))
    for work in getattr(detail, "work_experiences", []) or []:
        terms.extend(_text_terms(getattr(work, "position", None)))
        terms.extend(_text_terms(getattr(work, "description", None)))
    for project in getattr(detail, "projects", []) or []:
        terms.extend(_text_terms(getattr(project, "project_name", None)))
        terms.extend(_text_terms(getattr(project, "role", None)))
        terms.extend(_text_terms(getattr(project, "description", None)))
        terms.extend(_text_terms(getattr(project, "responsibility", None)))
    return Counter(terms)


def _text_terms(value: Any) -> list[str]:
    if value is None:
        return []
    text = str(value).lower()
    return [
        token
        for token in re.findall(r"[a-z0-9][a-z0-9.+#_-]*", text)
        if len(token) >= 2
    ]


def _cosine_similarity(left: Counter[str], right: Counter[str]) -> float:
    common = set(left) & set(right)
    dot_product = sum(left[key] * right[key] for key in common)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm <= 0 or right_norm <= 0:
        return 0
    return dot_product / (left_norm * right_norm)


def _float_config(value: Any, default: float) -> float:
    if value is None:
        return default
    return float(value)


def _clean_number(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 6)
