"""
Enterprise certification API.
"""
from typing import Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_role
from app.db.session import get_db
from app.modules.company_certification.schemas import (
    BusinessLicenseOcrResponse,
    CertificationProofFileResponse,
    CompanyCertificationListResponse,
    CompanyCertificationResponse,
    CompanyCertificationReview,
    CompanyCertificationSubmit,
)
from app.modules.company_certification.service import CompanyCertificationService
from app.modules.user.models import User

router = APIRouter()


@router.get("/me", response_model=CompanyCertificationResponse)
async def get_my_company_certification(
    current_user: User = Depends(require_role("recruiter")),
    db: AsyncSession = Depends(get_db),
):
    """Get current recruiter's enterprise certification status."""
    return await CompanyCertificationService.get_my_status(db, current_user)


@router.post("/me", response_model=CompanyCertificationResponse, status_code=http_status.HTTP_201_CREATED)
async def submit_my_company_certification(
    data: CompanyCertificationSubmit,
    current_user: User = Depends(require_role("recruiter")),
    db: AsyncSession = Depends(get_db),
):
    """Submit or resubmit current recruiter's enterprise certification."""
    return await CompanyCertificationService.submit(db, current_user, data)


@router.post("/license/ocr", response_model=BusinessLicenseOcrResponse)
async def upload_business_license_for_ocr(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("recruiter")),
):
    """Upload business license and return parsed OCR fields."""
    return await CompanyCertificationService.upload_license_and_ocr(current_user, file)


@router.post("/proof-file", response_model=CertificationProofFileResponse)
async def upload_company_certification_proof_file(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("recruiter")),
):
    """Upload non-license proof for enterprise certification review."""
    return await CompanyCertificationService.upload_proof_file(current_user, file)


@router.get("/admin", response_model=CompanyCertificationListResponse)
async def list_company_certifications_for_admin(
    status: Optional[str] = Query(None, description="pending/approved/rejected"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """List enterprise certification applications for admin review."""
    return await CompanyCertificationService.list_for_admin(
        db,
        skip=skip,
        limit=limit,
        status_filter=status,
    )


@router.get("/admin/{certification_id}", response_model=CompanyCertificationResponse)
async def get_company_certification_for_admin(
    certification_id: int,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Get one enterprise certification application for admin review."""
    return await CompanyCertificationService.get_for_admin(db, certification_id)


@router.post("/admin/{certification_id}/review", response_model=CompanyCertificationResponse)
async def review_company_certification(
    certification_id: int,
    data: CompanyCertificationReview,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject an enterprise certification application."""
    return await CompanyCertificationService.review(db, certification_id, current_user, data)
