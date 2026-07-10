"""
Seeker resume business logic.
"""
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.base_data.tag_refs import resolve_active_tag_refs
from app.modules.resume.chunking import hash_text, split_resume_text
from app.modules.resume.extractors import ResumeExtractionError, extract_resume_text
from app.modules.resume.models import (
    ResumeBasicInfo,
    ResumeCertificate,
    ResumeChunk,
    ResumeEducation,
    ResumeExtractedText,
    ResumeParseRun,
    ResumeProject,
    ResumeSkill,
    ResumeStructuredProfile,
    ResumeUpload,
    ResumeWorkExperience,
    SeekerResume,
)
from app.modules.resume.repository import ResumeRepository
from app.modules.resume.schemas import (
    ResumeChunkPreviewResponse,
    ResumeBasicInfoResponse,
    ResumeCertificateResponse,
    ResumeEducationResponse,
    ResumeExtractedTextPreviewResponse,
    ResumeProjectResponse,
    ResumeParseRunResponse,
    ResumeParseRunDetailResponse,
    ResumeResponse,
    ResumeStatusResponse,
    ResumeStructuredConfirmRequest,
    ResumeProfileCompletenessGroupResponse,
    ResumeProfileCompletenessResponse,
    ResumeProfileReviewResponse,
    ResumeProfileSourceLinksResponse,
    ResumeProfileSummaryListsResponse,
    ResumeProfileSummaryResponse,
    ResumeStructuredProfileCreateRequest,
    ResumeStructuredProfileDetailResponse,
    ResumeStructuredProfileResponse,
    ResumeStructuredProjectionRequest,
    ResumeStructuredProjectionResponse,
    ResumeSkillResponse,
    ResumeUploadHistoryItemResponse,
    ResumeUploadResponse,
    ResumeUploadResultResponse,
    ResumeWorkExperienceResponse,
)
from app.modules.seeker_profile.models import SeekerProfile
from app.modules.user.models import User


def _to_response(resume: SeekerResume) -> ResumeResponse:
    return ResumeResponse(
        id=resume.id,
        seeker_id=resume.seeker_id,
        file_url=resume.file_url,
        file_name=resume.file_name,
        content_type=resume.content_type,
        file_size=resume.file_size,
        parsed_snapshot=resume.parsed_snapshot,
        current_upload_id=resume.current_upload_id,
        current_parse_run_id=resume.current_parse_run_id,
        created_at=resume.created_at,
        updated_at=resume.updated_at,
    )


def _upload_to_response(upload: ResumeUpload) -> ResumeUploadResponse:
    return ResumeUploadResponse(
        id=upload.id,
        seeker_id=upload.seeker_id,
        resume_id=upload.resume_id,
        file_url=upload.file_url,
        original_file_name=upload.original_file_name,
        content_type=upload.content_type,
        file_ext=upload.file_ext,
        file_size=upload.file_size,
        status=upload.status,
        error_message=upload.error_message,
        created_at=upload.created_at,
        updated_at=upload.updated_at,
    )


def _parse_run_to_response(parse_run: ResumeParseRun) -> ResumeParseRunResponse:
    return ResumeParseRunResponse(
        id=parse_run.id,
        upload_id=parse_run.upload_id,
        seeker_id=parse_run.seeker_id,
        status=parse_run.status,
        parser_version=parse_run.parser_version,
        prompt_version=parse_run.prompt_version,
        extractor=parse_run.extractor,
        started_at=parse_run.started_at,
        finished_at=parse_run.finished_at,
        error_code=parse_run.error_code,
        error_message=parse_run.error_message,
        metrics_json=parse_run.metrics_json,
        created_at=parse_run.created_at,
        updated_at=parse_run.updated_at,
    )


def _text_preview(text: str, max_chars: int = 1200) -> str:
    stripped = text.strip()
    if len(stripped) <= max_chars:
        return stripped
    return f"{stripped[:max_chars].rstrip()}..."


def _extracted_text_to_preview(extracted_text: ResumeExtractedText) -> ResumeExtractedTextPreviewResponse:
    return ResumeExtractedTextPreviewResponse(
        id=extracted_text.id,
        parse_run_id=extracted_text.parse_run_id,
        upload_id=extracted_text.upload_id,
        text_preview=_text_preview(extracted_text.text),
        language=extracted_text.language,
        quality_score=extracted_text.quality_score,
        page_count=extracted_text.page_count,
        char_count=extracted_text.char_count,
        created_at=extracted_text.created_at,
    )


def _chunk_to_preview(chunk: ResumeChunk) -> ResumeChunkPreviewResponse:
    return ResumeChunkPreviewResponse(
        id=chunk.id,
        parse_run_id=chunk.parse_run_id,
        upload_id=chunk.upload_id,
        chunk_index=chunk.chunk_index,
        section=chunk.section,
        content_preview=_text_preview(chunk.content, max_chars=500),
        token_count=chunk.token_count,
        embedding_status=chunk.embedding_status,
        created_at=chunk.created_at,
    )


