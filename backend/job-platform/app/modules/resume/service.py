"""
Seeker resume business logic.
"""
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.resume.chunking import hash_text, split_resume_text
from app.modules.resume.extractors import ResumeExtractionError, extract_resume_text
from app.modules.resume.models import ResumeChunk, ResumeExtractedText, ResumeParseRun, ResumeUpload, SeekerResume
from app.modules.resume.repository import ResumeRepository
from app.modules.resume.schemas import (
    ResumeChunkPreviewResponse,
    ResumeExtractedTextPreviewResponse,
    ResumeParseRunResponse,
    ResumeParseRunDetailResponse,
    ResumeResponse,
    ResumeStatusResponse,
    ResumeUploadHistoryItemResponse,
    ResumeUploadResponse,
    ResumeUploadResultResponse,
)
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

        upload_dir = Path("uploads") / "resumes"
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
        else:
            resume.file_url = file_url
            resume.file_name = original_name
            resume.content_type = file.content_type
            resume.file_size = len(content)
            resume.parsed_snapshot = snapshot

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
        saved_resume.current_upload_id = upload.id
        saved_resume.current_parse_run_id = parse_run.id

        await ResumeService._run_local_parse(
            db=db,
            current_user=current_user,
            upload=upload,
            parse_run=parse_run,
            saved_path=saved_path,
            extension=extension,
        )

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
        except ResumeExtractionError as exc:
            parse_run.status = "completed_with_errors"
            parse_run.finished_at = datetime.now(timezone.utc).replace(tzinfo=None)
            parse_run.error_code = "text_extraction_unavailable"
            parse_run.error_message = str(exc)
            parse_run.metrics_json = {"file_ext": extension, "chunk_count": 0}
            upload.status = "failed"
            upload.error_message = str(exc)

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
