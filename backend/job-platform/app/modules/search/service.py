"""Search use cases."""
import re
from collections import Counter

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.job.models import Job
from app.modules.resume.models import ResumeBasicInfo, SeekerResume
from app.modules.search.repository import SearchRepository
from app.modules.search.schemas import (
    SearchJobItemResponse,
    SearchJobResponse,
    SearchResumeItemResponse,
    SearchResumeResponse,
)
from app.modules.user.models import User

METHOD = "keyword_semantic_fallback"


def _tokens(value: str) -> list[str]:
    text = (value or "").lower()
    chunks = re.findall(r"[a-z0-9+#.]+|[\u4e00-\u9fff]{2,}", text)
    tokens: list[str] = []
    for chunk in chunks:
        tokens.append(chunk)
        if re.search(r"[\u4e00-\u9fff]", chunk) and len(chunk) > 3:
            tokens.extend(chunk[index : index + 2] for index in range(len(chunk) - 1))
    return [token for token in tokens if token.strip()]


def _score(query: str, weighted_parts: list[tuple[str, float]]) -> tuple[float, list[str]]:
    query_tokens = _tokens(query)
    if not query_tokens:
        return 0.0, []
    token_counts = Counter(query_tokens)
    raw_score = 0.0
    reasons: list[str] = []
    seen: set[str] = set()
    for text, weight in weighted_parts:
        haystack = (text or "").lower()
        if not haystack:
            continue
        for token, count in token_counts.items():
            if token in haystack:
                raw_score += weight * count
                if token not in seen and len(reasons) < 5:
                    reasons.append(token)
                    seen.add(token)
    return min(100.0, round(raw_score * 12, 1)), reasons


def _job_parts(job: Job) -> list[tuple[str, float]]:
    return [
        (job.title, 3.0),
        (" ".join(job.tags or []), 2.6),
        (job.city, 1.8),
        (job.experience, 1.2),
        (job.education, 1.2),
        (job.requirement, 1.4),
        (job.description, 1.0),
        (job.benefits or "", 0.6),
    ]


def _tag_ref_names(tag_refs: list[dict] | None) -> str:
    names = []
    for item in tag_refs or []:
        name = str(item.get("name") or "").strip() if isinstance(item, dict) else ""
        if name:
            names.append(name)
    return " ".join(names)


def _has_tag_id(tag_refs: list[dict] | None, tag_id: int | None) -> bool:
    if tag_id is None:
        return True
    for item in tag_refs or []:
        if isinstance(item, dict) and int(item.get("id") or 0) == tag_id:
            return True
    return False


def _resume_parts(
    basic: ResumeBasicInfo | None,
    resume: SeekerResume | None,
    skills: list[str],
    chunks: list[str],
    tag_refs: list[dict] | None = None,
) -> list[tuple[str, float]]:
    return [
        (basic.target_position if basic else "", 3.0),
        (" ".join(skills), 2.6),
        (_tag_ref_names(tag_refs), 2.4),
        (basic.current_city if basic else "", 1.8),
        (basic.highest_education if basic else "", 1.2),
        (resume.parsed_snapshot if resume else "", 1.0),
        (" ".join(chunks), 1.0),
    ]


class SearchService:
    """Search candidates and jobs with a deterministic semantic fallback."""

    @staticmethod
    async def search_jobs(
        db: AsyncSession,
        current_user: User,
        *,
        query: str,
        tag_id: int | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> SearchJobResponse:
        if current_user.role != "seeker":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only seekers can search jobs")
        jobs = await SearchRepository.list_active_jobs(db)
        ranked = []
        for job in jobs:
            if not _has_tag_id(job.tag_refs, tag_id):
                continue
            score, reasons = _score(query, _job_parts(job))
            if score <= 0:
                continue
            ranked.append((score, reasons, job))
        ranked.sort(key=lambda item: (item[0], item[2].published_at or item[2].created_at), reverse=True)
        page = ranked[skip : skip + limit]
        return SearchJobResponse(
            query=query,
            method=METHOD,
            items=[
                SearchJobItemResponse(
                    id=job.id,
                    title=job.title,
                    city=job.city,
                    salary_min=job.salary_min,
                    salary_max=job.salary_max,
                    experience=job.experience,
                    education=job.education,
                    recruiter_display_name=job.recruiter.display_name if job.recruiter else None,
                    tags=job.tags or [],
                    tag_refs=job.tag_refs or [],
                    score=score,
                    reason=f"命中：{'、'.join(reasons)}" if reasons else "规则相关",
                    method=METHOD,
                    published_at=job.published_at,
                )
                for score, reasons, job in page
            ],
            total=len(ranked),
            skip=skip,
            limit=limit,
        )

    @staticmethod
    async def search_resumes(
        db: AsyncSession,
        current_user: User,
        *,
        query: str,
        tag_id: int | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> SearchResumeResponse:
        if current_user.role != "recruiter":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only recruiters can search resumes")
        rows = await SearchRepository.list_resume_candidates(db)
        profile_ids = [profile.id for profile, *_ in rows]
        seeker_ids = [profile.seeker_id for profile, *_ in rows]
        skill_map = await SearchRepository.skills_by_profile_ids(db, profile_ids)
        chunk_map = await SearchRepository.chunks_by_seeker_ids(db, seeker_ids)
        ranked = []
        for profile, basic, resume, user, seeker_profile in rows:
            tag_refs = profile.tag_refs or (seeker_profile.tag_refs if seeker_profile is not None else [])
            if not _has_tag_id(tag_refs, tag_id):
                continue
            skills = skill_map.get(profile.id, [])
            chunks = chunk_map.get(profile.seeker_id, [])
            score, reasons = _score(query, _resume_parts(basic, resume, skills, chunks, tag_refs))
            if score <= 0:
                continue
            ranked.append((score, reasons, profile, basic, resume, user, skills, tag_refs))
        ranked.sort(key=lambda item: (item[0], item[2].updated_at), reverse=True)
        page = ranked[skip : skip + limit]
        return SearchResumeResponse(
            query=query,
            method=METHOD,
            items=[
                SearchResumeItemResponse(
                    seeker_id=profile.seeker_id,
                    seeker_display_name=user.display_name if user else None,
                    structured_profile_id=profile.id,
                    real_name=basic.real_name if basic else None,
                    target_position=basic.target_position if basic else None,
                    current_city=basic.current_city if basic else None,
                    highest_education=basic.highest_education if basic else None,
                    work_years=basic.work_years if basic else None,
                    skills=skills[:8],
                    tag_refs=tag_refs or [],
                    score=score,
                    reason=f"命中：{'、'.join(reasons)}" if reasons else "规则相关",
                    method=METHOD,
                    updated_at=profile.updated_at,
                )
                for score, reasons, profile, basic, resume, user, skills, tag_refs in page
            ],
            total=len(ranked),
            skip=skip,
            limit=limit,
        )