def _structured_profile_to_response(profile: ResumeStructuredProfile) -> ResumeStructuredProfileResponse:
    return ResumeStructuredProfileResponse(
        id=profile.id,
        seeker_id=profile.seeker_id,
        upload_id=profile.upload_id,
        parse_run_id=profile.parse_run_id,
        schema_version=profile.schema_version,
        prompt_config_id=profile.prompt_config_id,
        prompt_version=profile.prompt_version,
        source=profile.source,
        status=profile.status,
        confidence_score=profile.confidence_score,
        structured_json=profile.structured_json,
        tag_refs=profile.tag_refs or [],
        validation_errors=profile.validation_errors,
        confirmed_at=profile.confirmed_at,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def _basic_info_to_response(row: ResumeBasicInfo) -> ResumeBasicInfoResponse:
    return ResumeBasicInfoResponse(
        id=row.id,
        real_name=row.real_name,
        gender=row.gender,
        age=row.age,
        phone=row.phone,
        email=row.email,
        highest_education=row.highest_education,
        work_years=row.work_years,
        current_city=row.current_city,
        target_position=row.target_position,
        expected_salary=row.expected_salary,
        source=row.source,
        confidence_score=row.confidence_score,
        created_at=row.created_at,
    )


def _education_to_response(row: ResumeEducation) -> ResumeEducationResponse:
    return ResumeEducationResponse(
        id=row.id,
        school_name=row.school_name,
        major=row.major,
        degree=row.degree,
        education_level=row.education_level,
        start_date=row.start_date,
        end_date=row.end_date,
        is_full_time=row.is_full_time,
        source=row.source,
        confidence_score=row.confidence_score,
        sort_order=row.sort_order,
        created_at=row.created_at,
    )


def _work_to_response(row: ResumeWorkExperience) -> ResumeWorkExperienceResponse:
    return ResumeWorkExperienceResponse(
        id=row.id,
        company_name=row.company_name,
        position=row.position,
        start_date=row.start_date,
        end_date=row.end_date,
        description=row.description,
        source=row.source,
        confidence_score=row.confidence_score,
        sort_order=row.sort_order,
        created_at=row.created_at,
    )


def _project_to_response(row: ResumeProject) -> ResumeProjectResponse:
    return ResumeProjectResponse(
        id=row.id,
        project_name=row.project_name,
        role=row.role,
        start_date=row.start_date,
        end_date=row.end_date,
        description=row.description,
        responsibility=row.responsibility,
        source=row.source,
        confidence_score=row.confidence_score,
        sort_order=row.sort_order,
        created_at=row.created_at,
    )


def _skill_to_response(row: ResumeSkill) -> ResumeSkillResponse:
    return ResumeSkillResponse(
        id=row.id,
        skill_name=row.skill_name,
        skill_level=row.skill_level,
        category=row.category,
        source=row.source,
        confidence_score=row.confidence_score,
        sort_order=row.sort_order,
        created_at=row.created_at,
    )


def _certificate_to_response(row: ResumeCertificate) -> ResumeCertificateResponse:
    return ResumeCertificateResponse(
        id=row.id,
        certificate_name=row.certificate_name,
        certificate_type=row.certificate_type,
        issuer=row.issuer,
        issued_at=row.issued_at,
        source=row.source,
        confidence_score=row.confidence_score,
        sort_order=row.sort_order,
        created_at=row.created_at,
    )


def _dict_value(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return None


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return str(value)


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _item_confidence(item: Any, default: float | None = None) -> float | None:
    if not isinstance(item, dict):
        return default
    confidence = _float_or_none(_dict_value(item, "confidence_score", "confidence", "score"))
    return default if confidence is None else confidence


def _list_from_json(data: dict[str, Any], *keys: str) -> list[Any]:
    for key in keys:
        value = data.get(key)
        if isinstance(value, list):
            return value
    return []


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list | tuple | set | dict):
        return bool(value)
    return True


PROFILE_COMPLETENESS_FIELD_LABELS = {
    "real_name": "姓名",
    "gender": "性别",
    "highest_education": "最高学历",
    "work_years": "工作年限",
    "target_position": "目标岗位",
    "phone": "手机号",
    "email": "邮箱",
    "current_city": "当前城市",
    "skills": "技能",
    "educations": "教育经历",
    "work_experiences": "工作经历",
}


def _profile_field_label(field: str) -> str:
    return PROFILE_COMPLETENESS_FIELD_LABELS.get(field, field)


def _source_text(item: Any) -> str | None:
    if isinstance(item, dict):
        return _string_or_none(_dict_value(item, "raw_text", "source_text", "text"))
    return _string_or_none(item)


_RESUME_VALUE_STOP_LABELS = [
    "姓名",
    "真实姓名",
    "性别",
    "年龄",
    "出生年月",
    "出生日期",
    "生日",
    "手机",
    "手机号",
    "电话",
    "联系电话",
    "邮箱",
    "最高学历",
    "学历",
    "教育程度",
    "工作年限",
    "工作经验",
    "从业经验",
    "经验",
    "所在城市",
    "当前城市",
    "城市",
    "地点",
    "职业方向",
    "求职意向",
    "目标岗位",
    "求职岗位",
    "应聘岗位",
    "期望职位",
    "职位",
    "岗位",
    "期望薪资",
    "薪资",
    "技能",
    "项目",
    "教育经历",
    "工作经历",
    "证书",
    "Name",
    "Full Name",
    "Gender",
    "Age",
    "Birth",
    "Mobile",
    "Phone",
    "Email",
    "E-mail",
    "Highest Education",
    "Education",
    "Degree",
    "Work Years",
    "Work Experience",
    "Years of Experience",
    "Experience",
    "City",
    "Target Position",
    "Career Direction",
    "Desired Position",
    "Position",
    "Salary",
    "Skills",
    "Project",
    "Projects",
    "School",
    "Major",
    "Company",
]


_RESUME_TITLE_WORDS = ["简历", "个人简历", "求职", "应聘", "个人总结", "自我评价", "工作背景", "工作经历", "项目经历", "教育经历", "技能", "resume", "cv"]


def _resume_label_pattern(labels: list[str]) -> str:
    parts = []
    for label in sorted(labels, key=len, reverse=True):
        escaped = re.escape(label)
        if re.fullmatch(r"[A-Za-z][A-Za-z ]*", label):
            escaped = rf"(?<![A-Za-z]){escaped}(?![A-Za-z])"
        parts.append(escaped)
    return "|".join(parts)


def _clean_resume_value(value: str | None, stop_labels: list[str] | None = None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if stop_labels:
        label_pattern = _resume_label_pattern(stop_labels)
        cleaned = re.split(rf"\s+(?=(?:{label_pattern})\s*[:：])", cleaned, maxsplit=1, flags=re.IGNORECASE)[0]
    cleaned = re.split(r"[，,；;|/]", cleaned, maxsplit=1)[0].strip(" ：:\t\r\n")
    return cleaned or None


def _extract_labeled_value(text: str, labels: list[str], max_chars: int = 80) -> str | None:
    label_pattern = _resume_label_pattern(labels)
    pattern = rf"(?:{label_pattern})\s*[:：]\s*([^\n\r]{{1,{max_chars}}})"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return _clean_resume_value(match.group(1), _RESUME_VALUE_STOP_LABELS) if match else None


def _normalize_resume_gender(value: str | None) -> str | None:
    cleaned = _clean_resume_value(value)
    if not cleaned:
        return None
    lowered = cleaned.lower()
    if cleaned.startswith("男") or lowered.startswith("male") or lowered in {"m"}:
        return "男"
    if cleaned.startswith("女") or lowered.startswith("female") or lowered in {"f"}:
        return "女"
    return cleaned


def _map_resume_education_level(text: str | None) -> str | None:
    if not text:
        return None
    for level in ["博士", "硕士", "研究生", "本科", "大专", "专科", "高中", "中专"]:
        if level in text:
            return "大专" if level == "专科" else level
    lowered = text.lower()
    mappings = [
        ("ph.d", "博士"),
        ("phd", "博士"),
        ("doctor", "博士"),
        ("master", "硕士"),
        ("mba", "硕士"),
        ("undergraduate", "本科"),
        ("bachelor", "本科"),
        ("postgraduate", "研究生"),
        ("graduate", "研究生"),
        ("associate", "大专"),
        ("junior college", "大专"),
        ("college", "大专"),
        ("high school", "高中"),
    ]
    for token, level in mappings:
        if token in lowered:
            return level
    return None


def _normalize_resume_education(value: str | None) -> str | None:
    cleaned = _clean_resume_value(value)
    if not cleaned:
        return None
    return _map_resume_education_level(cleaned) or cleaned


def _resume_name_candidate(line: str) -> str | None:
    candidate = line.strip(" -_｜|")
    if not candidate or any(char.isdigit() for char in candidate):
        return None
    lowered = candidate.lower()
    if any(word.lower() in lowered for word in _RESUME_TITLE_WORDS):
        return None
    if re.search(r"[:：@]", candidate):
        return None
    if re.search(r"手机|电话|邮箱|性别|年龄|学历|经验|技能|项目|公司|岗位|职位|gender|age|education|experience|skill", candidate, flags=re.IGNORECASE):
        return None
    if re.search(r"[\u4e00-\u9fff]", candidate):
        compact = re.sub(r"\s+", "", candidate)
        return candidate if 2 <= len(compact) <= 6 else None
    words = candidate.split()
    return candidate if 2 <= len(candidate) <= 40 and 1 <= len(words) <= 4 else None

def _extract_name_from_file_name(original_name: str | None) -> str | None:
    if not original_name:
        return None
    stem = Path(original_name).stem
    for token in reversed(re.split(r"[\s_\-—–丨|]+", stem)):
        candidate = _resume_name_candidate(token)
        if candidate and re.search(r"[\u4e00-\u9fff]", candidate):
            return candidate
    return None


def _extract_position_from_headline(lines: list[str]) -> str | None:
    if not lines:
        return None
    for part in re.split(r"[丨|/，,；;]", lines[0]):
        candidate = part.strip(" ：:-_\t")
        if not candidate or any(token in candidate for token in ["岁", "年经验", "本科", "硕士", "博士", "大专", "专科", "在职"]):
            continue
        if re.search(r"经理|产品|工程师|顾问|运营|设计|开发|分析师|主管|总监|专员|HR", candidate, flags=re.IGNORECASE):
            return candidate
    return None


def _extract_first_match(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else None


class ResumeService:
    """Resume upload and lookup use cases."""

    parser_version = "resume-parser-v1"

    allowed_extensions = {
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".bmp",
    }

    @staticmethod
    def _build_snapshot(current_user: User, original_name: str, file_size: int) -> str:
        size_kb = max(1, round(file_size / 1024))
        return (
            f"简历文件 | {original_name} | {size_kb}KB | "
            "已上传简历文件，当前生成规则快照；后续可接入 AI 精细解析。"
        )

    @staticmethod
    async def get_my_status(db: AsyncSession, current_user: User) -> ResumeStatusResponse:
        resume = await ResumeRepository.get_by_seeker_id(db, current_user.id)
        latest_upload = await ResumeRepository.get_latest_upload(db, current_user.id)
        latest_parse_run = await ResumeRepository.get_latest_parse_run(db, current_user.id)
        return ResumeStatusResponse(
            has_resume=resume is not None,
            resume=_to_response(resume) if resume else None,
            latest_upload=_upload_to_response(latest_upload) if latest_upload else None,
            latest_parse_run=_parse_run_to_response(latest_parse_run) if latest_parse_run else None,
        )

    @staticmethod
    async def get_my_profile_summary(
        db: AsyncSession,
        current_user: User,
    ) -> ResumeProfileSummaryResponse:
        resume = await ResumeRepository.get_by_seeker_id(db, current_user.id)
        if resume is None:
            return ResumeProfileSummaryResponse()

        profile = None
        if resume.current_parse_run_id is not None:
            profile = await ResumeRepository.get_latest_structured_profile_by_parse_run_id(
                db,
                resume.current_parse_run_id,
            )
        if profile is None:
            profile = await ResumeRepository.get_latest_structured_profile(db, current_user.id)
        if profile is not None and profile.seeker_id != current_user.id:
            profile = None

        if profile is None:
            return ResumeProfileSummaryResponse(
                resume=_to_response(resume),
                completeness=ResumeService._build_profile_completeness(None, [], [], []),
                review=ResumeProfileReviewResponse(status_label="未解析"),
                source_links=ResumeProfileSourceLinksResponse(parse_run_id=resume.current_parse_run_id),
            )

        detail = await ResumeService._structured_profile_detail_response(db, profile)
        completeness = ResumeService._build_profile_completeness(
            detail.basic_info,
            detail.educations,
            detail.work_experiences,
            detail.skills,
        )
        return ResumeProfileSummaryResponse(
            resume=_to_response(resume),
            profile=detail.profile,
            basic_info=detail.basic_info,
            summaries=ResumeProfileSummaryListsResponse(
                educations=detail.educations,
                work_experiences=detail.work_experiences,
                projects=detail.projects,
                skills=detail.skills,
                certificates=detail.certificates,
            ),
            completeness=completeness,
            review=ResumeService._build_profile_review(
                detail.profile,
                detail.basic_info,
                detail.educations,
                detail.work_experiences,
                detail.projects,
                detail.skills,
                detail.certificates,
            ),
            source_links=ResumeService._build_profile_source_links(detail.profile.parse_run_id),
        )

    @staticmethod
    async def list_my_uploads(
        db: AsyncSession,
        current_user: User,
        limit: int = 20,
    ) -> list[ResumeUploadHistoryItemResponse]:
        limit = max(1, min(limit, 50))
        uploads = await ResumeRepository.list_uploads(db, current_user.id, limit=limit)
        rows: list[ResumeUploadHistoryItemResponse] = []
        for upload in uploads:
            parse_run = await ResumeRepository.get_latest_parse_run_by_upload_id(db, upload.id)
            rows.append(
                ResumeUploadHistoryItemResponse(
                    upload=_upload_to_response(upload),
                    latest_parse_run=_parse_run_to_response(parse_run) if parse_run else None,
                )
            )
        return rows

    @staticmethod
    async def get_my_parse_run_detail(
        db: AsyncSession,
        current_user: User,
        parse_run_id: int,
    ) -> ResumeParseRunDetailResponse:
        parse_run = await ResumeRepository.get_parse_run_by_id(db, parse_run_id)
        if parse_run is None or parse_run.seeker_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parse run not found")

        upload = await ResumeRepository.get_upload_by_id(db, parse_run.upload_id)
        if upload is None or upload.seeker_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found")

        extracted_text = await ResumeRepository.get_extracted_text_by_parse_run_id(db, parse_run.id)
        chunks = await ResumeRepository.list_chunks_by_parse_run_id(db, parse_run.id)
        return ResumeParseRunDetailResponse(
            upload=_upload_to_response(upload),
            parse_run=_parse_run_to_response(parse_run),
            extracted_text=_extracted_text_to_preview(extracted_text) if extracted_text else None,
            chunks=[_chunk_to_preview(chunk) for chunk in chunks],
        )

    @staticmethod
    async def create_structured_profile(
        db: AsyncSession,
        current_user: User,
        payload: ResumeStructuredProfileCreateRequest,
    ) -> ResumeStructuredProfileResponse:
        parse_run = await ResumeRepository.get_parse_run_by_id(db, payload.parse_run_id)
        if parse_run is None or parse_run.seeker_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parse run not found")

        upload = await ResumeRepository.get_upload_by_id(db, parse_run.upload_id)
        if upload is None or upload.seeker_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found")

        has_tag_ids = "tag_ids" in payload.model_fields_set
        tag_refs = await resolve_active_tag_refs(db, payload.tag_ids) if has_tag_ids else []
        existing = await ResumeRepository.get_structured_profile_by_parse_run_schema(
            db,
            parse_run_id=parse_run.id,
            schema_version=payload.schema_version,
        )
        if existing is None:
            profile = ResumeStructuredProfile(
                seeker_id=current_user.id,
                upload_id=upload.id,
                parse_run_id=parse_run.id,
                schema_version=payload.schema_version,
                prompt_config_id=payload.prompt_config_id,
                prompt_version=payload.prompt_version,
                source=payload.source,
                status=payload.status,
                confidence_score=payload.confidence_score,
                structured_json=payload.structured_json,
                tag_refs=tag_refs,
                validation_errors=payload.validation_errors,
            )
        else:
            profile = existing
            profile.prompt_config_id = payload.prompt_config_id
            profile.prompt_version = payload.prompt_version
            profile.source = payload.source
            profile.status = payload.status
            profile.confidence_score = payload.confidence_score
            profile.structured_json = payload.structured_json
            if has_tag_ids:
                profile.tag_refs = tag_refs
            profile.validation_errors = payload.validation_errors

        saved = await ResumeRepository.save_structured_profile(db, profile)
        await db.commit()
        await db.refresh(saved)
        return _structured_profile_to_response(saved)

    @staticmethod
    async def get_my_latest_structured_profile(
        db: AsyncSession,
        current_user: User,
    ) -> ResumeStructuredProfileDetailResponse:
        profile = await ResumeRepository.get_latest_structured_profile(db, current_user.id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Structured profile not found")
        return await ResumeService._structured_profile_detail_response(db, profile)

    @staticmethod
    async def get_recruiter_application_structured_profile(
        db: AsyncSession,
        current_user: User,
        application_id: int,
    ) -> ResumeStructuredProfileDetailResponse:
        if current_user.role != "recruiter":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only recruiters can view application profile")

        from app.modules.application.repository import ApplicationRepository

        application = await ApplicationRepository.get_by_id(db, application_id)
        if application is None or application.recruiter_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

        profile = await ResumeRepository.get_latest_structured_profile(db, application.seeker_id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Structured profile not found")
        return await ResumeService._structured_profile_detail_response(db, profile)

    @staticmethod
    async def get_my_structured_profile_detail(
        db: AsyncSession,
        current_user: User,
        profile_id: int,
    ) -> ResumeStructuredProfileDetailResponse:
        profile = await ResumeRepository.get_structured_profile_by_id(db, profile_id)
        if profile is None or profile.seeker_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Structured profile not found")
        return await ResumeService._structured_profile_detail_response(db, profile)

    @staticmethod
    async def get_my_structured_profile_by_parse_run(
        db: AsyncSession,
        current_user: User,
        parse_run_id: int,
    ) -> ResumeStructuredProfileDetailResponse:
        parse_run = await ResumeRepository.get_parse_run_by_id(db, parse_run_id)
        if parse_run is None or parse_run.seeker_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parse run not found")

        profile = await ResumeRepository.get_latest_structured_profile_by_parse_run_id(db, parse_run_id)
        if profile is None or profile.seeker_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Structured profile not found")
        return await ResumeService._structured_profile_detail_response(db, profile)

    @staticmethod
    async def confirm_structured_profile_by_parse_run(
        db: AsyncSession,
        current_user: User,
        payload: ResumeStructuredConfirmRequest,
    ) -> ResumeStructuredProjectionResponse:
        parse_run = await ResumeRepository.get_parse_run_by_id(db, payload.parse_run_id)
        if parse_run is None or parse_run.seeker_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parse run not found")

        profile = await ResumeRepository.get_structured_profile_by_parse_run_schema(
            db,
            parse_run_id=payload.parse_run_id,
            schema_version=payload.schema_version,
        )
        if profile is None or profile.seeker_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Structured profile not found")

        if payload.structured_json is not None:
            profile.structured_json = payload.structured_json
        if "tag_ids" in payload.model_fields_set:
            profile.tag_refs = await resolve_active_tag_refs(db, payload.tag_ids)

        return await ResumeService._project_structured_profile_row(
            db,
            profile=profile,
            confirm=True,
            min_confidence=payload.min_confidence,
            sync_seeker_profile=True,
        )

    @staticmethod
    async def project_structured_profile(
        db: AsyncSession,
        current_user: User,
        profile_id: int,
        payload: ResumeStructuredProjectionRequest,
    ) -> ResumeStructuredProjectionResponse:
        profile = await ResumeRepository.get_structured_profile_by_id(db, profile_id)
        if profile is None or profile.seeker_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Structured profile not found")

        return await ResumeService._project_structured_profile_row(
            db,
            profile=profile,
            confirm=payload.confirm,
            min_confidence=payload.min_confidence,
            sync_seeker_profile=payload.confirm,
        )

    @staticmethod
    async def _project_structured_profile_row(
        db: AsyncSession,
        *,
        profile: ResumeStructuredProfile,
        confirm: bool,
        min_confidence: float,
        sync_seeker_profile: bool = False,
    ) -> ResumeStructuredProjectionResponse:
        await ResumeRepository.clear_projection_rows(db, profile.id)
        rows = ResumeService._build_projection_rows(profile, min_confidence)
        await ResumeRepository.add_projection_rows(db, **rows)
        if sync_seeker_profile:
            await ResumeService._upsert_seeker_profile_from_basic(db, profile.seeker, rows.get("basic_info"))

        profile.status = "confirmed" if confirm else "validated"
        if confirm:
            profile.confirmed_at = datetime.now(timezone.utc).replace(tzinfo=None)

        await db.commit()
        await db.refresh(profile)

        detail = await ResumeService._structured_profile_detail_response(db, profile)
        projected_counts = {
            "basic_info": 1 if detail.basic_info else 0,
            "educations": len(detail.educations),
            "work_experiences": len(detail.work_experiences),
            "projects": len(detail.projects),
            "skills": len(detail.skills),
            "certificates": len(detail.certificates),
        }
        return ResumeStructuredProjectionResponse(
            profile=_structured_profile_to_response(profile),
            projected_counts=projected_counts,
            detail=detail,
        )

    @staticmethod
    async def _structured_profile_detail_response(
        db: AsyncSession,
        profile: ResumeStructuredProfile,
    ) -> ResumeStructuredProfileDetailResponse:
        basic_info = await ResumeRepository.get_basic_info_by_profile_id(db, profile.id)
        educations = await ResumeRepository.list_educations_by_profile_id(db, profile.id)
        work_experiences = await ResumeRepository.list_work_experiences_by_profile_id(db, profile.id)
        projects = await ResumeRepository.list_projects_by_profile_id(db, profile.id)
        skills = await ResumeRepository.list_skills_by_profile_id(db, profile.id)
        certificates = await ResumeRepository.list_certificates_by_profile_id(db, profile.id)
        return ResumeStructuredProfileDetailResponse(
            profile=_structured_profile_to_response(profile),
            basic_info=_basic_info_to_response(basic_info) if basic_info else None,
            educations=[_education_to_response(row) for row in educations],
            work_experiences=[_work_to_response(row) for row in work_experiences],
            projects=[_project_to_response(row) for row in projects],
            skills=[_skill_to_response(row) for row in skills],
            certificates=[_certificate_to_response(row) for row in certificates],
        )

    @staticmethod
    def _build_profile_completeness(
        basic_info: ResumeBasicInfoResponse | None,
        educations: list[ResumeEducationResponse],
        work_experiences: list[ResumeWorkExperienceResponse],
        skills: list[ResumeSkillResponse],
    ) -> ResumeProfileCompletenessResponse:
        values = {
            "real_name": basic_info.real_name if basic_info else None,
            "gender": basic_info.gender if basic_info else None,
            "highest_education": basic_info.highest_education if basic_info else None,
            "work_years": basic_info.work_years if basic_info else None,
            "target_position": basic_info.target_position if basic_info else None,
            "phone": basic_info.phone if basic_info else None,
            "email": basic_info.email if basic_info else None,
            "current_city": basic_info.current_city if basic_info else None,
            "skills": skills,
            "educations": educations,
            "work_experiences": work_experiences,
        }
        core_fields = ["real_name", "gender", "highest_education", "work_years", "target_position"]
        recommended_fields = [*core_fields, "phone", "email", "current_city", "skills"]
        core = ResumeService._score_completeness_group(values, core_fields)
        recommended = ResumeService._score_completeness_group(values, recommended_fields)
        return ResumeProfileCompletenessResponse(
            score=recommended.score,
            filled_count=recommended.filled_count,
            total_count=recommended.total_count,
            missing_fields=recommended.missing_fields,
            core=core,
            recommended=recommended,
        )

    @staticmethod
    def _score_completeness_group(
        values: dict[str, Any],
        fields: list[str],
    ) -> ResumeProfileCompletenessGroupResponse:
        missing = [_profile_field_label(field) for field in fields if not _has_value(values.get(field))]
        filled_count = len(fields) - len(missing)
        score = round((filled_count / len(fields)) * 100) if fields else 0
        return ResumeProfileCompletenessGroupResponse(
            score=score,
            filled_count=filled_count,
            total_count=len(fields),
            missing_fields=missing,
        )

    @staticmethod
    def _build_profile_review(
        profile: ResumeStructuredProfileResponse,
        basic_info: ResumeBasicInfoResponse | None,
        educations: list[ResumeEducationResponse],
        work_experiences: list[ResumeWorkExperienceResponse],
        projects: list[ResumeProjectResponse],
        skills: list[ResumeSkillResponse],
        certificates: list[ResumeCertificateResponse],
    ) -> ResumeProfileReviewResponse:
        needs_review = profile.status != "confirmed"
        rows = [
            row
            for row in [basic_info, *educations, *work_experiences, *projects, *skills, *certificates]
            if row is not None
        ]
        low_confidence_count = sum(
            1
            for row in rows
            if row.confidence_score is not None and row.confidence_score < 0.8
        )
        return ResumeProfileReviewResponse(
            needs_review=needs_review,
            unconfirmed_count=1 if needs_review else 0,
            low_confidence_count=low_confidence_count,
            status_label=ResumeService._profile_status_label(profile.status),
        )

    @staticmethod
    def _profile_status_label(status_value: str | None) -> str:
        labels = {
            "draft": "草稿",
            "validated": "待确认",
            "needs_review": "待确认",
            "confirmed": "已确认",
            "rejected": "已废弃",
        }
        return labels.get(status_value or "", "未解析")

    @staticmethod
    def _build_profile_source_links(parse_run_id: int | None) -> ResumeProfileSourceLinksResponse:
        if parse_run_id is None:
            return ResumeProfileSourceLinksResponse()
        return ResumeProfileSourceLinksResponse(
            parse_run_id=parse_run_id,
            parse_run_detail_url=f"/api/v1/resumes/me/parse-runs/{parse_run_id}",
            structured_url=f"/api/v1/resumes/me/parse-runs/{parse_run_id}/structured",
            confirm_page_path=f"/seeker/parse-confirm/{parse_run_id}",
        )

    @staticmethod
    def _build_projection_rows(
        profile: ResumeStructuredProfile,
        min_confidence: float,
    ) -> dict[str, Any]:
        data = profile.structured_json or {}
        basic = data.get("basic") if isinstance(data.get("basic"), dict) else {}
        default_confidence = profile.confidence_score
        source = "parser"
        basic_confidence = _item_confidence(basic, default_confidence)
        basic_info = None
        if basic and ResumeService._should_project_item(basic, min_confidence, default_confidence):
            basic_info = ResumeBasicInfo(
                seeker_id=profile.seeker_id,
                upload_id=profile.upload_id,
                parse_run_id=profile.parse_run_id,
                structured_profile_id=profile.id,
                real_name=_string_or_none(_dict_value(basic, "name", "real_name")),
                gender=_string_or_none(_dict_value(basic, "gender")),
                age=_int_or_none(_dict_value(basic, "age")),
                phone=_string_or_none(_dict_value(basic, "phone", "mobile")),
                email=_string_or_none(_dict_value(basic, "email")),
                highest_education=_string_or_none(_dict_value(basic, "highest_education", "education")),
                work_years=_float_or_none(_dict_value(basic, "work_years", "experience_years")),
                current_city=_string_or_none(_dict_value(basic, "current_city", "city")),
                target_position=_string_or_none(_dict_value(basic, "target_position", "apply_job")),
                expected_salary=_string_or_none(_dict_value(basic, "expected_salary")),
                source=source,
                confidence_score=basic_confidence,
                raw_text=_source_text(basic),
                source_json=basic,
            )

        educations: list[ResumeEducation] = []
        for index, item in enumerate(_list_from_json(data, "education", "educations")):
            if not ResumeService._should_project_item(item, min_confidence, default_confidence):
                continue
            row = item if isinstance(item, dict) else {"school_name": item}
            educations.append(
                ResumeEducation(
                    seeker_id=profile.seeker_id,
                    upload_id=profile.upload_id,
                    parse_run_id=profile.parse_run_id,
                    structured_profile_id=profile.id,
                    school_name=_string_or_none(_dict_value(row, "school_name", "school", "edu_college")),
                    major=_string_or_none(_dict_value(row, "major", "edu_major")),
                    degree=_string_or_none(_dict_value(row, "degree", "edu_degree")),
                    education_level=_string_or_none(_dict_value(row, "education_level", "highest_education")),
                    start_date=_string_or_none(_dict_value(row, "start_date")),
                    end_date=_string_or_none(_dict_value(row, "end_date")),
                    is_full_time=row.get("is_full_time") if isinstance(row.get("is_full_time"), bool) else None,
                    source=source,
                    confidence_score=_item_confidence(row, default_confidence),
                    raw_text=_source_text(row),
                    source_json=row,
                    sort_order=index,
                )
            )

        work_experiences: list[ResumeWorkExperience] = []
        for index, item in enumerate(_list_from_json(data, "work_experiences", "work", "jobs")):
            if not ResumeService._should_project_item(item, min_confidence, default_confidence):
                continue
            row = item if isinstance(item, dict) else {"company_name": item}
            work_experiences.append(
                ResumeWorkExperience(
                    seeker_id=profile.seeker_id,
                    upload_id=profile.upload_id,
                    parse_run_id=profile.parse_run_id,
                    structured_profile_id=profile.id,
                    company_name=_string_or_none(_dict_value(row, "company_name", "company", "job_cpy")),
                    position=_string_or_none(_dict_value(row, "position", "job_position")),
                    start_date=_string_or_none(_dict_value(row, "start_date")),
                    end_date=_string_or_none(_dict_value(row, "end_date")),
                    description=_string_or_none(_dict_value(row, "description", "job_content", "content")),
                    source=source,
                    confidence_score=_item_confidence(row, default_confidence),
                    raw_text=_source_text(row),
                    source_json=row,
                    sort_order=index,
                )
            )

        projects: list[ResumeProject] = []
        for index, item in enumerate(_list_from_json(data, "projects", "project_experiences")):
            if not ResumeService._should_project_item(item, min_confidence, default_confidence):
                continue
            row = item if isinstance(item, dict) else {"project_name": item}
            projects.append(
                ResumeProject(
                    seeker_id=profile.seeker_id,
                    upload_id=profile.upload_id,
                    parse_run_id=profile.parse_run_id,
                    structured_profile_id=profile.id,
                    project_name=_string_or_none(_dict_value(row, "project_name", "name", "proj_name")),
                    role=_string_or_none(_dict_value(row, "role", "proj_role")),
                    start_date=_string_or_none(_dict_value(row, "start_date")),
                    end_date=_string_or_none(_dict_value(row, "end_date")),
                    description=_string_or_none(_dict_value(row, "description", "proj_content", "content")),
                    responsibility=_string_or_none(_dict_value(row, "responsibility", "proj_resp")),
                    source=source,
                    confidence_score=_item_confidence(row, default_confidence),
                    raw_text=_source_text(row),
                    source_json=row,
                    sort_order=index,
                )
            )

        skills: list[ResumeSkill] = []
        for index, item in enumerate(_list_from_json(data, "skills", "professional_skills")):
            if not ResumeService._should_project_item(item, min_confidence, default_confidence):
                continue
            row = item if isinstance(item, dict) else {"skill_name": item}
            skill_name = _string_or_none(_dict_value(row, "skill_name", "name", "skills_name"))
            if not skill_name:
                continue
            skills.append(
                ResumeSkill(
                    seeker_id=profile.seeker_id,
                    upload_id=profile.upload_id,
                    parse_run_id=profile.parse_run_id,
                    structured_profile_id=profile.id,
                    skill_name=skill_name,
                    skill_level=_string_or_none(_dict_value(row, "skill_level", "level", "skills_level")),
                    category=_string_or_none(_dict_value(row, "category")),
                    source=source,
                    confidence_score=_item_confidence(row, default_confidence),
                    raw_text=_source_text(row),
                    source_json=row,
                    sort_order=index,
                )
            )

        certificates: list[ResumeCertificate] = []
        for index, item in enumerate(_list_from_json(data, "certificates", "certs", "awards")):
            if not ResumeService._should_project_item(item, min_confidence, default_confidence):
                continue
            row = item if isinstance(item, dict) else {"certificate_name": item}
            certificate_name = _string_or_none(_dict_value(row, "certificate_name", "cert_name", "name"))
            if not certificate_name:
                continue
            certificates.append(
                ResumeCertificate(
                    seeker_id=profile.seeker_id,
                    upload_id=profile.upload_id,
                    parse_run_id=profile.parse_run_id,
                    structured_profile_id=profile.id,
                    certificate_name=certificate_name,
                    certificate_type=_string_or_none(_dict_value(row, "certificate_type", "cert_type", "type")),
                    issuer=_string_or_none(_dict_value(row, "issuer")),
                    issued_at=_string_or_none(_dict_value(row, "issued_at", "date")),
                    source=source,
                    confidence_score=_item_confidence(row, default_confidence),
                    raw_text=_source_text(row),
                    source_json=row,
                    sort_order=index,
                )
            )

        return {
            "basic_info": basic_info,
            "educations": educations,
            "work_experiences": work_experiences,
            "projects": projects,
            "skills": skills,
            "certificates": certificates,
        }

    @staticmethod
    def _should_project_item(item: Any, min_confidence: float, default_confidence: float | None) -> bool:
        confidence = _item_confidence(item, default_confidence)
        if confidence is None:
            return min_confidence <= 0
        return confidence >= min_confidence

    @staticmethod
    async def upload(db: AsyncSession, current_user: User, file: UploadFile) -> ResumeUploadResultResponse:
        if current_user.role != "seeker":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only seekers can upload resumes")

        original_name = file.filename or "resume"
        extension = Path(original_name).suffix.lower()
        if extension not in ResumeService.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pdf, doc, docx, xls, xlsx, jpg, jpeg, png, webp and bmp resumes are supported",
            )

        content = await file.read()
        if not content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resume file cannot be empty")
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Resume file is too large")

        upload_dir = Path(settings.UPLOAD_DIR) / "resumes"
        upload_dir.mkdir(parents=True, exist_ok=True)
        saved_name = f"{current_user.id}_{uuid4().hex}{extension}"
        saved_path = upload_dir / saved_name
        saved_path.write_bytes(content)

        file_url = f"/uploads/resumes/{saved_name}"
        snapshot = ResumeService._build_snapshot(current_user, original_name, len(content))
        resume = await ResumeRepository.get_by_seeker_id(db, current_user.id)
        if resume is None:
            resume = SeekerResume(
                seeker_id=current_user.id,
                file_url=file_url,
                file_name=original_name,
                content_type=file.content_type,
                file_size=len(content),
                parsed_snapshot=snapshot,
            )

        saved_resume = await ResumeRepository.flush_resume(db, resume)
        upload = await ResumeRepository.add_upload(
            db,
            ResumeUpload(
                seeker_id=current_user.id,
                resume_id=saved_resume.id,
                file_url=file_url,
                storage_path=str(saved_path),
                original_file_name=original_name,
                content_type=file.content_type,
                file_ext=extension,
                file_size=len(content),
                sha256=hashlib.sha256(content).hexdigest(),
                upload_source="seeker_web",
                status="processing",
            ),
        )
        parse_run = await ResumeRepository.add_parse_run(
            db,
            ResumeParseRun(
                upload_id=upload.id,
                seeker_id=current_user.id,
                status="running",
                parser_version=ResumeService.parser_version,
                extractor=extension.lstrip(".") or "unknown",
                started_at=datetime.now(timezone.utc).replace(tzinfo=None),
            ),
        )

        await ResumeService._run_local_parse(
            db=db,
            current_user=current_user,
            upload=upload,
            parse_run=parse_run,
            saved_path=saved_path,
            extension=extension,
        )
        if parse_run.status == "succeeded":
            saved_resume.file_url = file_url
            saved_resume.file_name = original_name
            saved_resume.content_type = file.content_type
            saved_resume.file_size = len(content)
            saved_resume.parsed_snapshot = snapshot
            saved_resume.current_upload_id = upload.id
            saved_resume.current_parse_run_id = parse_run.id

        await db.commit()
        await db.refresh(saved_resume)
        await db.refresh(upload)
        await db.refresh(parse_run)
        return ResumeUploadResultResponse(
            resume=_to_response(saved_resume),
            upload=_upload_to_response(upload),
            parse_run=_parse_run_to_response(parse_run),
        )

    @staticmethod
    async def _run_local_parse(
        db: AsyncSession,
        current_user: User,
        upload: ResumeUpload,
        parse_run: ResumeParseRun,
        saved_path: Path,
        extension: str,
    ) -> None:
        try:
            text, extractor = extract_resume_text(saved_path, extension)
            if not text:
                raise ResumeExtractionError("No text extracted from resume")

            chunks = split_resume_text(text)
            if not chunks:
                raise ResumeExtractionError("No chunks generated from resume text")

            parse_run.extractor = extractor
            parse_run.status = "succeeded"
            parse_run.finished_at = datetime.now(timezone.utc).replace(tzinfo=None)
            parse_run.metrics_json = {
                "char_count": len(text),
                "chunk_count": len(chunks),
                "file_ext": extension,
            }
            upload.status = "parsed"
            upload.error_message = None

            await ResumeRepository.add_extracted_text(
                db,
                ResumeExtractedText(
                    parse_run_id=parse_run.id,
                    upload_id=upload.id,
                    text=text,
                    text_hash=hash_text(text),
                    language="mixed",
                    quality_score=ResumeService._estimate_text_quality(text),
                    page_count=None,
                    char_count=len(text),
                ),
            )
            await ResumeRepository.add_chunks(
                db,
                [
                    ResumeChunk(
                        parse_run_id=parse_run.id,
                        upload_id=upload.id,
                        seeker_id=current_user.id,
                        chunk_index=int(chunk["chunk_index"]),
                        section=str(chunk["section"]),
                        content=str(chunk["content"]),
                        content_hash=str(chunk["content_hash"]),
                        token_count=int(chunk["token_count"]),
                        embedding_status="pending",
                    )
                    for chunk in chunks
                ],
            )
            await ResumeService._create_rule_structured_profile(
                db=db,
                current_user=current_user,
                upload=upload,
                parse_run=parse_run,
                text=text,
            )
        except ResumeExtractionError as exc:
            parse_run.status = "completed_with_errors"
            parse_run.finished_at = datetime.now(timezone.utc).replace(tzinfo=None)
            parse_run.error_code = "text_extraction_unavailable"
            parse_run.error_message = str(exc)
            parse_run.metrics_json = {"file_ext": extension, "chunk_count": 0}
            upload.status = "failed"
            upload.error_message = str(exc)

    @staticmethod
    async def _create_rule_structured_profile(
        db: AsyncSession,
        current_user: User,
        upload: ResumeUpload,
        parse_run: ResumeParseRun,
        text: str,
    ) -> None:
        structured_json, confidence = ResumeService._parse_text_to_structured_json(text, current_user, original_name=upload.original_file_name)
        profile = ResumeStructuredProfile(
            seeker_id=current_user.id,
            upload_id=upload.id,
            parse_run_id=parse_run.id,
            schema_version="resume-structured-v1",
            source="rule",
            status="validated",
            confidence_score=confidence,
            structured_json=structured_json,
            validation_errors=[],
        )
        saved_profile = await ResumeRepository.save_structured_profile(db, profile)
        await db.flush()

        rows = ResumeService._build_projection_rows(saved_profile, min_confidence=0.0)
        await ResumeRepository.add_projection_rows(db, **rows)

    @staticmethod
    def _parse_text_to_structured_json(text: str, current_user: User, original_name: str | None = None) -> tuple[dict[str, Any], float]:
        normalized = re.sub(r"[ \t]+", " ", text.strip())
        lines = [line.strip() for line in re.split(r"[\r\n]+", normalized) if line.strip()]

        phone = _extract_labeled_value(normalized, ["手机", "手机号", "电话", "联系电话", "Mobile", "Phone"])
        if not phone:
            phone = _extract_first_match(normalized, r"(?<!\d)(1[3-9]\d{9})(?!\d)")

        email = _extract_labeled_value(normalized, ["邮箱", "Email", "E-mail"], max_chars=120)
        if not email:
            email = _extract_first_match(normalized, r"([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})")

        gender = _normalize_resume_gender(_extract_labeled_value(normalized, ["性别", "Gender"], max_chars=10))
        if not gender and re.search(r"(^|[，,；;\s|/])男($|[，,；;\s|/])", normalized):
            gender = "男"
        elif not gender and re.search(r"(^|[，,；;\s|/])女($|[，,；;\s|/])", normalized):
            gender = "女"

        age = _int_or_none(_extract_labeled_value(normalized, ["年龄", "Age"], max_chars=10))
        if age is None:
            age_match = re.search(r"(?<!\d)(1[6-9]|[2-5]\d|60)\s*岁", normalized)
            if age_match:
                age = _int_or_none(age_match.group(1))
        if age is None:
            birth_year_match = re.search(r"(?:出生年月|出生日期|生日|Birth)\s*[:：]?\s*((?:19|20)\d{2})", normalized, flags=re.IGNORECASE)
            if birth_year_match:
                birth_year = _int_or_none(birth_year_match.group(1))
                if birth_year:
                    calculated_age = 2026 - birth_year
                    if 16 <= calculated_age <= 70:
                        age = calculated_age

        real_name = _extract_labeled_value(normalized, ["姓名", "真实姓名", "Name", "Full Name"], max_chars=40)
        if not real_name:
            real_name = _extract_name_from_file_name(original_name)
        if not real_name:
            for line in lines[:8]:
                real_name = _resume_name_candidate(line)
                if real_name:
                    break
        if not real_name:
            real_name = current_user.display_name

        highest_education = _normalize_resume_education(
            _extract_labeled_value(
                normalized,
                ["最高学历", "学历", "教育程度", "Education", "Highest Education", "Degree"],
                max_chars=40,
            )
        )
        if not highest_education:
            highest_education = _map_resume_education_level(normalized)

        work_years = None
        work_years_text = _extract_labeled_value(
            normalized,
            ["工作年限", "工作经验", "从业经验", "经验", "Experience", "Work Experience", "Work Years", "Years of Experience"],
            max_chars=40,
        )
        years_source = work_years_text or normalized
        years_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:年|years?)", years_source, flags=re.IGNORECASE)
        if years_match:
            work_years = _float_or_none(years_match.group(1))

        current_city = _extract_labeled_value(normalized, ["所在城市", "当前城市", "城市", "地点", "City"], max_chars=40)
        target_position = _extract_labeled_value(
            normalized,
            ["职业方向", "求职意向", "目标岗位", "求职岗位", "应聘岗位", "期望职位", "职位", "岗位", "Target Position", "Career Direction", "Desired Position", "Position"],
            max_chars=120,
        )
        if not target_position:
            target_position = _extract_position_from_headline(lines)
        expected_salary = _extract_labeled_value(normalized, ["期望薪资", "薪资", "Salary"], max_chars=40)

        skills = ResumeService._extract_skill_items(normalized)
        educations = ResumeService._extract_education_items(normalized, highest_education)
        work_experiences = ResumeService._extract_work_items(normalized, target_position)
        projects = ResumeService._extract_project_items(normalized)
        certificates = ResumeService._extract_certificate_items(normalized)

        basic = {
            "name": real_name,
            "gender": gender,
            "age": age,
            "phone": phone,
            "email": email,
            "highest_education": highest_education,
            "work_years": work_years,
            "current_city": current_city,
            "target_position": target_position,
            "expected_salary": expected_salary,
            "confidence_score": ResumeService._field_confidence(
                [real_name, gender, age, phone, email, highest_education, work_years, current_city, target_position]
            ),
            "raw_text": "\n".join(lines[:8]),
        }
        structured = {
            "basic": basic,
            "education": educations,
            "work_experiences": work_experiences,
            "projects": projects,
            "skills": skills,
            "certificates": certificates,
        }
        confidence = ResumeService._field_confidence(
            [basic.get("name"), basic.get("gender"), basic.get("age"), basic.get("phone"), basic.get("highest_education"), skills]
        )
        return structured, confidence

    @staticmethod
    def _extract_skill_items(text: str) -> list[dict[str, Any]]:
        known_skills = [
            "PeopleSoft",
            "HCM",
            "ERP",
            "Python",
            "Java",
            "JavaScript",
            "TypeScript",
            "React",
            "Vue",
            "Node.js",
            "SQL",
            "MySQL",
            "PostgreSQL",
            "Oracle",
            "Excel",
            "PMP",
        ]
        found = []
        for skill in known_skills:
            if re.search(rf"(?<![A-Za-z0-9]){re.escape(skill)}(?![A-Za-z0-9])", text, flags=re.IGNORECASE):
                found.append(skill)

        skill_line = _extract_labeled_value(text, ["技能", "专业技能", "技术栈", "Skills"], max_chars=200)
        if skill_line:
            for item in re.split(r"[，,；;、/|]", skill_line):
                skill = item.strip()
                if 1 < len(skill) <= 40 and skill not in found:
                    found.append(skill)

        return [
            {"skill_name": skill, "skill_level": None, "category": "技能", "confidence_score": 0.78}
            for skill in found[:20]
        ]

    @staticmethod
    def _extract_education_items(text: str, highest_education: str | None) -> list[dict[str, Any]]:
        school = _extract_labeled_value(text, ["毕业院校", "学校", "院校", "School"], max_chars=80)
        major = _extract_labeled_value(text, ["专业", "Major"], max_chars=80)
        if not school:
            school = _extract_first_match(text, r"([\u4e00-\u9fa5A-Za-z0-9]{2,40}(?:大学|学院|学校|University|College))")
        if not school and not major and not highest_education:
            return []
        return [
            {
                "school_name": school,
                "major": major,
                "degree": highest_education,
                "education_level": highest_education,
                "confidence_score": ResumeService._field_confidence([school, major, highest_education]),
            }
        ]

    @staticmethod
    def _extract_work_items(text: str, target_position: str | None) -> list[dict[str, Any]]:
        company = _extract_labeled_value(text, ["公司", "当前公司", "最近公司", "Company"], max_chars=80)
        position = _extract_labeled_value(text, ["职位", "岗位", "Position"], max_chars=80) or target_position
        if not company:
            company = _extract_first_match(text, r"([\u4e00-\u9fa5A-Za-z0-9]{2,40}(?:公司|集团|科技|信息|咨询|有限责任公司))")
        if not company and not position:
            return []
        return [
            {
                "company_name": company,
                "position": position,
                "description": _extract_labeled_value(text, ["工作内容", "职责", "工作职责"], max_chars=200),
                "confidence_score": ResumeService._field_confidence([company, position]),
            }
        ]

    @staticmethod
    def _extract_project_items(text: str) -> list[dict[str, Any]]:
        project = _extract_labeled_value(text, ["项目", "项目名称", "Project"], max_chars=100)
        if not project:
            project = _extract_first_match(text, r"([\u4e00-\u9fa5A-Za-z0-9 ]{2,60}(?:项目|系统|平台))")
        if not project:
            return []
        return [
            {
                "project_name": project,
                "role": _extract_labeled_value(text, ["项目角色", "角色"], max_chars=60),
                "responsibility": _extract_labeled_value(text, ["项目职责", "项目内容"], max_chars=200),
                "confidence_score": 0.72,
            }
        ]

    @staticmethod
    def _extract_certificate_items(text: str) -> list[dict[str, Any]]:
        certificates = []
        for cert in ["PMP", "CPA", "CFA", "软考", "教师资格证", "英语六级", "英语四级", "CET-6", "CET-4"]:
            if cert in text:
                certificates.append(
                    {"certificate_name": cert, "certificate_type": "证书", "confidence_score": 0.76}
                )
        return certificates[:10]

    @staticmethod
    def _field_confidence(values: list[Any]) -> float:
        if not values:
            return 0.0
        filled = sum(1 for value in values if value not in (None, "", []))
        return round(min(0.95, 0.55 + filled / len(values) * 0.35), 2)

    @staticmethod
    async def _upsert_seeker_profile_from_basic(
        db: AsyncSession,
        current_user: User,
        basic_info: ResumeBasicInfo | None,
    ) -> None:
        if basic_info is None:
            return
        from app.modules.seeker_profile.repository import SeekerProfileRepository

        profile = await SeekerProfileRepository.get_by_seeker_id(db, current_user.id)
        if profile is None:
            profile = SeekerProfile(seeker_id=current_user.id)

        updates = {
            "real_name": basic_info.real_name,
            "gender": basic_info.gender,
            "education": basic_info.highest_education,
            "experience_years": int(basic_info.work_years) if basic_info.work_years is not None else None,
            "target_position": basic_info.target_position,
            "expected_salary": basic_info.expected_salary,
            "city": basic_info.current_city,
        }
        for field, value in updates.items():
            if value not in (None, ""):
                setattr(profile, field, value)
        db.add(profile)
        await db.flush()

    @staticmethod
    def _estimate_text_quality(text: str) -> float:
        stripped = text.strip()
        if not stripped:
            return 0.0
        score = 0.3
        if len(stripped) >= 300:
            score += 0.3
        if any(keyword in stripped for keyword in ["经验", "项目", "教育", "技能", "工作"]):
            score += 0.2
        if "@" in stripped or any(char.isdigit() for char in stripped):
            score += 0.1
        return min(1.0, round(score, 2))
