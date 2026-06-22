"""
Enterprise certification data model.
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class CompanyCertification(Base):
    """Recruiter enterprise certification application."""

    __tablename__ = "company_certifications"

    id = Column(Integer, primary_key=True, index=True, comment="认证ID")
    recruiter_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="招聘者用户ID",
    )
    verification_method = Column(
        String(30),
        nullable=False,
        default="business_license",
        comment="认证方式：business_license/enterprise_email/hr_authorization",
    )
    company_name = Column(String(100), nullable=False, comment="企业名称")
    unified_social_credit_code = Column(String(18), nullable=True, comment="统一社会信用代码")
    legal_representative = Column(String(50), nullable=True, comment="法定代表人")
    registered_address = Column(String(300), nullable=True, comment="注册地址")
    license_file_url = Column(String(500), nullable=True, comment="营业执照文件URL")
    license_file_name = Column(String(200), nullable=True, comment="营业执照文件名")
    proof_file_url = Column(String(500), nullable=True, comment="辅助证明材料URL")
    proof_file_name = Column(String(200), nullable=True, comment="辅助证明材料文件名")
    work_email = Column(String(120), nullable=True, comment="企业邮箱")
    applicant_name = Column(String(50), nullable=True, comment="申请人姓名")
    applicant_title = Column(String(80), nullable=True, comment="申请人职位")
    applicant_phone = Column(String(30), nullable=True, comment="申请人联系电话")
    applicant_wechat = Column(String(80), nullable=True, comment="申请人微信")
    verification_note = Column(Text, nullable=True, comment="认证补充说明")
    status = Column(String(20), nullable=False, default="pending", comment="状态：pending/approved/rejected")
    reject_reason = Column(Text, nullable=True, comment="驳回原因")
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="审核人ID")
    reviewed_at = Column(DateTime, nullable=True, comment="审核时间")
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")

    recruiter = relationship("User", foreign_keys=[recruiter_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])

    __table_args__ = (
        Index("idx_company_certifications_recruiter_id", "recruiter_id"),
        Index("idx_company_certifications_status", "status"),
        Index("idx_company_certifications_credit_code", "unified_social_credit_code"),
    )

    def __repr__(self) -> str:
        return (
            f"<CompanyCertification(id={self.id}, recruiter_id={self.recruiter_id}, "
            f"company_name={self.company_name}, status={self.status})>"
        )
