"""
Seeker resume repository.
"""
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

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

    @staticmethod
    async def get_structured_profile_by_id(
        db: AsyncSession,
        profile_id: int,
    ) -> Optional[ResumeStructuredProfile]:
        result = await db.execute(select(ResumeStructuredProfile).where(ResumeStructuredProfile.id == profile_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_structured_profile_by_parse_run_schema(
        db: AsyncSession,
        parse_run_id: int,
        schema_version: str,
    ) -> Optional[ResumeStructuredProfile]:
        result = await db.execute(
            select(ResumeStructuredProfile).where(
                ResumeStructuredProfile.parse_run_id == parse_run_id,
                ResumeStructuredProfile.schema_version == schema_version,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_latest_structured_profile_by_parse_run_id(
        db: AsyncSession,
        parse_run_id: int,
    ) -> Optional[ResumeStructuredProfile]:
        result = await db.execute(
            select(ResumeStructuredProfile)
            .where(ResumeStructuredProfile.parse_run_id == parse_run_id)
            .order_by(ResumeStructuredProfile.created_at.desc(), ResumeStructuredProfile.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_latest_structured_profile(
        db: AsyncSession,
        seeker_id: int,
    ) -> Optional[ResumeStructuredProfile]:
        result = await db.execute(
            select(ResumeStructuredProfile)
            .where(ResumeStructuredProfile.seeker_id == seeker_id)
            .order_by(ResumeStructuredProfile.created_at.desc(), ResumeStructuredProfile.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def save_structured_profile(
        db: AsyncSession,
        profile: ResumeStructuredProfile,
    ) -> ResumeStructuredProfile:
        db.add(profile)
        await db.flush()
        await db.refresh(profile)
        return profile

    @staticmethod
    async def clear_projection_rows(db: AsyncSession, structured_profile_id: int) -> None:
        for model in (
            ResumeBasicInfo,
            ResumeEducation,
            ResumeWorkExperience,
            ResumeProject,
            ResumeSkill,
            ResumeCertificate,
        ):
            await db.execute(delete(model).where(model.structured_profile_id == structured_profile_id))

    @staticmethod
    async def add_projection_rows(
        db: AsyncSession,
        *,
        basic_info: Optional[ResumeBasicInfo],
        educations: list[ResumeEducation],
        work_experiences: list[ResumeWorkExperience],
        projects: list[ResumeProject],
        skills: list[ResumeSkill],
        certificates: list[ResumeCertificate],
    ) -> None:
        rows = []
        if basic_info is not None:
            rows.append(basic_info)
        rows.extend(educations)
        rows.extend(work_experiences)
        rows.extend(projects)
        rows.extend(skills)
        rows.extend(certificates)
        if rows:
            db.add_all(rows)
            await db.flush()

    @staticmethod
    async def get_basic_info_by_profile_id(
        db: AsyncSession,
        structured_profile_id: int,
    ) -> Optional[ResumeBasicInfo]:
        result = await db.execute(
            select(ResumeBasicInfo).where(ResumeBasicInfo.structured_profile_id == structured_profile_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_educations_by_profile_id(db: AsyncSession, structured_profile_id: int) -> list[ResumeEducation]:
        result = await db.execute(
            select(ResumeEducation)
            .where(ResumeEducation.structured_profile_id == structured_profile_id)
            .order_by(ResumeEducation.sort_order.asc(), ResumeEducation.id.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_work_experiences_by_profile_id(
        db: AsyncSession,
        structured_profile_id: int,
    ) -> list[ResumeWorkExperience]:
        result = await db.execute(
            select(ResumeWorkExperience)
            .where(ResumeWorkExperience.structured_profile_id == structured_profile_id)
            .order_by(ResumeWorkExperience.sort_order.asc(), ResumeWorkExperience.id.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_projects_by_profile_id(db: AsyncSession, structured_profile_id: int) -> list[ResumeProject]:
        result = await db.execute(
            select(ResumeProject)
            .where(ResumeProject.structured_profile_id == structured_profile_id)
            .order_by(ResumeProject.sort_order.asc(), ResumeProject.id.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_skills_by_profile_id(db: AsyncSession, structured_profile_id: int) -> list[ResumeSkill]:
        result = await db.execute(
            select(ResumeSkill)
            .where(ResumeSkill.structured_profile_id == structured_profile_id)
            .order_by(ResumeSkill.sort_order.asc(), ResumeSkill.id.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_certificates_by_profile_id(
        db: AsyncSession,
        structured_profile_id: int,
    ) -> list[ResumeCertificate]:
        result = await db.execute(
            select(ResumeCertificate)
            .where(ResumeCertificate.structured_profile_id == structured_profile_id)
            .order_by(ResumeCertificate.sort_order.asc(), ResumeCertificate.id.asc())
        )
        return list(result.scalars().all())
