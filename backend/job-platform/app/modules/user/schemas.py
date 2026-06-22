"""
User模块的Pydantic Schema
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator
import re


class UserRegister(BaseModel):
    """用户注册请求"""

    phone: str = Field(..., min_length=11, max_length=11, description="手机号")
    password: str = Field(..., min_length=8, max_length=20, description="密码")
    display_name: str = Field(..., min_length=2, max_length=20, description="显示名称")
    role: Literal["seeker", "recruiter"] = Field(..., description="角色")
    verification_code: str = Field(..., min_length=6, max_length=6, description="验证码")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """验证手机号格式"""
        if not re.match(r"^1[3-9]\d{9}$", v):
            raise ValueError("手机号格式不正确")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码强度"""
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("密码必须包含字母")
        if not re.search(r"\d", v):
            raise ValueError("密码必须包含数字")
        return v

    @field_validator("verification_code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """验证验证码格式"""
        if not v.isdigit():
            raise ValueError("验证码必须是6位数字")
        return v


class UserLogin(BaseModel):
    """用户登录请求"""

    phone: str = Field(..., min_length=11, max_length=11, description="手机号")
    password: str = Field(..., min_length=8, max_length=20, description="密码")


class UserUpdate(BaseModel):
    """用户更新请求"""

    display_name: Optional[str] = Field(None, min_length=2, max_length=20, description="显示名称")
    avatar_url: Optional[str] = Field(None, max_length=500, description="头像URL")
    real_name: Optional[str] = Field(None, min_length=2, max_length=20, description="真实姓名")


class UserResponse(BaseModel):
    """用户响应"""

    id: int
    phone: str
    display_name: str
    role: str
    avatar_url: Optional[str] = None
    wechat_bound: bool = False
    status: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class UserListResponse(BaseModel):
    """Paginated user list response."""

    items: list[UserResponse]
    total: int
    skip: int
    limit: int


class TokenResponse(BaseModel):
    """登录Token响应"""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
