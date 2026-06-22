"""
Job posting business logic.
"""
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.base_data.repository import StandardPositionRepository
from app.modules.base_data.tag_refs import resolve_active_tag_refs, tag_ref_names
from app.modules.company_certification.repository import CompanyCertificationRepository
from app.modules.job.jd_parser import ALLOWED_JD_EXTENSIONS, extract_jd_text, parse_jd_fields
from app.modules.job.models import Job, JobFavorite, JobSubscription, JobVisit
from app.modules.job.repository import JobRepository
from app.modules.job.salary import suggest_salary
from app.modules.job.schemas import (
    JobCreate,
    JobJdParseResponse,
    JobJdTextParseRequest,
    JobListResponse,
    JobPublicContactResponse,
    JobFavoriteListResponse,
    JobFavoriteResponse,
    JobHistoryItemResponse,
    JobHistoryListResponse,
    JobResponse,
    JobSubscriptionCreate,
    JobSubscriptionListResponse,
    JobSubscriptionResponse,
    JobSubscriptionUpdate,
    JobVisitorListResponse,
    JobVisitorResponse,
    JobReview,
    JobSalarySuggestionRequest,
    JobSalarySuggestionResponse,
    SeekerNotificationListResponse,
    SeekerNotificationResponse,
    JobUpdate,
)
from app.modules.notification.service import NotificationService
from app.modules.notification.repository import NotificationRepository
from app.modules.user.models import User


VALID_STATUSES = {"draft", "pending", "active", "closed", "rejected"}
JOB_VISIBILITY_FIELDS = {
    "company_display_mode",
    "contact_phone_public",
    "contact_email_public",
    "contact_wechat_public",
}


def _approved_certification(certification):
    if certification is not None and certification.status == "approved":
        return certification
    return None


def _recruiter_public_display_name(job: Job, certification=None) -> Optional[str]:
    recruiter = job.recruiter
    certification = _approved_certification(certification)
    if job.company_display_mode == "anonymous":
        return None
    if job.company_display_mode == "company_name" and certification is not None:
        return certification.company_name
    return recruiter.display_name if recruiter else None


def _public_contact(job: Job, certification=None) -> JobPublicContactResponse:
    recruiter = job.recruiter
    certification = _approved_certification(certification)
    phone = None
    email = None
    wechat = None
    company_name = None
    if certification is not None and job.company_display_mode == "company_name":
        company_name = certification.company_name
    if job.contact_phone_public:
        if certification is not None and certification.applicant_phone:
            phone = certification.applicant_phone
        elif recruiter is not None and recruiter.phone_encrypted:
            from app.utils.encryption import encryptor

            phone = encryptor.decrypt(recruiter.phone_encrypted)
    if job.contact_email_public and certification is not None:
        email = certification.work_email
    if job.contact_wechat_public and certification is not None:
        wechat = certification.applicant_wechat
    return JobPublicContactResponse(company_name=company_name, phone=phone, email=email, wechat=wechat)


