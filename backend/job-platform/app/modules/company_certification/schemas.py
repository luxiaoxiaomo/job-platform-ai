"""
Enterprise certification schemas.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator
import re


CertificationStatus = Literal["not_submitted", "pending", "approved", "rejected"]
ReviewAction = Literal["approve", "reject"]
VerificationMethod = Literal["business_license", "enterprise_email", "hr_authorization"]

PUBLIC_EMAIL_DOMAINS = {
    "gmail.com",
    "outlook.com",
    "hotmail.com",
    "qq.com",
    "163.com",
    "126.com",
    "sina.com",
    "foxmail.com",
}


class CompanyCertificationSubmit(BaseModel):
    """Recruiter enterprise certification submission."""

    verification_method: VerificationMethod = Field("business_license", description="认证方式")
    company_name: str = Field(..., min_length=2, max_length=100, description="企业名称")
    unified_social_credit_code: Optional[str] = Field(None, min_length=18, max_length=18, description="统一社会信用代码")
    legal_representative: Optional[str] = Field(None, min_length=2, max_length=50, description="法定代表人")
    registered_address: Optional[str] = Field(None, min_length=5, max_length=300, description="注册地址")
    license_file_url: Optional[str] = Field(None, max_length=500, description="营业执照文件URL")
    license_file_name: Optional[str] = Field(None, max_length=200, description="营业执照文件名")
    proof_file_url: Optional[str] = Field(None, max_length=500, description="辅助证明材料URL")
    proof_file_name: Optional[str] = Field(None, max_length=200, description="辅助证明材料文件名")
    work_email: Optional[str] = Field(None, max_length=120, description="企业邮箱")
    applicant_name: Optional[str] = Field(None, max_length=50, description="申请人姓名")
    applicant_title: Optional[str] = Field(None, max_length=80, description="申请人职位")
    applicant_phone: Optional[str] = Field(None, max_length=30, description="申请人联系电话")
    applicant_wechat: Optional[str] = Field(None, max_length=80, description="申请人微信")
    verification_note: Optional[str] = Field(None, max_length=500, description="认证补充说明")

    @field_validator("unified_social_credit_code")
    @classmethod
    def validate_credit_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate Chinese unified social credit code shape."""
        if v is None or not v.strip():
            return None
        normalized = v.strip().upper()
        if not re.match(r"^[0-9A-Z]{18}$", normalized):
            raise ValueError("统一社会信用代码必须是18位数字或大写字母")
        return normalized

    @field_validator(
        "company_name",
        "legal_representative",
        "registered_address",
        "work_email",
        "applicant_name",
        "applicant_title",
        "applicant_phone",
        "applicant_wechat",
        "verification_note",
    )
    @classmethod
    def strip_text(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v

    @field_validator("work_email")
    @classmethod
    def validate_work_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        normalized = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", normalized):
            raise ValueError("企业邮箱格式不正确")
        domain = normalized.rsplit("@", 1)[1]
        if domain in PUBLIC_EMAIL_DOMAINS:
            raise ValueError("请使用企业邮箱，不支持公共邮箱")
        return normalized

    @field_validator("verification_method")
    @classmethod
    def validate_method(cls, v: VerificationMethod) -> VerificationMethod:
        return v

    def model_post_init(self, __context) -> None:
        if self.verification_method == "business_license":
            missing = [
                label
                for label, value in [
                    ("统一社会信用代码", self.unified_social_credit_code),
                    ("法定代表人", self.legal_representative),
                    ("注册地址", self.registered_address),
                ]
                if not value
            ]
            if missing:
                raise ValueError(f"营业执照认证需填写：{'、'.join(missing)}")
        elif self.verification_method == "enterprise_email" and not self.work_email:
            raise ValueError("企业邮箱认证需填写企业邮箱")
        elif self.verification_method == "hr_authorization" and not self.proof_file_url:
            raise ValueError("HR授权认证需上传授权书、工牌或企业通讯工具截图等证明材料")


class CompanyCertificationReview(BaseModel):
    """Admin certification review request."""

    action: ReviewAction = Field(..., description="审核动作：approve/reject")
    reject_reason: Optional[str] = Field(None, max_length=500, description="驳回原因")

    @field_validator("reject_reason")
    @classmethod
    def strip_reason(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v


class CompanyCertificationResponse(BaseModel):
    """Enterprise certification response."""

    id: Optional[int] = None
    recruiter_id: int
    recruiter_display_name: Optional[str] = None
    verification_method: VerificationMethod = "business_license"
    company_name: Optional[str] = None
    unified_social_credit_code: Optional[str] = None
    legal_representative: Optional[str] = None
    registered_address: Optional[str] = None
    license_file_url: Optional[str] = None
    license_file_name: Optional[str] = None
    proof_file_url: Optional[str] = None
    proof_file_name: Optional[str] = None
    work_email: Optional[str] = None
    applicant_name: Optional[str] = None
    applicant_title: Optional[str] = None
    applicant_phone: Optional[str] = None
    applicant_wechat: Optional[str] = None
    verification_note: Optional[str] = None
    status: CertificationStatus
    reject_reason: Optional[str] = None
    reviewer_id: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CompanyCertificationListResponse(BaseModel):
    """Paginated certification list."""

    items: list[CompanyCertificationResponse]
    total: int
    skip: int
    limit: int


class BusinessLicenseOcrResponse(BaseModel):
    """Business license upload and OCR response."""

    license_file_url: str
    license_file_name: str
    company_name: Optional[str] = None
    unified_social_credit_code: Optional[str] = None
    legal_representative: Optional[str] = None
    registered_address: Optional[str] = None
    confidence: float = Field(..., ge=0, le=1)
    source: str = "dev_mock"
    raw_text: Optional[str] = None


class CertificationProofFileResponse(BaseModel):
    """Uploaded certification proof file."""

    proof_file_url: str
    proof_file_name: str
