"""
Enterprise certification business logic.
"""
from datetime import datetime, timezone
from pathlib import Path
import re
from uuid import uuid4
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.company_certification.models import CompanyCertification
from app.modules.company_certification.ocr import run_business_license_ocr
from app.modules.company_certification.repository import CompanyCertificationRepository
from app.modules.company_certification.schemas import (
    BusinessLicenseOcrResponse,
    CertificationProofFileResponse,
    CompanyCertificationListResponse,
    CompanyCertificationResponse,
    CompanyCertificationReview,
    CompanyCertificationSubmit,
)
from app.modules.user.models import User


def _to_response(
    certification: Optional[CompanyCertification],
    recruiter: Optional[User] = None,
) -> CompanyCertificationResponse:
    """Convert ORM object to API response, including not_submitted state."""
    if certification is None:
        if recruiter is None:
            raise ValueError("recruiter is required when certification is None")
        return CompanyCertificationResponse(
            recruiter_id=recruiter.id,
            recruiter_display_name=recruiter.display_name,
            status="not_submitted",
        )

    related_recruiter = certification.recruiter or recruiter
    return CompanyCertificationResponse(
        id=certification.id,
        recruiter_id=certification.recruiter_id,
        recruiter_display_name=related_recruiter.display_name if related_recruiter else None,
        verification_method=certification.verification_method,
        company_name=certification.company_name,
        unified_social_credit_code=certification.unified_social_credit_code,
        legal_representative=certification.legal_representative,
        registered_address=certification.registered_address,
        license_file_url=certification.license_file_url,
        license_file_name=certification.license_file_name,
        proof_file_url=certification.proof_file_url,
        proof_file_name=certification.proof_file_name,
        work_email=certification.work_email,
        applicant_name=certification.applicant_name,
        applicant_title=certification.applicant_title,
        applicant_phone=certification.applicant_phone,
        verification_note=certification.verification_note,
        status=certification.status,
        reject_reason=certification.reject_reason,
        reviewer_id=certification.reviewer_id,
        reviewed_at=certification.reviewed_at,
        created_at=certification.created_at,
        updated_at=certification.updated_at,
    )