def _to_response(job: Job, certification=None, standard_position_name: str | None = None) -> JobResponse:
    return JobResponse(
        id=job.id,
        recruiter_id=job.recruiter_id,
        recruiter_display_name=_recruiter_public_display_name(job, certification),
        company_display_mode=job.company_display_mode or "display_name",
        contact_phone_public=bool(job.contact_phone_public),
        contact_email_public=bool(job.contact_email_public),
        contact_wechat_public=bool(job.contact_wechat_public),
        public_contact=_public_contact(job, certification),
        standard_position_id=job.standard_position_id,
        standard_position_name=standard_position_name,
        title=job.title,
        city=job.city,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        experience=job.experience,
        education=job.education,
        description=job.description,
        requirement=job.requirement,
        benefits=job.benefits,
        tags=job.tags,
        tag_refs=job.tag_refs or [],
        status=job.status,
        reject_reason=job.reject_reason,
        reviewer_id=job.reviewer_id,
        reviewed_at=job.reviewed_at,
        published_at=job.published_at,
        view_count=job.view_count or 0,
        conversation_count=getattr(job, "conversation_count", 0) or 0,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


async def _certification_for_job(db: AsyncSession, job: Job):
    return await CompanyCertificationRepository.get_by_recruiter_id(db, job.recruiter_id)


async def _to_response_with_certification(db: AsyncSession, job: Job) -> JobResponse:
    certification = await _certification_for_job(db, job)
    standard_position_name = None
    if job.standard_position_id is not None:
        position = await StandardPositionRepository.get_by_id(db, job.standard_position_id)
        standard_position_name = position.name if position is not None else None
    return _to_response(job, certification, standard_position_name)


async def _to_responses_with_certifications(db: AsyncSession, jobs: list[Job]) -> list[JobResponse]:
    return [await _to_response_with_certification(db, job) for job in jobs]


def _intent_score(view_count: int, has_conversation: bool, has_application: bool) -> int:
    score = 40 + min(view_count * 10, 25)
    if has_conversation:
        score += 20
    if has_application:
        score += 25
    return min(score, 100)


def _intent_tags(view_count: int, has_conversation: bool, has_application: bool, high_intent: bool) -> list[str]:
    tags: list[str] = []
    if view_count >= 2:
        tags.append("多次浏览")
    if has_conversation:
        tags.append("已咨询")
    if has_application:
        tags.append("已投递")
    if high_intent:
        tags.append("高意向")
    return tags or ["已浏览"]


def _normalize_text(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def _subscription_matches_job(subscription: JobSubscription, job: Job) -> bool:
    keywords = [_normalize_text(item) for item in (subscription.keywords or []) if _normalize_text(item)]
    haystack = " ".join(
        [
            _normalize_text(job.title),
            _normalize_text(job.description),
            _normalize_text(job.requirement),
            _normalize_text(" ".join(job.tags or [])),
        ]
    )
    if keywords and not any(keyword in haystack for keyword in keywords):
        return False

    city = _normalize_text(subscription.city)
    if city and city not in {"不限", "全国", "any", "all"} and city not in _normalize_text(job.city):
        return False

    if subscription.salary_min is not None and job.salary_max < subscription.salary_min:
        return False
    if subscription.salary_max is not None and job.salary_min > subscription.salary_max:
        return False
    return True


async def _subscription_to_response(
    db: AsyncSession,
    subscription: JobSubscription,
    matched_jobs: list[Job],
    match_count: int,
) -> JobSubscriptionResponse:
    return JobSubscriptionResponse(
        id=subscription.id,
        name=subscription.name,
        keywords=subscription.keywords or [],
        city=subscription.city,
        salary_min=subscription.salary_min,
        salary_max=subscription.salary_max,
        active=subscription.active,
        match_count=match_count,
        matched_jobs=await _to_responses_with_certifications(db, matched_jobs),
        created_at=subscription.created_at,
        updated_at=subscription.updated_at,
    )
async def _attach_conversation_counts(db: AsyncSession, jobs: list[Job]) -> list[Job]:
    counts = await JobRepository.count_conversations_by_job_ids(db, [job.id for job in jobs])
    for job in jobs:
        job.conversation_count = counts.get(job.id, 0)
    return jobs


class JobService:
    """Job posting use cases."""

    allowed_jd_extensions = ALLOWED_JD_EXTENSIONS

    @staticmethod
    async def _ensure_recruiter_can_publish(db: AsyncSession, current_user: User) -> None:
        if current_user.role != "recruiter":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only recruiters can publish jobs",
            )

        certification = await CompanyCertificationRepository.get_by_recruiter_id(db, current_user.id)
        if certification is None or certification.status != "approved":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Enterprise certification must be approved before publishing jobs",
            )

    @staticmethod
    async def _ensure_active_standard_position(db: AsyncSession, standard_position_id: int | None) -> None:
        if standard_position_id is None:
            return
        position = await StandardPositionRepository.get_by_id(db, standard_position_id)
        if position is None or position.status != "active":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Standard position not found")

    @staticmethod
    async def create(db: AsyncSession, current_user: User, data: JobCreate) -> JobResponse:
        await JobService._ensure_recruiter_can_publish(db, current_user)
        await JobService._ensure_active_standard_position(db, data.standard_position_id)
        tag_refs = await resolve_active_tag_refs(db, data.tag_ids)

        job = Job(
            recruiter_id=current_user.id,
            standard_position_id=data.standard_position_id,
            title=data.title,
            city=data.city,
            salary_min=data.salary_min,
            salary_max=data.salary_max,
            experience=data.experience,
            education=data.education,
            description=data.description,
            requirement=data.requirement,
            benefits=data.benefits,
            tags=tag_ref_names(tag_refs) if tag_refs else data.tags,
            tag_refs=tag_refs,
            company_display_mode=data.company_display_mode,
            contact_phone_public=data.contact_phone_public,
            contact_email_public=data.contact_email_public,
            contact_wechat_public=data.contact_wechat_public,
            status=data.status,
        )
        created = await JobRepository.create(db, job)
        created.recruiter = current_user
        return await _to_response_with_certification(db, created)

    @staticmethod
    async def parse_jd_upload(current_user: User, file: UploadFile) -> JobJdParseResponse:
        if current_user.role != "recruiter":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only recruiters can parse JD files",
            )

        original_name = file.filename or "job-description"
        extension = Path(original_name).suffix.lower()
        if extension not in JobService.allowed_jd_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only txt, md, csv, docx, xlsx, pdf, and common image formats are supported",
            )

        content = await file.read()
        if not content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file cannot be empty")
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Uploaded file is too large")

        upload_dir = Path("uploads") / "job_jds"
        upload_dir.mkdir(parents=True, exist_ok=True)
        saved_name = f"{current_user.id}_{uuid4().hex}{extension}"
        saved_path = upload_dir / saved_name
        saved_path.write_bytes(content)

        raw_text, confidence, source = await extract_jd_text(saved_path, original_name, content)
        if not raw_text.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No readable JD text was extracted from the uploaded file",
            )

        parsed = parse_jd_fields(raw_text, source=source, confidence=confidence)
        return JobJdParseResponse(
            file_name=original_name,
            source=parsed.source,
            confidence=parsed.confidence,
            raw_text=parsed.raw_text,
            title=parsed.title,
            city=parsed.city,
            salary_min=parsed.salary_min,
            salary_max=parsed.salary_max,
            experience=parsed.experience,
            education=parsed.education,
            description=parsed.description,
            requirement=parsed.requirement,
            benefits=parsed.benefits,
            tags=parsed.tags,
            missing_fields=parsed.missing_fields,
        )

    @staticmethod
    async def parse_jd_text(current_user: User, data: JobJdTextParseRequest) -> JobJdParseResponse:
        if current_user.role != "recruiter":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only recruiters can parse JD text",
            )

        parsed = parse_jd_fields(data.text, source="pasted_text", confidence=1.0)
        return JobJdParseResponse(
            file_name="pasted-jd.txt",
            source=parsed.source,
            confidence=parsed.confidence,
            raw_text=parsed.raw_text,
            title=parsed.title,
            city=parsed.city,
            salary_min=parsed.salary_min,
            salary_max=parsed.salary_max,
            experience=parsed.experience,
            education=parsed.education,
            description=parsed.description,
            requirement=parsed.requirement,
            benefits=parsed.benefits,
            tags=parsed.tags,
            missing_fields=parsed.missing_fields,
        )

    @staticmethod
    async def suggest_salary(current_user: User, data: JobSalarySuggestionRequest) -> JobSalarySuggestionResponse:
        if current_user.role != "recruiter":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only recruiters can get salary suggestions",
            )
        return suggest_salary(data)

    @staticmethod
    async def list_my_jobs(
        db: AsyncSession,
        current_user: User,
        skip: int = 0,
        limit: int = 20,
        status_filter: Optional[str] = None,
    ) -> JobListResponse:
        if status_filter and status_filter not in VALID_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job status")

        items, total = await JobRepository.list_by_recruiter(
            db,
            recruiter_id=current_user.id,
            skip=skip,
            limit=limit,
            status=status_filter,
        )
        await _attach_conversation_counts(db, items)
        return JobListResponse(
            items=await _to_responses_with_certifications(db, items),
            total=total,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    async def list_public_jobs(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        city: Optional[str] = None,
    ) -> JobListResponse:
        items, total = await JobRepository.list_public_active(db, skip=skip, limit=limit, city=city)
        await _attach_conversation_counts(db, items)
        return JobListResponse(
            items=await _to_responses_with_certifications(db, items),
            total=total,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    async def get_public_job(db: AsyncSession, job_id: int, current_user: Optional[User] = None) -> JobResponse:
        job = await JobRepository.get_by_id(db, job_id)
        if job is None or job.status != "active":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        job.view_count = (job.view_count or 0) + 1
        job = await JobRepository.update(db, job)
        if current_user is not None and current_user.role == "seeker":
            await JobRepository.create_visit(
                db,
                JobVisit(
                    job_id=job.id,
                    recruiter_id=job.recruiter_id,
                    seeker_id=current_user.id,
                    source="public_detail",
                ),
            )
        await _attach_conversation_counts(db, [job])
        return await _to_response_with_certification(db, job)

    @staticmethod
    async def list_my_history(
        db: AsyncSession,
        current_user: User,
        skip: int = 0,
        limit: int = 20,
    ) -> JobHistoryListResponse:
        rows, total = await JobRepository.list_history_by_seeker(
            db,
            seeker_id=current_user.id,
            skip=skip,
            limit=limit,
        )
        jobs = [row[0] for row in rows]
        await _attach_conversation_counts(db, jobs)
        favorite_ids = await JobRepository.favorite_job_ids(db, seeker_id=current_user.id, job_ids=[job.id for job in jobs])
        job_responses = {item.id: item for item in await _to_responses_with_certifications(db, jobs)}
        return JobHistoryListResponse(
            items=[
                JobHistoryItemResponse(
                    job=job_responses[job.id],
                    view_count=int(view_count or 0),
                    first_viewed_at=first_viewed_at,
                    last_viewed_at=last_viewed_at,
                    is_favorited=job.id in favorite_ids,
                )
                for job, view_count, first_viewed_at, last_viewed_at in rows
            ],
            total=total,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    async def list_my_favorites(
        db: AsyncSession,
        current_user: User,
        skip: int = 0,
        limit: int = 20,
    ) -> JobFavoriteListResponse:
        favorites, total = await JobRepository.list_favorites(
            db,
            seeker_id=current_user.id,
            skip=skip,
            limit=limit,
        )
        jobs = [favorite.job for favorite in favorites if favorite.job is not None]
        await _attach_conversation_counts(db, jobs)
        job_responses = {item.id: item for item in await _to_responses_with_certifications(db, jobs)}
        return JobFavoriteListResponse(
            items=[
                JobFavoriteResponse(
                    id=favorite.id,
                    job=job_responses[favorite.job.id],
                    created_at=favorite.created_at,
                )
                for favorite in favorites
                if favorite.job is not None
            ],
            total=total,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    async def add_my_favorite(db: AsyncSession, current_user: User, job_id: int) -> JobFavoriteResponse:
        job = await JobRepository.get_by_id(db, job_id)
        if job is None or job.status != "active":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        favorite = await JobRepository.get_favorite(db, seeker_id=current_user.id, job_id=job_id)
        if favorite is None:
            favorite = await JobRepository.create_favorite(
                db,
                JobFavorite(job_id=job.id, seeker_id=current_user.id),
            )
            favorite.job = job
        await _attach_conversation_counts(db, [favorite.job])
        return JobFavoriteResponse(
            id=favorite.id,
            job=await _to_response_with_certification(db, favorite.job),
            created_at=favorite.created_at,
        )

    @staticmethod
    async def remove_my_favorite(db: AsyncSession, current_user: User, job_id: int) -> dict[str, bool]:
        deleted = await JobRepository.delete_favorite(db, seeker_id=current_user.id, job_id=job_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Favorite not found")
        return {"ok": True}

    @staticmethod
    async def _subscription_matches(db: AsyncSession, subscription: JobSubscription) -> tuple[list[Job], int]:
        jobs = await JobRepository.list_active_jobs_for_matching(db)
        matched = [job for job in jobs if _subscription_matches_job(subscription, job)]
        await _attach_conversation_counts(db, matched[:5])
        return matched[:5], len(matched)

    @staticmethod
    async def _sync_subscription_match_notification(
        db: AsyncSession,
        subscription: JobSubscription,
        matched_jobs: list[Job],
        match_count: int,
    ) -> None:
        if not subscription.active or match_count <= 0:
            return
        matched_ids = [job.id for job in matched_jobs]
        preview_titles = "、".join(job.title for job in matched_jobs[:3]) or "暂无岗位预览"
        extra = "" if match_count <= 3 else f" 等 {match_count} 个岗位"
        action_url = f"/seeker/home?tab=subs&subscriptionId={subscription.id}"
        await NotificationService.create_or_update(
            db,
            recipient_id=subscription.seeker_id,
            type_="match",
            title=f"订阅「{subscription.name}」有 {match_count} 个匹配岗位",
            detail=f"{preview_titles}{extra}，点击查看",
            action_url=action_url,
            payload={
                "subscription_id": subscription.id,
                "subscription_name": subscription.name,
                "matched_job_ids": matched_ids,
                "match_count": match_count,
            },
            dedupe_key=f"subscription_match:{subscription.id}:{','.join(str(item) for item in matched_ids)}",
        )

    @staticmethod
    async def list_my_subscriptions(
        db: AsyncSession,
        current_user: User,
        skip: int = 0,
        limit: int = 20,
    ) -> JobSubscriptionListResponse:
        subscriptions, total = await JobRepository.list_subscriptions(
            db,
            seeker_id=current_user.id,
            skip=skip,
            limit=limit,
        )
        items: list[JobSubscriptionResponse] = []
        for subscription in subscriptions:
            matched_jobs, match_count = await JobService._subscription_matches(db, subscription)
            items.append(await _subscription_to_response(db, subscription, matched_jobs, match_count))
        return JobSubscriptionListResponse(items=items, total=total, skip=skip, limit=limit)

    @staticmethod
    async def list_my_notifications(
        db: AsyncSession,
        current_user: User,
        limit: int = 20,
    ) -> SeekerNotificationListResponse:
        if current_user.role != "seeker":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only seekers can list notifications")

        subscriptions, _ = await JobRepository.list_subscriptions(
            db,
            seeker_id=current_user.id,
            skip=0,
            limit=100,
        )
        for subscription in subscriptions:
            matched_jobs, match_count = await JobService._subscription_matches(db, subscription)
            await JobService._sync_subscription_match_notification(db, subscription, matched_jobs, match_count)

        notifications, total = await NotificationRepository.list_for_user(
            db,
            recipient_id=current_user.id,
            skip=0,
            limit=limit,
        )
        items: list[SeekerNotificationResponse] = []
        for notification in notifications:
            if notification.type != "match":
                continue
            payload = notification.payload or {}
            items.append(
                SeekerNotificationResponse(
                    id=str(notification.id),
                    type="match",
                    title=notification.title,
                    detail=notification.detail or "",
                    time="刚刚",
                    read=notification.read_at is not None,
                    subscription_id=int(payload.get("subscription_id") or 0),
                    subscription_name=str(payload.get("subscription_name") or ""),
                    matched_job_ids=[int(item) for item in payload.get("matched_job_ids", [])],
                    match_count=int(payload.get("match_count") or 0),
                )
            )

        return SeekerNotificationListResponse(items=items, total=total)

    @staticmethod
    async def create_my_subscription(
        db: AsyncSession,
        current_user: User,
        data: JobSubscriptionCreate,
    ) -> JobSubscriptionResponse:
        name = data.name or " / ".join(data.keywords[:2])
        subscription = await JobRepository.create_subscription(
            db,
            JobSubscription(
                seeker_id=current_user.id,
                name=name[:100],
                keywords=data.keywords,
                city=data.city,
                salary_min=data.salary_min,
                salary_max=data.salary_max,
                active=data.active,
            ),
        )
        matched_jobs, match_count = await JobService._subscription_matches(db, subscription)
        await JobService._sync_subscription_match_notification(db, subscription, matched_jobs, match_count)
        return await _subscription_to_response(db, subscription, matched_jobs, match_count)

    @staticmethod
    async def update_my_subscription(
        db: AsyncSession,
        current_user: User,
        subscription_id: int,
        data: JobSubscriptionUpdate,
    ) -> JobSubscriptionResponse:
        subscription = await JobRepository.get_subscription(
            db,
            seeker_id=current_user.id,
            subscription_id=subscription_id,
        )
        if subscription is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

        payload = data.model_dump(exclude_unset=True)
        next_min = payload.get("salary_min", subscription.salary_min)
        next_max = payload.get("salary_max", subscription.salary_max)
        if next_min is not None and next_max is not None and next_max < next_min:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid salary range")

        for field, value in payload.items():
            setattr(subscription, field, value)
        updated = await JobRepository.update_subscription(db, subscription)
        matched_jobs, match_count = await JobService._subscription_matches(db, updated)
        await JobService._sync_subscription_match_notification(db, updated, matched_jobs, match_count)
        return await _subscription_to_response(db, updated, matched_jobs, match_count)

    @staticmethod
    async def delete_my_subscription(db: AsyncSession, current_user: User, subscription_id: int) -> dict[str, bool]:
        deleted = await JobRepository.delete_subscription(
            db,
            seeker_id=current_user.id,
            subscription_id=subscription_id,
        )
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
        return {"ok": True}

    @staticmethod
    async def list_job_visitors(
        db: AsyncSession,
        current_user: User,
        job_id: int,
        skip: int = 0,
        limit: int = 20,
        sort: str = "time",
    ) -> JobVisitorListResponse:
        if sort not in {"time", "views", "intent"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid visitor sort")
        job = await JobRepository.get_by_id(db, job_id)
        if job is None or job.recruiter_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        rows, total = await JobRepository.list_visitors_by_job(
            db,
            job_id=job.id,
            recruiter_id=current_user.id,
            skip=skip,
            limit=limit,
            sort=sort,
        )
        seeker_ids = [int(row.seeker_id) for row in rows]
        conversation_seekers = await JobRepository.conversation_seeker_ids(db, job_id=job.id, seeker_ids=seeker_ids)
        application_seekers = await JobRepository.application_seeker_ids(db, job_id=job.id, seeker_ids=seeker_ids)

        items: list[JobVisitorResponse] = []
        for row in rows:
            seeker_id = int(row.seeker_id)
            view_count = int(row.view_count or 0)
            has_conversation = seeker_id in conversation_seekers
            has_application = seeker_id in application_seekers
            score = _intent_score(view_count, has_conversation, has_application)
            high_intent = score >= 70 or has_conversation or has_application
            items.append(
                JobVisitorResponse(
                    seeker_id=seeker_id,
                    seeker_display_name=row.seeker_display_name,
                    avatar_url=row.avatar_url,
                    view_count=view_count,
                    first_viewed_at=row.first_viewed_at,
                    last_viewed_at=row.last_viewed_at,
                    has_conversation=has_conversation,
                    has_application=has_application,
                    high_intent=high_intent,
                    intent_score=score,
                    tags=_intent_tags(view_count, has_conversation, has_application, high_intent),
                )
            )

        if sort == "intent":
            items.sort(key=lambda item: (item.intent_score, item.last_viewed_at), reverse=True)

        return JobVisitorListResponse(
            job_id=job.id,
            job_title=job.title,
            total_views=job.view_count or 0,
            unique_visitors=total,
            items=items,
            total=total,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    async def list_for_admin(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        status_filter: Optional[str] = None,
    ) -> JobListResponse:
        if status_filter and status_filter not in VALID_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job status")

        items, total = await JobRepository.list_for_admin(db, skip=skip, limit=limit, status=status_filter)
        await _attach_conversation_counts(db, items)
        return JobListResponse(
            items=await _to_responses_with_certifications(db, items),
            total=total,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    async def get_for_admin(db: AsyncSession, job_id: int) -> JobResponse:
        job = await JobRepository.get_by_id(db, job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        await _attach_conversation_counts(db, [job])
        return await _to_response_with_certification(db, job)

    @staticmethod
    async def update_my_job(db: AsyncSession, current_user: User, job_id: int, data: JobUpdate) -> JobResponse:
        job = await JobRepository.get_by_id(db, job_id)
        if job is None or job.recruiter_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        payload = data.model_dump(exclude_unset=True)
        if "standard_position_id" in payload:
            await JobService._ensure_active_standard_position(db, payload["standard_position_id"])
        if "tag_ids" in payload:
            tag_refs = await resolve_active_tag_refs(db, payload.pop("tag_ids"))
            payload["tag_refs"] = tag_refs
            payload["tags"] = tag_ref_names(tag_refs)
        if "salary_max" in payload and "salary_min" not in payload and payload["salary_max"] < job.salary_min:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid salary range")
        if "salary_min" in payload and "salary_max" not in payload and payload["salary_min"] > job.salary_max:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid salary range")

        for field, value in payload.items():
            setattr(job, field, value)

        if payload and any(field not in JOB_VISIBILITY_FIELDS for field in payload):
            job.status = "pending"
            job.reject_reason = None
            job.reviewer_id = None
            job.reviewed_at = None
            job.published_at = None

        updated = await JobRepository.update(db, job)
        return await _to_response_with_certification(db, updated)

    @staticmethod
    async def submit_my_job_for_review(db: AsyncSession, current_user: User, job_id: int) -> JobResponse:
        job = await JobRepository.get_by_id(db, job_id)
        if job is None or job.recruiter_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        if job.status == "pending":
            return await _to_response_with_certification(db, job)
        if job.status == "closed":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Closed jobs cannot be submitted for review")

        job.status = "pending"
        job.reject_reason = None
        job.reviewer_id = None
        job.reviewed_at = None
        job.published_at = None

        updated = await JobRepository.update(db, job)
        return await _to_response_with_certification(db, updated)
    @staticmethod
    async def review(db: AsyncSession, job_id: int, reviewer: User, data: JobReview) -> JobResponse:
        job = await JobRepository.get_by_id(db, job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        if data.action == "reject" and not data.reject_reason:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reject reason is required")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        job.status = "active" if data.action == "approve" else "rejected"
        job.reject_reason = None if data.action == "approve" else data.reject_reason
        job.reviewer_id = reviewer.id
        job.reviewed_at = now
        job.published_at = now if data.action == "approve" else None

        updated = await JobRepository.update(db, job, commit=False)
        await NotificationService.notify_job_reviewed(
            db,
            job=updated,
            action=data.action,
            reject_reason=data.reject_reason,
            commit=False,
        )
        await db.commit()
        await db.refresh(updated)
        return await _to_response_with_certification(db, updated)
