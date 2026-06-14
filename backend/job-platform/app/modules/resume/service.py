"""
Seeker resume business logic.
"""
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.resume.models import SeekerResume
from app.modules.resume.repository import ResumeRepository
from app.modules.resume.schemas import ResumeResponse, ResumeStatusResponse
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
        created_at=resume.created_at,
        updated_at=resume.updated_at,
    )


class ResumeService:
    """Resume upload and lookup use cases."""

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
            f"{current_user.display_name}｜{original_name}｜{size_kb}KB｜"
            "已上传简历，规则解析快照；待接入 AI 精细解析。"
        )

    @staticmethod
    async def get_my_status(db: AsyncSession, current_user: User) -> ResumeStatusResponse:
        resume = await ResumeRepository.get_by_seeker_id(db, current_user.id)
        return ResumeStatusResponse(has_resume=resume is not None, resume=_to_response(resume) if resume else None)

    @staticmethod
    async def upload(db: AsyncSession, current_user: User, file: UploadFile) -> ResumeResponse:
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

        saved = await ResumeRepository.save(db, resume)
        return _to_response(saved)
