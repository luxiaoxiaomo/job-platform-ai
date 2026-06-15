"""
Seeker resume repository.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.resume.models import ResumeChunk, ResumeExtractedText, ResumeParseRun, ResumeUpload, SeekerResume


class ResumeRepository:
    """Database operations for seeker resumes."""

    @staticmethod
    async def get_by_seeker_id(db: AsyncSession, seeker_id: int) -> Optional[SeekerResume]:
        result = await db.execute(select(SeekerResume).where(SeekerResume.seeker_id == seeker_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def save(db: AsyncSession, resume: SeekerResume) -> SeekerResume:
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        return resume

    @staticmethod
    async def flush_resume(db: AsyncSession, resume: SeekerResume) -> SeekerResume:
        db.add(resume)
        await db.flush()
        await db.refresh(resume)
        return resume

    @staticmethod
    async def get_latest_upload(db: AsyncSession, seeker_id: int) -> Optional[ResumeUpload]:
        result = await db.execute(
            select(ResumeUpload)
            .where(ResumeUpload.seeker_id == seeker_id)
            .order_by(ResumeUpload.created_at.desc(), ResumeUpload.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_latest_parse_run(db: AsyncSession, seeker_id: int) -> Optional[ResumeParseRun]:
        result = await db.execute(
            select(ResumeParseRun)
            .where(ResumeParseRun.seeker_id == seeker_id)
            .order_by(ResumeParseRun.created_at.desc(), ResumeParseRun.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_uploads(db: AsyncSession, seeker_id: int, limit: int = 20) -> list[ResumeUpload]:
        result = await db.execute(
            select(ResumeUpload)
            .where(ResumeUpload.seeker_id == seeker_id)
            .order_by(ResumeUpload.created_at.desc(), ResumeUpload.id.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_upload_by_id(db: AsyncSession, upload_id: int) -> Optional[ResumeUpload]:
        result = await db.execute(select(ResumeUpload).where(ResumeUpload.id == upload_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_parse_run_by_id(db: AsyncSession, parse_run_id: int) -> Optional[ResumeParseRun]:
        result = await db.execute(select(ResumeParseRun).where(ResumeParseRun.id == parse_run_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_latest_parse_run_by_upload_id(db: AsyncSession, upload_id: int) -> Optional[ResumeParseRun]:
        result = await db.execute(
            select(ResumeParseRun)
            .where(ResumeParseRun.upload_id == upload_id)
            .order_by(ResumeParseRun.created_at.desc(), ResumeParseRun.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_extracted_text_by_parse_run_id(
        db: AsyncSession,
        parse_run_id: int,
    ) -> Optional[ResumeExtractedText]:
        result = await db.execute(
            select(ResumeExtractedText).where(ResumeExtractedText.parse_run_id == parse_run_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_chunks_by_parse_run_id(db: AsyncSession, parse_run_id: int) -> list[ResumeChunk]:
        result = await db.execute(
            select(ResumeChunk)
            .where(ResumeChunk.parse_run_id == parse_run_id)
            .order_by(ResumeChunk.chunk_index.asc(), ResumeChunk.id.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def add_upload(db: AsyncSession, upload: ResumeUpload) -> ResumeUpload:
        db.add(upload)
        await db.flush()
        await db.refresh(upload)
        return upload

    @staticmethod
    async def add_parse_run(db: AsyncSession, parse_run: ResumeParseRun) -> ResumeParseRun:
        db.add(parse_run)
        await db.flush()
        await db.refresh(parse_run)
        return parse_run

    @staticmethod
    async def add_extracted_text(db: AsyncSession, extracted_text: ResumeExtractedText) -> ResumeExtractedText:
        db.add(extracted_text)
        await db.flush()
        await db.refresh(extracted_text)
        return extracted_text

    @staticmethod
    async def add_chunks(db: AsyncSession, chunks: list[ResumeChunk]) -> list[ResumeChunk]:
        db.add_all(chunks)
        await db.flush()
        for chunk in chunks:
            await db.refresh(chunk)
        return chunks
