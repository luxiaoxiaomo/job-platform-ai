"""
User数据模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Index
from sqlalchemy.sql import func

from app.db.base import Base


class User(Base):
    """用户模型"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, comment="用户ID")
    phone_hash = Column(String(64), unique=True, nullable=False, comment="手机号哈希（HMAC-SHA256，用于查询）")
    phone_encrypted = Column(String(200), nullable=False, comment="加密的手机号（Fernet，用于展示）")
    password_hash = Column(String(200), nullable=False, comment="密码哈希")
    display_name = Column(String(50), nullable=False, comment="显示名称")
    real_name_encrypted = Column(String(200), nullable=True, comment="加密的真实姓名")
    role = Column(
        SQLEnum("seeker", "recruiter", "admin", name="user_role"),
        nullable=False,
        comment="角色：seeker应聘者/recruiter招聘者/admin管理员"
    )
    avatar_url = Column(String(500), nullable=True, comment="头像URL")
    status = Column(
        SQLEnum("active", "inactive", "banned", name="user_status"),
        default="active",
        nullable=False,
        comment="状态：active活跃/inactive未激活/banned封禁"
    )
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间"
    )

    # 索引
    __table_args__ = (
        Index("idx_user_phone_hash", "phone_hash"),
        Index("idx_user_status", "status"),
        Index("idx_user_role", "role"),
    )

    def __repr__(self):
        return f"<User(id={self.id}, display_name={self.display_name}, role={self.role})>"