class CompanyCertificationService:
    """Enterprise certification use cases."""

    allowed_license_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".heic", ".heif", ".pdf"}
    allowed_proof_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".heic", ".heif", ".pdf"}

    @staticmethod
    def _mock_ocr_from_filename(filename: str) -> dict:
        normalized = Path(filename).stem.strip()
        credit_match = re.search(r"[0-9A-Z]{18}", normalized.upper())
        company_name = None

        if "杭州毅创越新" in normalized:
            company_name = "杭州毅创越新信息咨询有限公司"
        elif "星辰互联" in normalized:
            company_name = "杭州星辰互联科技有限公司"
        elif normalized:
            cleaned = re.sub(r"[_\-\s]+", "", normalized)
            cleaned = re.sub(r"(营业执照|执照|license|business)", "", cleaned, flags=re.IGNORECASE)
            if credit_match:
                cleaned = cleaned.replace(credit_match.group(0), "")
            if len(cleaned) >= 2:
                company_name = cleaned

        return {
            "company_name": company_name or "杭州毅创越新信息咨询有限公司",
            "unified_social_credit_code": credit_match.group(0) if credit_match else "91330100MA2TEST607",
            "legal_representative": "张三",
            "registered_address": "浙江省杭州市西湖区文三路 607 号",
            "confidence": 0.86 if credit_match else 0.72,
            "raw_text": "开发环境OCR模拟结果：已识别企业名称、统一社会信用代码、法定代表人和注册地址。",
        }

    @staticmethod
    async def upload_license_and_ocr(
        current_user: User,
        file: UploadFile,
    ) -> BusinessLicenseOcrResponse:
        if current_user.role != "recruiter":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有招聘者可以上传营业执照",
            )

        original_name = file.filename or "business-license"
        extension = Path(original_name).suffix.lower()
        if extension not in CompanyCertificationService.allowed_license_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="仅支持 jpg、jpeg、png、webp、bmp、heic、heif、pdf 格式的营业执照",
            )

        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="上传文件不能为空",
            )
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="上传文件超过大小限制",
            )

        upload_dir = Path("uploads") / "business_licenses"
        upload_dir.mkdir(parents=True, exist_ok=True)
        saved_name = f"{current_user.id}_{uuid4().hex}{extension}"
        saved_path = upload_dir / saved_name
        saved_path.write_bytes(content)

        parsed = await run_business_license_ocr(
            saved_path,
            original_name,
            CompanyCertificationService._mock_ocr_from_filename,
        )
        return BusinessLicenseOcrResponse(
            license_file_url=f"/uploads/business_licenses/{saved_name}",
            license_file_name=original_name,
            company_name=parsed.company_name,
            unified_social_credit_code=parsed.unified_social_credit_code,
            legal_representative=parsed.legal_representative,
            registered_address=parsed.registered_address,
            confidence=parsed.confidence,
            source=parsed.source,
            raw_text=parsed.raw_text,
        )

    @staticmethod
    async def upload_proof_file(
        current_user: User,
        file: UploadFile,
    ) -> CertificationProofFileResponse:
        if current_user.role != "recruiter":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有招聘者可以上传企业认证证明材料",
            )

        original_name = file.filename or "certification-proof"
        extension = Path(original_name).suffix.lower()
        if extension not in CompanyCertificationService.allowed_proof_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="仅支持 jpg、jpeg、png、webp、bmp、heic、heif、pdf 格式的证明材料",
            )

        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="上传文件不能为空",
            )
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="上传文件超过大小限制",
            )

        upload_dir = Path("uploads") / "company_certification_proofs"
        upload_dir.mkdir(parents=True, exist_ok=True)
        saved_name = f"{current_user.id}_{uuid4().hex}{extension}"
        saved_path = upload_dir / saved_name
        saved_path.write_bytes(content)

        return CertificationProofFileResponse(
            proof_file_url=f"/uploads/company_certification_proofs/{saved_name}",
            proof_file_name=original_name,
        )

    @staticmethod
    async def get_my_status(db: AsyncSession, current_user: User) -> CompanyCertificationResponse:
        certification = await CompanyCertificationRepository.get_by_recruiter_id(db, current_user.id)
        return _to_response(certification, current_user)

    @staticmethod
    async def submit(
        db: AsyncSession,
        current_user: User,
        data: CompanyCertificationSubmit,
    ) -> CompanyCertificationResponse:
        if current_user.role != "recruiter":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有招聘者可以提交企业认证",
            )

        certification = await CompanyCertificationRepository.get_by_recruiter_id(db, current_user.id)

        if certification is None:
            certification = CompanyCertification(
                recruiter_id=current_user.id,
                verification_method=data.verification_method,
                company_name=data.company_name,
                unified_social_credit_code=data.unified_social_credit_code,
                legal_representative=data.legal_representative,
                registered_address=data.registered_address,
                license_file_url=data.license_file_url,
                license_file_name=data.license_file_name,
                proof_file_url=data.proof_file_url,
                proof_file_name=data.proof_file_name,
                work_email=data.work_email,
                applicant_name=data.applicant_name,
                applicant_title=data.applicant_title,
                applicant_phone=data.applicant_phone,
                verification_note=data.verification_note,
                status="pending",
            )
            certification = await CompanyCertificationRepository.create(db, certification)
        else:
            certification.verification_method = data.verification_method
            certification.company_name = data.company_name
            certification.unified_social_credit_code = data.unified_social_credit_code
            certification.legal_representative = data.legal_representative
            certification.registered_address = data.registered_address
            certification.license_file_url = data.license_file_url
            certification.license_file_name = data.license_file_name
            certification.proof_file_url = data.proof_file_url
            certification.proof_file_name = data.proof_file_name
            certification.work_email = data.work_email
            certification.applicant_name = data.applicant_name
            certification.applicant_title = data.applicant_title
            certification.applicant_phone = data.applicant_phone
            certification.verification_note = data.verification_note
            certification.status = "pending"
            certification.reject_reason = None
            certification.reviewer_id = None
            certification.reviewed_at = None
            certification = await CompanyCertificationRepository.update(db, certification)

        return _to_response(certification, current_user)

    @staticmethod
    async def list_for_admin(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        status_filter: Optional[str] = None,
    ) -> CompanyCertificationListResponse:
        if status_filter and status_filter not in {"pending", "approved", "rejected"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="认证状态筛选值不正确",
            )

        items, total = await CompanyCertificationRepository.list(
            db,
            skip=skip,
            limit=limit,
            status=status_filter,
        )

        return CompanyCertificationListResponse(
            items=[_to_response(item) for item in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    async def get_for_admin(db: AsyncSession, certification_id: int) -> CompanyCertificationResponse:
        certification = await CompanyCertificationRepository.get_by_id(db, certification_id)
        if certification is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="企业认证申请不存在",
            )
        return _to_response(certification)

    @staticmethod
    async def review(
        db: AsyncSession,
        certification_id: int,
        reviewer: User,
        data: CompanyCertificationReview,
    ) -> CompanyCertificationResponse:
        certification = await CompanyCertificationRepository.get_by_id(db, certification_id)
        if certification is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="企业认证申请不存在",
            )

        if data.action == "reject" and not data.reject_reason:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="驳回认证时必须填写原因",
            )

        certification.status = "approved" if data.action == "approve" else "rejected"
        certification.reject_reason = None if data.action == "approve" else data.reject_reason
        certification.reviewer_id = reviewer.id
        certification.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)

        certification = await CompanyCertificationRepository.update(db, certification)
        return _to_response(certification)
